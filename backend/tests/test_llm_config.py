import os
os.environ.setdefault("SMTP_HOST", "127.0.0.1")

from fastapi.testclient import TestClient
from fakes import ollama_message, patch_config, scripted_ollama
from app.main import app
from app.seed import seed

seed(force=True)
client = TestClient(app, raise_server_exceptions=False)


def test_ollama_request_uses_configured_options(monkeypatch):
    patch_config(monkeypatch, OLLAMA_MODEL="qwen3:8b", OLLAMA_TEMPERATURE=0.2,
                 OLLAMA_MAX_TOKENS=2048, OLLAMA_TIMEOUT_SECONDS=600, OLLAMA_THINK=False)
    _, seen = scripted_ollama(monkeypatch, ollama_message(content="hi"))
    r = client.post("/api/chat", json={"message": "hello"}).json()
    assert r["planner"] == "none"
    p = seen[0][1]["json"]
    assert p["model"] == "qwen3:8b"
    assert p["options"]["temperature"] == 0.2
    assert p["options"]["num_predict"] == 2048
    assert p["think"] is False
    assert seen[0][1].get("timeout") == 600


def test_openai_native_tool_calls(monkeypatch):
    from fakes import native_call, openai_message, patch_config, scripted_ollama
    patch_config(monkeypatch, LLM_PROVIDER="openai", OPENAI_API_KEY="sk-test",
                 OPENAI_BASE_URL="http://fake-provider:1234/v1", OPENAI_MODEL="qwen3.5:4b")
    calls, seen = scripted_ollama(monkeypatch,
                                  openai_message(content="", tool_calls=[
                                      native_call("list_products")]),
                                  openai_message(content="Listed products."))
    r = client.post("/api/chat", json={"message": "List GPUs"}).json()
    assert seen[0][0].startswith("http://fake-provider:1234/v1/chat/completions")
    assert seen[0][1]["json"].get("tools"), "tools schema must be sent on the openai path too"
    assert r["planner"] == "ai"
    assert any(t["name"] == "list_products" for t in r["tool_calls"])


def test_default_model_is_qwen3_5_4b(monkeypatch):
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    import importlib
    import app.config as cfg
    importlib.reload(cfg)
    try:
        assert cfg.OLLAMA_MODEL == "qwen3.5:4b"
        assert cfg.OLLAMA_TIMEOUT_SECONDS == 600
        assert cfg.OLLAMA_THINK is False
    finally:
        importlib.reload(cfg)


def test_openai_request_uses_configured_options(monkeypatch):
    import httpx
    patch_config(monkeypatch, LLM_PROVIDER="openai", OPENAI_API_KEY="sk-test",
                 OPENAI_BASE_URL="http://fake-provider:1234/v1",
                 OPENAI_MODEL="gpt-4o-mini", OPENAI_TEMPERATURE=0.2,
                 OPENAI_MAX_TOKENS=2048, OPENAI_TIMEOUT_SECONDS=600)
    seen = {}

    def fake_post(url, **k):
        seen["url"] = url
        seen["payload"] = k["json"]
        seen["timeout"] = k.get("timeout")
        req = httpx.Request("POST", url)
        return httpx.Response(200, request=req,
                              json={"choices": [{"message": {"content": "hi"}}]})

    import app.ollama
    monkeypatch.setattr(app.ollama.httpx, "post", fake_post)
    r = client.post("/api/chat", json={"message": "hello"}).json()
    assert r["planner"] == "none"
    assert seen["url"] == "http://fake-provider:1234/v1/chat/completions"
    p = seen["payload"]
    assert p["model"] == "gpt-4o-mini"
    assert p["temperature"] == 0.2
    assert p["max_tokens"] == 2048
    assert seen["timeout"] == 600
