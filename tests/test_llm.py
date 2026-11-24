import json

import pytest

from rca_investigator import llm
from rca_investigator.cli import main


class FakeResponse:
    def __init__(self, body):
        self.body = json.dumps(body).encode()

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def fake_ollama(models, reply_text):
    def urlopen(req, timeout):
        if req.full_url.endswith("/api/tags"):
            return FakeResponse({"models": [{"name": m} for m in models]})
        return FakeResponse({"message": {"role": "assistant", "content": reply_text}})

    return urlopen


def test_chat_json_parses_reply(monkeypatch):
    monkeypatch.setattr(llm.urllib.request, "urlopen", fake_ollama([], '{"status": "ready"}'))
    client = llm.OllamaClient(model="test-model")
    assert client.chat_json("hi", json_schema={"type": "object"}) == {"status": "ready"}


def test_chat_json_rejects_invalid_json(monkeypatch):
    monkeypatch.setattr(llm.urllib.request, "urlopen", fake_ollama([], "not json"))
    with pytest.raises(llm.LLMError, match="valid JSON"):
        llm.OllamaClient().chat_json("hi", json_schema={})


def test_unreachable_server_raises_llm_error(monkeypatch):
    def refuse(req, timeout):
        raise llm.urllib.error.URLError("connection refused")

    monkeypatch.setattr(llm.urllib.request, "urlopen", refuse)
    with pytest.raises(llm.LLMError, match="cannot reach"):
        llm.OllamaClient().installed_models()


def test_check_command_reports_missing_model(monkeypatch, capsys):
    monkeypatch.setattr(llm.urllib.request, "urlopen", fake_ollama(["other:1b"], "{}"))
    assert main(["check", "--model", "qwen2.5:3b"]) == 1
    assert "ollama pull qwen2.5:3b" in capsys.readouterr().out


def test_check_command_succeeds(monkeypatch, capsys):
    monkeypatch.setattr(
        llm.urllib.request, "urlopen", fake_ollama(["qwen2.5:3b"], '{"status": "ready"}')
    )
    assert main(["check", "--model", "qwen2.5:3b"]) == 0
    assert "All good" in capsys.readouterr().out
