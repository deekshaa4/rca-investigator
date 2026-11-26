import json

from fastapi.testclient import TestClient
from test_investigate import GOOD_REPLY, FakeClient

from rca_investigator.investigate import investigate
from rca_investigator.llm import LLMError
from rca_investigator.simulate import generate_dataset, generate_incident, save_incident
from rca_investigator.web import create_app


def events(text):
    out = []
    for block in text.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines())
        out.append((lines["event"], json.loads(lines["data"])))
    return out


def make_client(tmp_path, factory=lambda llm: None):
    for inc in generate_dataset(5, seed=3):
        save_incident(inc, tmp_path)
    return TestClient(create_app(tmp_path, client_factory=factory))


def test_page_and_incident_list(tmp_path):
    client = make_client(tmp_path)
    assert "RCA Investigator" in client.get("/").text
    assert client.get("/api/info").json()["bot_name"] == "CuteBot"
    incidents = client.get("/api/incidents").json()
    assert len(incidents) == 5 and incidents[0]["question"]


def test_investigation_streams_steps_then_report(tmp_path):
    client = make_client(tmp_path)
    first = client.get("/api/incidents").json()[0]["id"]
    got = events(client.get(f"/api/investigate/{first}?llm=false").text)
    kinds = [k for k, _ in got]
    steps = [d["step"] for k, d in got if k == "step"]
    assert steps[:2] == ["numbers", "numbers_done"] and "judge_done" in steps
    assert kinds[-2:] == ["report", "done"]
    assert got[-2][1]["sufficiency"]["verdict"] in {"sufficient", "partial", "insufficient"}


def test_model_steps_are_streamed(tmp_path):
    client = make_client(tmp_path, lambda llm: FakeClient(GOOD_REPLY))
    first = client.get("/api/incidents").json()[0]["id"]
    steps = [d["step"] for k, d in events(client.get(f"/api/investigate/{first}").text)
             if k == "step"]
    assert "model" in steps and "fact_check" in steps


def test_unreachable_model_falls_back_to_engines(tmp_path):
    class Down:
        def chat_json(self, *a, **k):
            raise LLMError("cannot reach Ollama")

    client = make_client(tmp_path, lambda llm: Down())
    first = client.get("/api/incidents").json()[0]["id"]
    got = events(client.get(f"/api/investigate/{first}").text)
    assert any("not available" in d.get("message", "") for k, d in got if k == "step")
    assert [k for k, _ in got][-2:] == ["report", "done"]


def test_unknown_incident_is_404(tmp_path):
    client = make_client(tmp_path)
    assert client.get("/api/investigate/..%2F..%2Fetc").status_code == 404
    assert client.get("/api/investigate/NOPE").status_code == 404


def test_on_step_reports_each_stage():
    inc = generate_incident("INC-T", "bad_deploy", seed=12)
    seen = []
    investigate("INC-T", inc.question, inc.metric, inc.metrics, inc.records, None,
                on_step=lambda step, msg: seen.append(step))
    assert seen[0] == "numbers" and seen[-1] == "judge_done"
