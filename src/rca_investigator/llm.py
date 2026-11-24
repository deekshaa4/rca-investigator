"""Client for a local language model served by Ollama (https://ollama.com).

Uses only the Python standard library, so there are no extra dependencies, and
everything runs on the local machine for free.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

DEFAULT_HOST = os.environ.get("RCA_OLLAMA_HOST", "http://localhost:11434")
DEFAULT_MODEL = os.environ.get("RCA_MODEL", "qwen2.5:3b")


class LLMError(RuntimeError):
    """Raised when the model cannot be reached or returns an unusable answer."""


class OllamaClient:
    def __init__(self, model: str = DEFAULT_MODEL, host: str = DEFAULT_HOST, timeout: float = 300):
        self.model = model
        self.host = host.rstrip("/")
        self.timeout = timeout

    def _request(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.host}{path}"
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode())
        except (urllib.error.URLError, TimeoutError) as exc:
            raise LLMError(f"cannot reach Ollama at {self.host}: {exc}") from exc

    def installed_models(self) -> list[str]:
        """Names of the models available locally."""
        return [m["name"] for m in self._request("/api/tags").get("models", [])]

    def has_model(self) -> bool:
        names = self.installed_models()
        return self.model in names or f"{self.model}:latest" in names

    def chat(
        self,
        prompt: str,
        system: str | None = None,
        json_schema: dict[str, Any] | None = None,
        temperature: float = 0.1,
    ) -> str:
        """Send one prompt and return the model's reply.

        If json_schema is given, the model is constrained to reply with JSON
        matching that schema.
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if json_schema is not None:
            payload["format"] = json_schema
        reply = self._request("/api/chat", payload)
        try:
            return reply["message"]["content"]
        except (KeyError, TypeError) as exc:
            raise LLMError(f"unexpected reply from Ollama: {reply}") from exc

    def chat_json(self, prompt: str, json_schema: dict[str, Any], system: str | None = None) -> Any:
        """Like chat(), but parses and returns the JSON reply."""
        text = self.chat(prompt, system=system, json_schema=json_schema)
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise LLMError(f"model did not return valid JSON: {text[:200]}") from exc
