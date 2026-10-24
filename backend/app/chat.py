"""Owned guest routes and SSE, with committed final answers and source references."""

import asyncio
import json
import logging
from uuid import UUID

import anyio
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.agent import generate_reply
from backend.app.diagnostics import AssistantFailure
from backend.app.sessions import COOKIE, SESSION_SECONDS, GuestStore


class ChatInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    turn_id: UUID
    message: str = Field(min_length=1, max_length=2000)

    @field_validator("message")
    @classmethod
    def nonblank(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Enter a message")
        return value


async def stub_reply(message):
    answer = (
        "This is a demo reply. The hotel AI assistant is not connected yet. "
        "Your completed messages are saved in this browser session. "
        "No reservation has been made."
    )
    for word in answer.split(" "):
        await asyncio.sleep(0.025)
        yield word + " "


def event(name, data):
    return f"event: {name}\ndata: {json.dumps(data)}\n\n"


class GuestStream(StreamingResponse):
    def __init__(self, content, store, session, turn_id):
        super().__init__(
            content,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-store",
                "X-Accel-Buffering": "no",
            },
        )
        self.store, self.session, self.turn_id = store, session, turn_id

    async def __call__(self, scope, receive, send):
        try:
            await super().__call__(scope, receive, send)
        finally:
            # Also runs when disconnected before the generator starts.
            with anyio.move_on_after(5, shield=True):
                try:
                    await self.store.interrupt(self.session, self.turn_id)
                except Exception:
                    logging.warning("Turn cleanup failed; the busy lease will expire")


def guest_routes(settings):
    router = APIRouter()

    def store(request):
        return GuestStore(request.app.state.pool)

    def origin(request):
        if request.headers.get("origin") != settings.app_origin:
            raise HTTPException(403, "Open the chat from the hotel website.")

    @router.post("/api/session")
    async def session(request: Request):
        origin(request)
        token, conversation = await store(request).session(request.cookies.get(COOKIE))
        response = JSONResponse({"conversation_id": str(conversation)})
        if token:
            response.set_cookie(
                COOKIE,
                token,
                max_age=SESSION_SECONDS,
                httponly=True,
                secure=settings.cookie_secure,
                samesite="strict",
                path="/",
            )
        return response

    @router.get("/api/history")
    async def history(request: Request):
        return await store(request).history(request.cookies.get(COOKIE))

    @router.post("/api/conversation")
    async def reset(request: Request):
        origin(request)
        return await store(request).reset(request.cookies.get(COOKIE))

    @router.post("/api/chat")
    async def chat(request: Request, body: ChatInput):
        origin(request)
        guest_store = store(request)
        session, conversation = await guest_store.admit(
            request.cookies.get(COOKIE), body.turn_id, body.message
        )

        async def stream():
            try:
                async with asyncio.timeout(90):
                    yield event("turn_started", {"turn_id": str(body.turn_id)})
                    parts = []
                    size = 0
                    sources = []
                    if settings.assistant_mode == "vertex":
                        previous = await guest_store.history(request.cookies.get(COOKIE))
                        reply = await generate_reply(
                            settings, request.app.state.hotel, body.message, previous["turns"]
                        )
                        logging.info("Assistant completed: %s", json.dumps(reply.diagnostics))
                        parts.append(reply.answer)
                        sources = reply.sources
                    else:
                        async for part in request.app.state.reply(body.message):
                            size += len(part)
                            if size > 16000:
                                raise RuntimeError("Reply too large")
                            parts.append(part)
                            yield event("text", {"text": part})
                    answer = "".join(parts).strip()
                    if not answer:
                        raise RuntimeError("Empty reply")
                    result = {"turn_id": str(body.turn_id), "answer": answer, "sources": sources}
                    if len(json.dumps(result).encode("utf-8")) > 65536:
                        raise RuntimeError("Result too large")
                    await guest_store.complete(session, conversation, body.turn_id, answer, sources)
                    yield event("result", result)
                    yield event("done", {})
            except Exception as exc:
                if isinstance(exc, AssistantFailure):
                    logging.warning("Assistant failed: %s", json.dumps(exc.diagnostics))
                yield event(
                    "error", {"message": "Reply interrupted. Reload history, then try again."}
                )

        return GuestStream(stream(), guest_store, session, body.turn_id)

    return router
