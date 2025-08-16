# main.py
from __future__ import annotations

import os
import uuid
import json
import logging
from typing import Any, Dict, List, Optional, Literal

from fastapi import FastAPI, HTTPException, Header, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from core.env_health import log_env_report, ensure_env
from core.config import settings
from routers.search import router as search_router
from services import (
    gemini_service,
    groq_service,
    hf_service,
    pollinations_service,
    ddg_service,
    brain_service,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("syne-backend")

# Initialize FastAPI app
app = FastAPI(title="Syne API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the standalone search router
app.include_router(search_router)


@app.on_event("startup")
async def startup_env_check():
    # Print a redacted snapshot of env vars
    log_env_report()
    # In production, fail fast on missing/invalid vars
    if settings.env.lower() == "production":
        ensure_env(strict=True)


# -----------------------------
# Session stores
# -----------------------------

class BaseStore:
    async def get_session(self, session_id: str) -> Dict[str, Any]:
        raise NotImplementedError

    async def set_session(self, session_id: str, data: Dict[str, Any]) -> None:
        raise NotImplementedError

    async def new_session(self) -> str:
        raise NotImplementedError

    async def close(self) -> None:
        pass


class InMemoryStore(BaseStore):
    def __init__(self) -> None:
        self._db: Dict[str, Dict[str, Any]] = {}

    async def get_session(self, session_id: str) -> Dict[str, Any]:
        return self._db.get(session_id, {"messages": []})

    async def set_session(self, session_id: str, data: Dict[str, Any]) -> None:
        self._db[session_id] = data

    async def new_session(self) -> str:
        session_id = str(uuid.uuid4())
        self._db[session_id] = {"messages": []}
        return session_id


try:
    import redis.asyncio as redis  # redis-py >= 4.2
except ImportError:
    redis = None


class RedisStore(BaseStore):
    def __init__(
        self,
        url: str,
        key_prefix: str = "syne:sessions:",
        decode_responses: bool = True,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        if not redis:
            raise RuntimeError("Redis is not available. Install redis and set REDIS_URL.")
        self._r = redis.from_url(url, decode_responses=decode_responses)
        self.key_prefix = key_prefix
        self.ttl_seconds = ttl_seconds

    def _key(self, session_id: str) -> str:
        return f"{self.key_prefix}{session_id}"

    async def get_session(self, session_id: str) -> Dict[str, Any]:
        raw = await self._r.get(self._key(session_id))
        if not raw:
            return {"messages": []}
        try:
            return json.loads(raw)
        except Exception:
            return {"messages": []}

    async def set_session(self, session_id: str, data: Dict[str, Any]) -> None:
        payload = json.dumps(data, ensure_ascii=False)
        key = self._key(session_id)
        if self.ttl_seconds:
            await self._r.set(key, payload, ex=self.ttl_seconds)
        else:
            await self._r.set(key, payload)

    async def new_session(self) -> str:
        session_id = str(uuid.uuid4())
        await self.set_session(session_id, {"messages": []})
        return session_id

    async def close(self) -> None:
        try:
            await self._r.close()
        except Exception:
            pass


def build_store() -> BaseStore:
    redis_url = os.getenv("REDIS_URL")
    if redis_url and redis:
        ttl_env = os.getenv("SESSION_TTL_SECONDS")
        ttl = int(ttl_env) if ttl_env and ttl_env.isdigit() else None
        logger.info("Using Redis session store.")
        return RedisStore(url=redis_url, ttl_seconds=ttl)
    logger.info("Using in-memory session store.")
    return InMemoryStore()


store: BaseStore = build_store()


# -----------------------------
# Models
# -----------------------------

class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    model: Literal["gemini", "groq", "hf", "pollinations", "auto"] = "auto"
    edit_index: Optional[int] = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    history: List[Message]


# -----------------------------
# Helpers
# -----------------------------

def append_message(history: List[Dict[str, Any]], role: str, content: str) -> None:
    history.append({"role": role, "content": content})


def to_messages(raw: List[Dict[str, Any]]) -> List[Message]:
    msgs: List[Message] = []
    for item in raw:
        if (
            isinstance(item, dict)
            and item.get("role") in ("user", "assistant", "system")
            and isinstance(item.get("content"), str)
        ):
            msgs.append(Message(role=item["role"], content=item["content"]))
    return msgs


# -----------------------------
# Chat endpoint
# -----------------------------

@app.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    response: Response,
    session_id: Optional[str] = Header(None, alias="session-id"),
):
    # Ensure or create session
    if not session_id:
        session_id = await store.new_session()
    response.headers["session-id"] = session_id

    # Load & sanitize history
    session_data = await store.get_session(session_id)
    history = session_data.get("messages", [])

    # Handle edit (regenerate from index)
    if req.edit_index is not None:
        if 0 <= req.edit_index <= len(history):
            history = history[: req.edit_index]
        else:
            raise HTTPException(status_code=400, detail="edit_index out of range")

    # Smart search context
    search_results: Optional[List[Dict[str, str]]] = None
    if brain_service.should_search(req.prompt):
        try:
            query = brain_service.extract_query(req.prompt)
            search_results = await run_in_threadpool(ddg_service.search, query, 5)
            if search_results:
                context = "\n".join(
                    f"Title: {r['title']}\nSnippet: {r['snippet']}"
                    for r in search_results[:3]
                )
                append_message(history, "system", f"Search context:\n{context}")
        except Exception as e:
            logger.warning("Search failed: %s", e)

    # Auto-model selection
    picked = req.model
    if picked == "auto":
        picked = brain_service.pick_model(req.prompt)
    if picked not in ("gemini", "groq", "hf", "pollinations"):
        picked = "gemini"

    # Record user prompt
    append_message(history, "user", req.prompt)

    # Route to chosen AI
    try:
        if picked == "gemini":
            reply = await run_in_threadpool(gemini_service.chat, history)
        elif picked == "groq":
            reply = await run_in_threadpool(groq_service.chat, history)
        elif picked == "hf":
            prompt_text = req.prompt
            if search_results:
                ctx = " ".join(r["snippet"] for r in search_results[:3])
                prompt_text = f"Context: {ctx}\n\nQuestion: {req.prompt}"
            reply = await run_in_threadpool(hf_service.chat, prompt_text)
        else:  # pollinations
            reply = await run_in_threadpool(pollinations_service.chat, req.prompt)

        # Save assistant response
        append_message(history, "assistant", reply)
        await store.set_session(session_id, {"messages": history})

        return ChatResponse(
            reply=reply,
            session_id=session_id,
            history=to_messages(history),
        )

    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error in /chat")
        raise HTTPException(status_code=500, detail="Internal error")


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host if hasattr(settings, "host") else "0.0.0.0",
        port=settings.port,
        reload=settings.env.lower() != "production",
  )
