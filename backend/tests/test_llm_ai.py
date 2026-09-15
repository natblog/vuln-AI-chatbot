import os
os.environ.setdefault("SMTP_HOST", "127.0.0.1")

import httpx
from fastapi.testclient import TestClient
from fakes import native_call, ollama_message, ollama_text, scripted_ollama
from app.main import app
from app.seed import seed

seed(force=True)
client = TestClient(app, raise_server_exceptions=False)


def test_ai_drives_tool_calls(monkeypatch):
    scripted_ollama(monkeypatch,
                    ollama_message(content='```json\n[{"name": "list_products", "args": {}}]\n```'),
                    ollama_text("Here are the shop products (see tool results)."))
    r = client.post("/api/chat", json={"message": "List GPUs"}).json()
    assert r["planner"] == "ai"
    assert any(t["name"] == "list_products" for t in r["tool_calls"])
    assert "shop products" in r["reply_markdown"]


def test_ai_native_tool_calls(monkeypatch):
    _, seen = scripted_ollama(monkeypatch,
                              ollama_message(content="", tool_calls=[
                                  native_call("list_products")]),
                              ollama_text("Listed the shop products for you."))
    r = client.post("/api/chat", json={"message": "List GPUs"}).json()
    assert seen[0][1]["json"].get("tools"), "native tools schema must be sent to Ollama"
    assert r["planner"] == "ai"
    assert any(t["name"] == "list_products" for t in r["tool_calls"])
    assert "shop products" in r["reply_markdown"]


def test_unreachable_primary_falls_back_to_docker_internal(monkeypatch):
    import app.ollama
    monkeypatch.setattr(app.ollama, "OLLAMA_HOST", "http://127.0.0.1:11434")
    seen = []

    def fake_post(url, **k):
        seen.append(url)
        if "127.0.0.1" in url:
            raise httpx.ConnectError("refused")
        return ollama_text("Hi, I can help with products and orders.")

    monkeypatch.setattr(app.ollama.httpx, "post", fake_post)
    r = client.post("/api/chat", json={"message": "hello"}).json()
    assert any("host.docker.internal" in u for u in seen)
    assert "Hi, I can help" in r["reply_markdown"]


def test_offline_runs_no_tools(monkeypatch):
    from fakes import dead_ollama
    dead_ollama(monkeypatch)
    r = client.post("/api/chat", json={"message": "Show my purchase history"}).json()
    assert r["tool_calls"] == []
    assert r["planner"] == "none"
    assert "offline" in r["reply_markdown"].lower()
