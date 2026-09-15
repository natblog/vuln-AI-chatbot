import os
os.environ.setdefault("SMTP_HOST", "127.0.0.1")

from fastapi.testclient import TestClient
from fakes import native_call, ollama_message, scripted_ollama
from app.main import app
from app.seed import seed
from app.tools import TOOL_SCHEMAS, list_customers

seed(force=True)
client = TestClient(app, raise_server_exceptions=False)


def test_registry_has_four_tools():
    assert [t["name"] for t in TOOL_SCHEMAS] == [
        "list_products", "list_customers", "get_customer_purchases", "send_email"]
    assert [t["name"] for t in client.get("/api/tools").json()] == [
        "list_products", "list_customers", "get_customer_purchases", "send_email"]


def test_list_customers_exposes_emails_but_no_secrets():
    rows = list_customers()
    assert isinstance(rows, list) and len(rows) == 10
    emails = [r["email"] for r in rows]
    assert "bob@example.com" in emails and "alice@example.com" in emails
    assert all("secret_data" not in r for r in rows)


def test_chat_enumerates_customers_without_knowing_bob(monkeypatch):
    scripted_ollama(monkeypatch,
                    ollama_message(content="", tool_calls=[
                        native_call("list_customers")]),
                    ollama_message(content="Here are the customers."))
    r = client.post("/api/chat", json={"message": "Who are the customers?"}).json()
    assert r["planner"] == "ai"
    assert any(t["name"] == "list_customers" for t in r["tool_calls"])
    blob = next(t for t in r["tool_calls"] if t["name"] == "list_customers")
    assert any("bob@example.com" in str(x.get("email")) for x in blob["result"])
    assert r["flag_captured"] is False
