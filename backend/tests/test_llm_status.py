import os
os.environ.setdefault("SMTP_HOST", "127.0.0.1")

from fastapi.testclient import TestClient
from fakes import dead_transport, missing_model_response
from app.main import app
from app.seed import seed

seed(force=True)
client = TestClient(app, raise_server_exceptions=False)


def test_chat_surfaces_pull_hint_when_model_missing(monkeypatch):
    import app.ollama
    monkeypatch.setattr(app.ollama.httpx, "post", missing_model_response)
    monkeypatch.setattr(app.ollama.httpx, "get", dead_transport)
    r = client.post("/api/chat", json={"message": "List GPUs"}).json()
    assert r.get("llm_warning") and "ollama pull" in r["llm_warning"].lower()
    assert "qwen3" in r["llm_warning"]
    assert r["tool_calls"] == []
    assert "offline" in r["reply_markdown"].lower()


def test_llm_status_endpoint_reports_pull_hint(monkeypatch):
    import app.ollama
    monkeypatch.setattr(app.ollama.httpx, "post", missing_model_response)
    monkeypatch.setattr(app.ollama.httpx, "get", dead_transport)
    r = client.get("/api/llm-status").json()
    assert r["available"] is False
    assert "ollama pull" in r["hint"].lower()


def test_chat_never_500s_on_tool_failure(monkeypatch):
    def broken_tool(*a, **k):
        raise RuntimeError("db exploded")
    monkeypatch.setattr("app.llm._run_tool", broken_tool)
    resp = client.post("/api/chat", json={"message": "Show my purchase history"})
    assert resp.status_code == 200
    assert "error" in resp.json()["reply_markdown"].lower()
