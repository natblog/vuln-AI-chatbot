import httpx

import app.llm
import app.ollama


def ollama_message(role="assistant", content="", tool_calls=None):
    msg = {"role": role, "content": content}
    if tool_calls is not None:
        msg["tool_calls"] = tool_calls
    req = httpx.Request("POST", "http://x/api/chat")
    return httpx.Response(200, request=req, json={"message": msg})


def ollama_text(content):
    return ollama_message(content=content)


def native_call(name, args=None):
    return {"function": {"name": name, "arguments": args or {}}}


def openai_message(content="", tool_calls=None):
    msg = {"role": "assistant", "content": content}
    if tool_calls is not None:
        msg["tool_calls"] = tool_calls
    req = httpx.Request("POST", "http://x/v1/chat/completions")
    return httpx.Response(200, request=req, json={"choices": [{"message": msg}]})


def missing_model_response(*a, **k):
    req = httpx.Request("POST", "http://ollama/api/chat")
    resp = httpx.Response(404, request=req, text="model 'qwen3.5:4b' not found, try pulling it first")
    raise httpx.HTTPStatusError("not found", request=req, response=resp)


def dead_transport(*a, **k):
    raise httpx.ConnectError("down")


def scripted_ollama(monkeypatch, *responses):
    calls = {"n": 0}
    seen = []

    def fake_post(url, **k):
        calls["n"] += 1
        seen.append((url, k))
        resp = responses[min(calls["n"], len(responses)) - 1]
        return resp() if callable(resp) else resp

    monkeypatch.setattr(app.ollama.httpx, "post", fake_post)
    return calls, seen


def dead_ollama(monkeypatch):
    monkeypatch.setattr(app.ollama.httpx, "post", dead_transport)
    monkeypatch.setattr(app.ollama.httpx, "get", dead_transport)


def patch_config(monkeypatch, **overrides):
    for key, value in overrides.items():
        monkeypatch.setattr(app.ollama, key, value)
        if hasattr(app.llm, key):
            monkeypatch.setattr(app.llm, key, value)
