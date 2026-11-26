import base64
import json

from fastapi.testclient import TestClient
from test_ingest import own_format_table
from test_investigate import GOOD_REPLY, FakeClient

from rca_investigator.chat import Conversation, Session, choose_metric
from rca_investigator.investigate import investigate
from rca_investigator.llm import LLMError
from rca_investigator.simulate import generate_incident
from rca_investigator.web import create_app

SID = "test-session-1"


class Talker(FakeClient):
    def chat(self, prompt, system=None, json_schema=None, temperature=0.1):
        return "Because of the deploy [E5]."


def events(text):
    out = []
    for block in text.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines())
        out.append((lines["event"], json.loads(lines["data"])))
    return out


def app(factory=lambda llm: None):
    return TestClient(create_app(client_factory=factory))


def chat(client, message, llm=True):
    return events(client.post("/api/chat", json={"session": SID, "message": message,
                                                  "llm": llm}).text)


def test_page_and_info():
    client = app()
    assert "CuteBot" in client.get("/").text
    assert client.get("/api/info").json()["bot_name"] == "CuteBot"


def test_without_data_cutebot_explains_what_to_share():
    got = chat(app(), "hello")
    assert got[0][0] == "say" and "upload" in got[0][1]["text"].lower()


def test_upload_then_ask_streams_stages_and_report():
    client = app()
    data = base64.b64encode(own_format_table().to_csv(index=False).encode()).decode()
    r = client.post("/api/upload", json={"session": SID, "name": "export.csv",
                                         "data_base64": data})
    assert r.status_code == 200 and r.json()["has_numbers"]
    got = chat(client, "Why did errors go up?", llm=False)
    stages = [d["stage"] for k, d in got if k == "stage"]
    assert stages[0] == "collect" and "weigh" in stages and stages[-1] == "back"
    report = next(d for k, d in got if k == "report")
    assert report["what_changed"]["metric"] == "errors"
    assert got[-1][0] == "done"


def test_bad_upload_gives_a_friendly_error():
    r = app().post("/api/upload", json={"session": SID, "name": "chart.png",
                                        "data_base64": base64.b64encode(b"x").decode()})
    assert r.status_code == 400 and "pictures" in r.json()["detail"]


def test_sample_then_follow_up_question():
    client = app(lambda llm: Talker(GOOD_REPLY) if llm else None)
    q = client.post("/api/sample", json={"session": SID}).json()["question"]
    assert any(k == "report" for k, _ in chat(client, q))
    follow = chat(client, "Could it be traffic instead?")
    assert not any(k == "report" for k, _ in follow)
    assert any(k == "say" and "[E5]" in d["text"] for k, d in follow)


def test_unreachable_model_falls_back_to_engines():
    class Down:
        def chat_json(self, *a, **k):
            raise LLMError("cannot reach Ollama")

    client = app(lambda llm: Down())
    q = client.post("/api/sample", json={"session": SID}).json()["question"]
    got = chat(client, q)
    assert any("isn't available" in d.get("text", "") for k, d in got if k == "stage")
    assert any(k == "report" for k, _ in got)


def test_pasted_records_are_added_but_a_dated_question_is_not():
    session, said = Session(), []
    convo = Conversation(lambda llm: None)
    convo.respond(session, "2026-05-01 14:50 Deployed api v2.4\n2026-05-01 15:00 alert fired",
                  False, lambda k, d: said.append((k, d)))
    assert len(session.records) == 2 and "numbers" in said[-1][1]["text"]
    convo.respond(session, "Why did errors jump at 2026-05-01 15:00?", False, lambda k, d: None)
    assert len(session.records) == 2


def test_choose_metric_from_words_or_biggest_change():
    inc = generate_incident("X", "bad_deploy", seed=12)
    assert choose_metric(inc.metrics, "why is it so slow?") == "latency_p95_ms"
    assert choose_metric(inc.metrics, "what happened?") == inc.metric


def test_bad_session_id_rejected_and_sample_files():
    client = app()
    assert client.post("/api/chat", json={"session": "../x", "message": "hi"}).status_code == 422
    assert client.get("/api/sample-file/metrics.csv").text.startswith("timestamp,")
    assert client.get("/api/sample-file/records.csv").text.startswith("timestamp,source")
    assert client.get("/api/sample-file/nope").status_code == 404


def test_on_step_reports_each_stage():
    inc = generate_incident("INC-T", "bad_deploy", seed=12)
    seen = []
    investigate("INC-T", inc.question, inc.metric, inc.metrics, inc.records, None,
                on_step=lambda step, msg: seen.append(step))
    assert seen[0] == "numbers" and seen[-1] == "judge_done"
