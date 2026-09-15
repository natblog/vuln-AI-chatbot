import logging
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import ATTACKER_EMAIL, CURRENT_USER_EMAIL
from .database import init_db
from .llm import chat
from .ollama import llm_status
from .schemas import ChatRequest, ChatResponse
from .seed import seed
from .tools import TOOL_SCHEMAS, get_customer_purchases, list_products

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
log = logging.getLogger("vulnlab")

app = FastAPI(title="AI Vuln Chat Lab (deliberately vulnerable)")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(Exception)
async def unhandled_exception(_request, exc: Exception):
    log.exception("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"detail": f"Internal error: {exc}"})


try:
    init_db()
except Exception as e:
    log.exception("DB init failed: %s", e)
try:
    seed()
except Exception as e:
    log.exception("DB seed failed: %s", e)


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/me")
def me():
    return {"email": CURRENT_USER_EMAIL, "attacker_email": ATTACKER_EMAIL}


@app.get("/api/llm-status")
def llm_status_ep():
    return llm_status()


@app.get("/api/products")
def products():
    res = list_products()
    if isinstance(res, dict) and res.get("error"):
        raise HTTPException(status_code=500, detail=res["error"])
    return res


@app.get("/api/purchases")
def purchases(email: str | None = None, customer_id: int | None = None):
    res = get_customer_purchases(email, customer_id)
    if isinstance(res, dict) and res.get("error"):
        raise HTTPException(status_code=500, detail=res["error"])
    return res


@app.get("/api/tools")
def tool_list():
    return TOOL_SCHEMAS


@app.post("/api/chat", response_model=ChatResponse)
def chat_ep(req: ChatRequest):
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="Message is empty.")
    return chat(req.message, req.history or [])


@app.post("/api/reset")
def reset():
    return {"ok": True}


@app.post("/api/reseed")
def reseed():
    return seed(force=True)
