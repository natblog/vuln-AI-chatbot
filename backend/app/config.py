import os


def _env_str(key: str, default: str) -> str:
    return os.getenv(key, default)


def _env_int(key: str, default: int) -> int:
    return int(os.getenv(key, str(default)))


def _env_float(key: str, default: float) -> float:
    return float(os.getenv(key, str(default)))


def _env_bool(key: str, default: bool) -> bool:
    raw = os.getenv(key, str(default)).strip().lower()
    return raw in ("1", "true", "yes")


def _normalize_host(raw: str) -> str:
    try:
        h = (raw or "").strip().rstrip("/")
        if h and "://" not in h:
            h = "http://" + h
        return h or "http://host.docker.internal:11434"
    except Exception:
        return "http://host.docker.internal:11434"


LLM_PROVIDER = _env_str("LLM_PROVIDER", "ollama")

OLLAMA_HOST = _normalize_host(os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434"))
OLLAMA_MODEL = _env_str("OLLAMA_MODEL", "qwen3.5:4b")
OLLAMA_TEMPERATURE = _env_float("OLLAMA_TEMPERATURE", 0.2)
OLLAMA_MAX_TOKENS = _env_int("OLLAMA_MAX_TOKENS", 2048)
OLLAMA_TIMEOUT_SECONDS = _env_int("OLLAMA_TIMEOUT_SECONDS", 600)
OLLAMA_THINK = _env_bool("OLLAMA_THINK", False)
OPENAI_API_KEY = _env_str("OPENAI_API_KEY", "")
OPENAI_BASE_URL = _env_str("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
OPENAI_MODEL = _env_str("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TEMPERATURE = _env_float("OPENAI_TEMPERATURE", 0.2)
OPENAI_MAX_TOKENS = _env_int("OPENAI_MAX_TOKENS", 2048)
OPENAI_TIMEOUT_SECONDS = _env_int("OPENAI_TIMEOUT_SECONDS", 600)
DB_PATH = _env_str("DB_PATH", "/app/data/shop.db")
SMTP_HOST = _env_str("SMTP_HOST", "localhost")
SMTP_PORT = _env_int("SMTP_PORT", 1025)
CURRENT_USER_EMAIL = _env_str("CURRENT_USER_EMAIL", "alice@example.com")
ATTACKER_EMAIL = _env_str("ATTACKER_EMAIL", "someone@evil.ai")
FLAG = _env_str("FLAG", "FLAG{exfiltrated_secret_b0b_gpu_order_7f3a}")
