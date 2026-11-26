import pytest
from fastapi.testclient import TestClient
from test_documents import POSTMORTEM, FactReader

from rca_investigator import sufficiency
from rca_investigator.settings import Settings
from rca_investigator.smalltalk import read_sections, write_sections
from rca_investigator.trace import TRACES
from rca_investigator.web import create_app


def app(factory=lambda llm: None):
    return TestClient(create_app(client_factory=factory, memory_dir=None, vision={}))


def chat(client, message, sid="admin-session-1", llm=False):
    return client.post("/api/chat", json={"session": sid, "message": message, "llm": llm}).text


def test_traces_say_what_was_decided_and_where():
    client = app()
    chat(client, "sorry, I forgot to attach it")
    trace = client.get("/api/admin/traces").json()[0]
    assert trace["route"] == "small talk: forgot"
    decision = trace["decisions"][-1]
    assert decision["file"].endswith("chat.py") and decision["line"] > 1
    assert "forgot" in decision["reason"] and trace["events"][-1]["kind"] == "say"


def test_traces_record_ai_calls():
    client = app(lambda llm: FactReader() if llm else None)
    chat(client, POSTMORTEM + "\nWhat caused the outage?", llm=True)
    trace = client.get("/api/admin/traces").json()[0]
    assert trace["route"] == "investigate document"
    calls = trace["llm_calls"]
    assert calls and calls[0]["kind"] == "chat_json" and calls[0]["prompt"]
    assert calls[0]["called_from"]["function"] in {"model_facts", "investigate_documents"}


def test_replies_round_trip(tmp_path):
    path = tmp_path / "replies.md"
    path.write_text("# Replies\n\nIntro.\n\n## hello\nmatch: hi, hey\n- Hi!\n- Hey!\n")
    head, sections = read_sections(path)
    assert sections == [{"name": "hello", "match": "hi, hey", "replies": ["Hi!", "Hey!"]}]
    sections[0]["replies"].append("Hello there!")
    write_sections(head, sections, path)
    assert read_sections(path)[1][0]["replies"][-1] == "Hello there!"
    with pytest.raises(ValueError):
        write_sections(head, [{"name": "empty", "match": "", "replies": [" "]}], path)


def test_replies_api_and_tester():
    client = app()
    assert len(client.get("/api/admin/replies").json()["sections"]) >= 15
    hit = client.post("/api/admin/try", json={"message": "can I upload a pdf?"}).json()
    assert hit["intent"] and hit["phrase"]
    miss = client.post("/api/admin/try", json={"message": "why did errors jump at 3pm?"}).json()
    assert miss["intent"] is None


def test_settings_validate_apply_and_style(tmp_path):
    settings = Settings(tmp_path / "settings.json")
    try:
        settings.update({"sufficient_at": 0.8, "accent": "#ff6699", "font_size": 18})
        assert sufficiency.SUFFICIENT_AT == 0.8
        assert "--accent:#ff6699" in settings.css() and "--font-size:18px" in settings.css()
        assert Settings(tmp_path / "settings.json").values["font_size"] == 18
        for bad in ({"font_size": 99}, {"accent": "red"}, {"partial_at": 0.85},
                    {"nope": 1}):
            with pytest.raises(ValueError):
                settings.update(bad)
    finally:
        settings.reset()
    assert sufficiency.SUFFICIENT_AT == 0.7


def test_settings_api_and_appearance_css(tmp_path):
    client = TestClient(create_app(client_factory=lambda llm: None, memory_dir=None, vision={},
                                   settings_path=tmp_path / "s.json"))
    try:
        assert client.put("/api/admin/settings", json={"radius": 24}).status_code == 200
        assert "--radius:24px" in client.get("/api/appearance.css").text
        assert client.put("/api/admin/settings", json={"radius": 99}).status_code == 400
    finally:
        client.post("/api/admin/settings/reset")


def test_health_accuracy_and_map():
    client = app()
    result = client.post("/api/admin/health/accuracy").json()["result"]
    assert all(v["verdict correct"] >= 90 for v in result.values())
    assert client.post("/api/admin/health/unknown").status_code == 404
    rows = client.get("/api/admin/map").json()
    assert len(rows) >= 15 and all(r["line"] >= 1 for r in rows)
    assert any(r["file"].endswith("replies.md") and r["line"] > 1 for r in rows)


def test_control_centre_is_local_only():
    remote = TestClient(create_app(client_factory=lambda llm: None, memory_dir=None, vision={}),
                        client=("203.0.113.9", 5000))
    assert remote.get("/api/admin/traces").status_code == 403
    assert remote.get("/admin").status_code == 403
    assert remote.get("/").status_code == 200
    off = TestClient(create_app(client_factory=lambda llm: None, memory_dir=None, vision={},
                                admin=False))
    assert off.get("/admin").status_code == 404


def test_traces_are_capped():
    assert TRACES.maxlen == 100
