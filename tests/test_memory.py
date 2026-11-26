import json
from collections import deque

from fastapi.testclient import TestClient
from test_documents import POSTMORTEM

from rca_investigator.chat import Conversation, Session
from rca_investigator.memory import CaseNotes
from rca_investigator.smalltalk import load_intents, match_intent, pick_reply
from rca_investigator.web import create_app


def test_replies_file_is_rich():
    intents = load_intents()
    assert len(intents) >= 12
    assert sum(len(i.replies) for i in intents) >= 150


def test_small_talk_matches_the_situation():
    assert match_intent("Hi cute bot, I've got issues with a document. I'll share it in a "
                        "while, give me a second").name == "later"
    assert match_intent("Hi, I've got few docs, can I share it?").name == "can_share"
    assert match_intent("I forgot, I'm so sorry").name == "forgot"
    assert match_intent("can you review some documents for me").name == "review"
    assert match_intent("hello!").name == "greeting"
    assert match_intent("is my data safe?").name == "privacy"
    assert match_intent("Why did checkout errors jump at 14:00 after the deploy?") is None


def test_replies_do_not_repeat():
    intent = match_intent("hello")
    recent = deque(maxlen=30)
    picked = [pick_reply(intent, recent) for _ in range(len(intent.replies))]
    assert len(set(picked)) == len(intent.replies)


def test_chat_small_talk_and_investigation_still_work():
    session, events = Session(), []
    convo = Conversation(lambda llm: None)
    say = lambda k, d: events.append((k, d))
    convo.respond(session, "Hi! I've got few docs, can I share it?", False, say)
    assert [k for k, _ in events if k != "style"] == ["say"]
    convo.respond(session, POSTMORTEM + "\nWhat went wrong?", False, say)
    assert any(k == "report" for k, _ in events)
    events.clear()
    convo.respond(session, "thanks!", False, say)
    assert [k for k, _ in events if k != "style"] == ["say"]


def test_case_notes_recall_and_corrections(tmp_path):
    notes = CaseNotes(tmp_path)
    convo = Conversation(lambda llm: None, memory=notes)
    say = []
    first = Session()
    convo.respond(first, POSTMORTEM + "\nWhat went wrong?", False,
                  lambda k, d: say.append((k, d)), remember=True)
    assert len(notes.cases()) == 1 and first.case_path.exists()
    convo.respond(first, "No, it was actually the payment provider", False,
                  lambda k, d: say.append((k, d)), remember=True)
    assert "case notes" in say[-1][1]["text"]
    assert notes.cases()[0]["corrections"] == ["No, it was actually the payment provider"]

    second, said = Session(), []
    convo.respond(second, POSTMORTEM.replace("forty", "fifty") + "\nWhy did payments fail?",
                  False, lambda k, d: said.append((k, d)), remember=True)
    recall = [d["text"] for k, d in said if k == "say" and "past case" in d["text"]]
    assert recall and "payment provider" in recall[0]
    assert len(notes.cases()) == 2


def test_memory_off_keeps_nothing(tmp_path):
    notes = CaseNotes(tmp_path)
    session, said = Session(), []
    Conversation(lambda llm: None, memory=notes).respond(
        session, POSTMORTEM + "\nWhat went wrong?", False, lambda k, d: said.append((k, d)))
    assert notes.cases() == []


def test_memory_endpoints(tmp_path):
    client = TestClient(create_app(client_factory=lambda llm: None, memory_dir=tmp_path))
    text = client.post("/api/chat", json={"session": "mem-session-1", "remember": True,
                                          "message": POSTMORTEM + "\nWhat went wrong?",
                                          "llm": False}).text
    assert "event: report" in text
    assert client.get("/api/memory").json()["cases"] == 1
    assert client.delete("/api/memory").json() == {"forgotten": 1}
    assert json.loads(client.get("/api/memory").text)["cases"] == 0


def test_announcing_a_file_is_not_an_investigation(tmp_path):
    from rca_investigator.demo import write_demo_db

    db = tmp_path / "shop.db"
    write_demo_db(db)
    client = TestClient(create_app(client_factory=lambda llm: None, sources=[str(db)],
                                   memory_dir=None))
    text = client.post("/api/chat", json={"session": "chat-session-9", "llm": False, "message":
        "Hi cute bot, I've got some issues with one of the documents in understanding what "
        "went wrong, and I need your help. I'll share the file in a while."}).text
    assert "event: report" not in text and "event: say" in text
