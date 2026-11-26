"""Everyday conversations that must go the right way (from real testing)."""

from fastapi.testclient import TestClient
from test_documents import POSTMORTEM

from rca_investigator.chat import Conversation, Session
from rca_investigator.documents import document_from_text
from rca_investigator.web import create_app

STATEMENT = """Account summary and transactions
Account number 12345678   Sort code 12-34-56   Statement date 25/09/2023
Opening balance  £1,250.00     Closing balance  £1,104.50
Date         Description                 Debit      Credit    Balance
01/09/2023   Salary                                  £2,000.00
03/09/2023   Rent                        £1,200.00
10/09/2023   Grocery store               £85.50
18/09/2023   Phone bill                  £40.00
22/09/2023   Transfer to savings         £820.00"""

STATEMENT_WITH_PROBLEM = STATEMENT + """
24/09/2023   Direct debit returned: insufficient funds   £25.00 fee
24/09/2023   Gym membership payment declined"""

MEETING = """Weekly team meeting minutes
Attendees: Priya, Sam, Alex
Agenda: launch plan, budget
Alex will send the budget draft by Friday. Sam is preparing the launch checklist."""


def run(session, message, convo=None, llm=None):
    events = []
    (convo or Conversation(lambda use: llm)).respond(session, message, llm is not None,
                                                     lambda k, d: events.append((k, d)))
    return events


def said(events):
    return " ".join(d["text"] for k, d in events if k == "say")


def kinds(events):
    return [k for k, _ in events]


def with_doc(text, name="file.pdf"):
    s = Session()
    s.add_document(document_from_text(name, text))
    return s


def test_mentioning_an_unshared_file_asks_for_it():
    events = run(Session(), "i was thinking you could investigate my account statement and give "
                            "me a summary?")
    assert "report" not in kinds(events)
    assert "account statement" in said(events)


def test_connected_database_not_used_for_unshared_file(tmp_path):
    from rca_investigator.demo import write_demo_db

    db = tmp_path / "demo.db"
    write_demo_db(db)
    client = TestClient(create_app(client_factory=lambda llm: None, sources=[str(db)],
                                   memory_dir=None, vision={}))
    text = client.post("/api/chat", json={"session": "route-one-1", "llm": False, "message":
        "i was thinking you could investigate my account statement and give me a summary?"}).text
    assert "event: report" not in text and "service_metrics_5min" not in text
    info = client.get("/api/info").json()
    assert info["connected"]  # still known to the server, just not shown as a banner
    asked = client.post("/api/chat", json={"session": "route-two-2", "llm": False, "message":
        "Why did the error rate go up on 17 March 2026?"}).text
    assert "event: report" in asked


def test_statement_summary_is_a_summary_not_an_investigation():
    events = run(with_doc(STATEMENT), "give me a summary")
    assert "report" not in kinds(events)
    assert "statement" in said(events) and "£1,200.00" in said(events)


def test_statement_without_problems_is_not_turned_into_an_incident():
    events = run(with_doc(STATEMENT), "what went wrong?")
    assert "report" not in kinds(events)
    assert "a bank or account statement" in said(events)


def test_statement_with_a_problem_is_investigated():
    events = run(with_doc(STATEMENT_WITH_PROBLEM), "what went wrong?")
    report = next(d["report"] for k, d in events if k == "report")
    assert any("insufficient funds" in e["summary"] or "declined" in e["summary"]
               for e in report["evidence"])


def test_question_about_notes_is_answered_not_investigated():
    events = run(with_doc(MEETING, "minutes.docx"), "who is sending the budget?")
    assert "report" not in kinds(events) and "Alex" in said(events)


def test_incident_report_is_still_investigated():
    events = run(with_doc(POSTMORTEM), "what caused the outage?")
    assert "report" in kinds(events)


def test_summary_numbers_are_checked():
    class Inventor:
        def chat(self, prompt, system=None, json_schema=None, temperature=0.1):
            return "A bank statement. Rent was £1,200.00 and a bonus of £9,999 arrived."

        def chat_json(self, *a, **k):
            return {"facts": []}

    events = run(with_doc(STATEMENT), "summarise this", llm=Inventor())
    assert "£9,999" in said(events) and "aren't written in the document" in said(events)


def test_answers_stream_piece_by_piece():
    class Streamer:
        def chat(self, prompt, system=None, json_schema=None, temperature=0.1):
            return "unused"

        def chat_stream(self, prompt, system=None, temperature=0.1):
            yield from ["Root cause analysis ", "finds why ", "things went wrong."]

        def chat_json(self, *a, **k):
            return {"facts": []}

    events = run(Session(), "What is a root cause analysis exactly?", llm=Streamer())
    deltas = [d["text"] for k, d in events if k == "delta"]
    assert deltas == ["Root cause analysis ", "finds why ", "things went wrong."]
    final = [d for k, d in events if k == "say"][-1]
    assert final["final"] and "things went wrong." in final["text"]
