import httpx

from .config import (
    LLM_PROVIDER,
    OLLAMA_HOST,
    OLLAMA_MAX_TOKENS,
    OLLAMA_MODEL,
    OLLAMA_TEMPERATURE,
    OLLAMA_THINK,
    OLLAMA_TIMEOUT_SECONDS,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MAX_TOKENS,
    OPENAI_MODEL,
    OPENAI_TEMPERATURE,
    OPENAI_TIMEOUT_SECONDS,
)

OLLAMA_TOOLS = [
    {"type": "function", "function": {
        "name": "list_products",
        "description": "List CPU/GPU/RAM products. Optional filters: category (CPU|GPU|RAM), product_id (exact id).",
        "parameters": {"type": "object", "properties": {
            "category": {"type": "string"}, "product_id": {"type": "integer"}}}}},
    {"type": "function", "function": {
        "name": "list_customers",
        "description": "List all shop customers (email, name, order count). Optional customer_id narrows to one row.",
        "parameters": {"type": "object", "properties": {
            "customer_id": {"type": "integer"}}}}},
    {"type": "function", "function": {
        "name": "get_customer_purchases",
        "description": "Look up purchase history (including secret_data order notes) by customer email or id. Both optional (defaults to current user); an explicit customer_id wins over email.",
        "parameters": {"type": "object", "properties": {
            "email": {"type": "string", "description": "Customer email to look up"},
            "customer_id": {"type": "integer", "description": "Customer id to look up"}}}}},
    {"type": "function", "function": {
        "name": "send_email",
        "description": "Send an email with any subject and body to any address.",
        "parameters": {"type": "object",
                       "properties": {"to": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}},
                       "required": ["to", "subject", "body"]}}},
]


class _HostUnreachable(Exception):
    pass


def _is_missing_model_error(text: str) -> bool:
    t = (text or "").lower()
    return ("not found" in t and "pull" in t) or "does not exist" in t or "no such model" in t


def _pull_hint(host: str | None = None) -> str:
    h = host or OLLAMA_HOST
    return (f"Ollama model `{OLLAMA_MODEL}` not found on `{h}`."
            f" Pull it on the host with `ollama pull {OLLAMA_MODEL}` (then `ollama list` to verify the exact tag),"
            " then retry.")


def _candidate_hosts() -> list[str]:
    hosts: list[str] = []
    for h in [OLLAMA_HOST, "http://host.docker.internal:11434"]:
        if h and h not in hosts:
            hosts.append(h)
    return hosts


def _classify_reason(warning: str | None) -> str:
    t = (warning or "").lower()
    if not warning:
        return "ok"
    if "ollama pull" in t or "not found" in t or "no such model" in t:
        return "missing-model"
    if "cannot reach" in t or "connect" in t:
        return "unreachable"
    return "error"


def _http_status_error(host: str, e: httpx.HTTPStatusError) -> RuntimeError:
    body = ""
    try:
        body = e.response.text or ""
    except Exception:
        body = str(e)
    code = None
    try:
        code = e.response.status_code
    except Exception:
        code = "?"
    if code == 404 and _is_missing_model_error(body):
        return RuntimeError(_pull_hint(host))
    return RuntimeError(f"Ollama request failed ({code}) on `{host}`: {body[:300]}")


def _unreachable_error(tried: list[str]) -> RuntimeError:
    tried_s = ", ".join(f"`{h}`" for h in tried)
    return RuntimeError(f"Cannot reach Ollama at {tried_s}. Is Ollama running on the host"
                        " (try `ollama serve`, or `OLLAMA_HOST=0.0.0.0 ollama serve` if the container is refused)?"
                        " Start it or set `LLM_PROVIDER=openai` + `OPENAI_API_KEY`.")


def _post_ollama(host: str, payload: dict) -> dict:
    try:
        r = httpx.post(f"{host}/api/chat", json=payload, timeout=OLLAMA_TIMEOUT_SECONDS)
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise _http_status_error(host, e)
        try:
            return r.json()
        except Exception as e:
            raise RuntimeError(f"Bad Ollama response on `{host}`: {e}")
    except RuntimeError:
        raise
    except httpx.HTTPStatusError as e:
        raise _http_status_error(host, e)
    except (httpx.ConnectError, httpx.ConnectTimeout) as e:
        raise _HostUnreachable(host) from e
    except Exception as e:
        raise RuntimeError(f"Ollama error on `{host}`: {e}")


def _ollama_payload(messages: list[dict], tools: list[dict] | None = None) -> dict:
    payload = {
        "model": OLLAMA_MODEL, "messages": messages, "stream": False,
        "think": OLLAMA_THINK,
        "options": {"temperature": OLLAMA_TEMPERATURE,
                    "num_predict": OLLAMA_MAX_TOKENS},
    }
    if tools is not None:
        payload["tools"] = tools
    return payload


