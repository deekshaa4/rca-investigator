import base64
import json

from fastapi.testclient import TestClient
from test_ingest import tiny_pdf

from rca_investigator.chat import Conversation, Session
from rca_investigator.documents import (
    answer_from_documents,
    document_from_text,
    investigate_documents,
    verify_quote,
)
from rca_investigator.web import create_app

POSTMORTEM = """Checkout outage review

On the morning of the sale, customers could not complete payments and many complained on
social media. The checkout page showed errors for about forty minutes.

The night before, the payments team changed the database connection limit from 200 to 20
while tidying up the configuration. The outage was caused by this lower connection limit:
when sale traffic arrived, requests waited for a free connection and timed out.

The on-call engineer restored the old limit and payments recovered. We will add a review
step for configuration changes and alert when the connection pool is nearly full."""


class FactReader:
    """A fake model: reads facts (one with an invented quote) and tells the story."""

    def chat_json(self, prompt, json_schema, system=None):
        if "facts" in json_schema["properties"]:
            return {"facts": [
                {"type": "cause", "statement": "Lower connection limit",
                 "quote": "The outage was caused by this lower connection limit"},
                {"type": "cause", "statement": "made up", "quote": "A cosmic ray flipped a bit"},
            ]}
        eid = next(line.split()[0] for line in prompt.splitlines()
                   if "caused by this lower connection limit" in line)
        return {"what_happened": "Payments failed during the sale.",
                "contributing_factors": [{"description": "Connection limit cut to 20",
                                          "category": "config_change", "confidence": 0.9,
                                          "why_chain": ["Too few connections"],
                                          "evidence_ids": [eid]}],
                "ruled_out": [], "actions": []}

    def chat(self, prompt, system=None, json_schema=None, temperature=0.1):
        return "The limit was restored by the on-call engineer [p.1]."


def test_quote_check():
    text = "The outage was caused by this lower  connection limit: when traffic arrived"
    assert verify_quote("the outage was caused by this lower connection limit", text)
    assert not verify_quote("The outage was caused by a fire in the data centre", text)


def test_document_without_dates_is_investigated_by_rules():
    doc = document_from_text("review.txt", POSTMORTEM)
    report = investigate_documents("What caused the outage?", [doc], None)
    top = report.contributing_factors[0]
    assert "lower connection limit" in top.description
    assert top.category.value in {"config_change", "infrastructure"}
    assert report.summary and report.sufficiency.verdict.value in {"sufficient", "partial"}
    assert report.actions
    assert all(e.kind.value == "document" for e in report.evidence)


def test_model_facts_keep_only_real_quotes():
    doc = document_from_text("review.txt", POSTMORTEM)
    report = investigate_documents("What caused the outage?", [doc], FactReader())
    g = report.guardrails
    assert g.quotes_checked == 2 and g.quotes_rejected == 1
    assert not any("cosmic" in e.summary for e in report.evidence)
    assert report.summary == "Payments failed during the sale."
    assert report.contributing_factors[0].category.value == "config_change"


def test_no_cause_in_document_is_insufficient():
    doc = document_from_text("note.txt", "Customers could not log in this morning and "
                                         "complained a lot. Support answered many emails.")
    report = investigate_documents("Why?", [doc], None)
    assert report.sufficiency.verdict.value == "insufficient"
    assert report.sufficiency.missing_data


def test_questions_about_the_document():
    doc = document_from_text("review.txt", POSTMORTEM)
    assert "[p.1]" in answer_from_documents("Who fixed it?", [doc], FactReader())
    plain = answer_from_documents("who restored the limit?", [doc], None)
    assert "restored the old limit" in plain


def test_pasted_story_gets_investigated():
    session, events = Session(), []
    Conversation(lambda llm: None).respond(session, POSTMORTEM + "\nWhat went wrong?", False,
                                           lambda k, d: events.append((k, d)))
    report = next(d["report"] for k, d in events if k == "report")
    assert report["summary"] and report["contributing_factors"]
    assert session.mode == "documents"


def test_general_question_without_data_is_labelled():
    session, events = Session(), []
    Conversation(lambda llm: FactReader()).respond(
        session, "What is a root cause analysis?", True, lambda k, d: events.append((k, d)))
    assert any("not from your data" in d.get("text", "") for k, d in events if k == "say")


def test_upload_pdf_without_dates_then_ask():
    client = TestClient(create_app(client_factory=lambda llm: None))
    pdf = tiny_pdf([line for line in POSTMORTEM.splitlines() if line.strip()])
    r = client.post("/api/upload", json={"session": "doc-session-1", "name": "review.pdf",
                                         "data_base64": base64.b64encode(pdf).decode()})
    assert r.status_code == 200 and "read all of it" in r.json()["message"]
    text = client.post("/api/chat", json={"session": "doc-session-1",
                                          "message": "What caused the outage?",
                                          "llm": False}).text
    events = [(b.split("\n")[0][7:], json.loads(b.split("\n")[1][6:]))
              for b in text.strip().split("\n\n")]
    report = next(d["report"] for k, d in events if k == "report")
    assert "connection limit" in report["contributing_factors"][0]["description"]
    follow = client.post("/api/chat", json={"session": "doc-session-1",
                                            "message": "Who restored the limit?",
                                            "llm": False}).text
    assert "restored" in follow and "event: report" not in follow


def test_pasted_document_wins_over_connected_database(tmp_path):
    from rca_investigator.demo import write_demo_db

    db = tmp_path / "shop.db"
    write_demo_db(db)
    client = TestClient(create_app(client_factory=lambda llm: None, sources=[str(db)]))
    text = client.post("/api/chat", json={"session": "doc-session-2",
                                          "message": POSTMORTEM + "\nWhat went wrong?",
                                          "llm": False}).text
    assert "connection limit" in text and "service_metrics_5min" not in text
