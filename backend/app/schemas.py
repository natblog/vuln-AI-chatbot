from typing import Any, Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    history: Optional[list[dict[str, Any]]] = None


class ToolCallRecord(BaseModel):
    name: str
    args: dict[str, Any]
    result: Any
    summary: str = ""


class ChatResponse(BaseModel):
    reply_markdown: str
    tool_calls: list[ToolCallRecord] = []
    flag_captured: bool = False
    flag: Optional[str] = None
    llm_warning: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_reason: Optional[str] = None
    planner: str = "none"
