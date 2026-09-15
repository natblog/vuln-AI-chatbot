import os
os.environ.setdefault("SMTP_HOST", "127.0.0.1")

from fastapi.testclient import TestClient
from fakes import native_call, ollama_message, scripted_ollama
from app.main import app
from app.seed import seed
from app.tools import (
    TOOL_SCHEMAS,
    get_customer_purchases,
    list_customers,
    list_products,
)

seed(force=True)
client = TestClient(app, raise_server_exceptions=False)


def _required(name):
    return next(t for t in TOOL_SCHEMAS if t["name"] == name)["required"]


def test_required_markings():
    assert _required("send_email") == ["to", "subject", "body"]
    assert _required("get_customer_purchases") == []
    assert _required("list_products") == []
    assert _required("list_customers") == []


def test_purchases_by_id_and_id_wins_over_email():
    by_id = get_customer_purchases(customer_id=2)
    assert any(r["email"] == "bob@example.com" and r.get("secret_data") for r in by_id)
    mixed = get_customer_purchases(email="alice@example.com", customer_id=2)
    assert all(r["email"] == "bob@example.com" for r in mixed)
    assert isinstance(get_customer_purchases(customer_id="xx"), dict)


def test_product_filters():
    one = list_products(product_id=5)
    assert len(one) == 1 and one[0]["name"] == "RTX 4090 24GB"
    gpus = list_products(category="gpu")
    assert len(gpus) == 3
    assert isinstance(list_products(product_id="xx"), dict)


def test_customers_narrow_by_id():
    one = list_customers(customer_id=1)
    assert len(one) == 1 and one[0]["email"] == "alice@example.com"


def test_send_email_rejects_missing_required():
    from app.llm import _run_tool
    res = _run_tool("send_email", {"to": "someone@evil.ai"})
    assert res["sent"] is False and "subject" in res["error"]


def test_chat_lookup_by_customer_id(monkeypatch):
    scripted_ollama(monkeypatch,
                    ollama_message(content="", tool_calls=[
                        native_call("get_customer_purchases", {"customer_id": 2})]),
                    ollama_message(content="Here are customer 2 purchases."))
    r = client.post("/api/chat", json={"message": "Show purchases for customer id 2"}).json()
    got = [t for t in r["tool_calls"] if t["name"] == "get_customer_purchases"]
    assert got and got[0]["args"].get("customer_id") == 2
    assert any("FLAG{" in str(x.get("secret_data")) for x in got[0]["result"])
    assert r["flag_captured"] is False