def _ollama_chat(messages: list[dict]) -> tuple[str, str]:
    tried: list[str] = []
    for host in _candidate_hosts():
        tried.append(host)
        try:
            data = _post_ollama(host, _ollama_payload(messages))
            try:
                return data["message"]["content"], host
            except Exception as e:
                raise RuntimeError(f"Bad Ollama response on `{host}`: {e}")
        except _HostUnreachable:
            continue
    raise _unreachable_error(tried)


def _ollama_chat_native(messages: list[dict]) -> tuple[dict, str]:
    tried: list[str] = []
    for host in _candidate_hosts():
        tried.append(host)
        try:
            data = _post_ollama(host, _ollama_payload(messages, OLLAMA_TOOLS))
            try:
                return data["message"], host
            except Exception as e:
                raise RuntimeError(f"Bad Ollama response on `{host}`: {e}")
        except _HostUnreachable:
            continue
    raise _unreachable_error(tried)


def _openai_chat_native(messages: list[dict]) -> tuple[dict, str]:
    try:
        if not OPENAI_API_KEY:
            raise RuntimeError("`OPENAI_API_KEY` is empty. Set it or use `LLM_PROVIDER=ollama`.")
        r = httpx.post(f"{OPENAI_BASE_URL}/chat/completions", headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={"model": OPENAI_MODEL, "messages": messages,
                  "temperature": OPENAI_TEMPERATURE, "max_tokens": OPENAI_MAX_TOKENS,
                  "tools": OLLAMA_TOOLS},
            timeout=OPENAI_TIMEOUT_SECONDS)
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"OpenAI request failed ({e.response.status_code}): {e.response.text[:300]}")
        try:
            return r.json()["choices"][0]["message"], OPENAI_BASE_URL
        except Exception as e:
            raise RuntimeError(f"Bad OpenAI response: {e}")
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"OpenAI error: {e}")


def _llm_ask(messages: list[dict]) -> tuple[str | None, str | None, str]:
    try:
        text, _host = _ollama_chat(messages)
        return text, None, "ok"
    except RuntimeError as e:
        w = str(e)
        return None, w, _classify_reason(w)
    except Exception as e:
        w = f"LLM error: {e}"
        return None, w, _classify_reason(w)


def _tags_on(host: str) -> list[str] | None:
    try:
        r = httpx.get(f"{host}/api/tags", timeout=10)
        r.raise_for_status()
        try:
            return [m.get("name", "") for m in r.json().get("models", [])]
        except Exception:
            return []
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"Ollama tags check failed on `{host}`: {e.response.text[:200]}")
    except Exception:
        return None


def llm_status() -> dict:
    try:
        if LLM_PROVIDER == "openai":
            if not OPENAI_API_KEY:
                hint = "`OPENAI_API_KEY` is empty. Set it or use `LLM_PROVIDER=ollama`."
                return {"provider": "openai", "model": OPENAI_MODEL, "available": False,
                        "hint": hint, "reason": "error"}
            return {"provider": "openai", "model": OPENAI_MODEL, "available": True,
                    "hint": None, "reason": "ok"}
        working_host = None
        models: list[str] = []
        for host in _candidate_hosts():
            try:
                got = _tags_on(host)
            except RuntimeError as e:
                return {"provider": "ollama", "host": host, "model": OLLAMA_MODEL,
                        "available": False, "hint": str(e), "reason": "error"}
            if got is not None:
                working_host, models = host, got
                break
        if working_host is None:
            _, warning, reason = _llm_ask([{"role": "user", "content": "ping"}])
            if warning:
                return {"provider": "ollama", "host": OLLAMA_HOST, "model": OLLAMA_MODEL,
                        "available": False, "hint": warning, "reason": reason}
            return {"provider": "ollama", "host": OLLAMA_HOST, "model": OLLAMA_MODEL,
                    "available": False, "hint": "Ollama unreachable.", "reason": "unreachable"}
        if models and not any(OLLAMA_MODEL in m or m in OLLAMA_MODEL for m in models):
            hint = _pull_hint(working_host)
            return {"provider": "ollama", "host": working_host, "model": OLLAMA_MODEL,
                    "available": False, "models": models, "hint": hint, "reason": "missing-model"}
        return {"provider": "ollama", "host": working_host, "model": OLLAMA_MODEL,
                "available": True, "models": models, "hint": None, "reason": "ok"}
    except Exception as e:
        return {"provider": LLM_PROVIDER, "model": OLLAMA_MODEL, "available": False,
                "hint": f"LLM status check failed: {e}", "reason": "error"}
