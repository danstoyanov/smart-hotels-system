"""ADK boundary. SDK clients and working state live for exactly one invocation."""

import asyncio
from contextlib import aclosing
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

from backend.app.tools import HotelTools


@dataclass
class Reply:
    answer: str
    sources: list[dict] = field(default_factory=list)
    usage: dict = field(default_factory=dict)


def bounded_history(turns):
    selected, size = [], 0
    for turn in reversed(turns[-20:]):
        length = len(turn["question"]) + len(turn["answer"])
        if size + length > 16000:
            break
        selected.append(turn)
        size += length
    return list(reversed(selected))


async def generate_reply(settings, hotel, message, history=(), *, model_override=None):
    # Stub startup never initializes Google credentials or a client.
    from google import genai
    from google.adk.agents import Agent
    from google.adk.agents.run_config import RunConfig, StreamingMode
    from google.adk.events import Event
    from google.adk.models import Gemini
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types

    if not message.strip() or len(message) > 2000:
        raise ValueError("Message must contain 1–2000 characters")
    tools = HotelTools(hotel)
    instruction = Path(__file__).with_name("assistant_prompt.txt").read_text(encoding="utf-8")
    instruction += (
        f"\nHotel: {settings.hotel_name}. Language: {settings.hotel_language}. "
        f"Timezone: {settings.hotel_timezone}. "
        f"Today: {datetime.now(ZoneInfo(settings.hotel_timezone)).date().isoformat()}."
    )
    client, runner = None, None
    usage = {"model_calls": 0, "total_tokens": 0}
    try:
        model = model_override
        if model is None:
            client = genai.Client(
                vertexai=True,
                project=settings.google_cloud_project,
                location=settings.google_cloud_location,
                http_options=types.HttpOptions(
                    api_version="v1",
                    timeout=60000,
                    retry_options=types.HttpRetryOptions(attempts=1),
                ),
            )
            model = Gemini(model=settings.gemini_model, client=client)
        agent = Agent(
            name="hotel_assistant",
            model=model,
            instruction=instruction,
            tools=[tools.list_information, tools.read_information],
            generate_content_config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=2048,
                thinking_config=types.ThinkingConfig(thinking_level="LOW"),
            ),
        )
        service = InMemorySessionService()
        identity = uuid4().hex
        session = await service.create_session(app_name="hotel", user_id=identity)
        for turn in bounded_history(history):
            for role, text in (("user", turn["question"]), ("model", turn["answer"])):
                await service.append_event(
                    session,
                    Event(
                        invocation_id=uuid4().hex,
                        author="user" if role == "user" else agent.name,
                        content=types.Content(role=role, parts=[types.Part(text=text)]),
                    ),
                )
        runner = Runner(agent=agent, app_name="hotel", session_service=service)
        answer = None
        async with asyncio.timeout(85):
            async with aclosing(
                runner.run_async(
                    user_id=identity,
                    session_id=session.id,
                    new_message=types.Content(role="user", parts=[types.Part(text=message)]),
                    run_config=RunConfig(max_llm_calls=8, streaming_mode=StreamingMode.SSE),
                )
            ) as events:
                async for event in events:
                    if event.error_code:
                        raise RuntimeError("Model request failed")
                    if event.usage_metadata and not event.partial:
                        usage["model_calls"] += 1
                        usage["total_tokens"] += event.usage_metadata.total_token_count or 0
                    if event.is_final_response() and event.content:
                        answer = "".join(
                            part.text
                            for part in event.content.parts or []
                            if part.text and not part.thought
                        ).strip()
        if not answer or len(answer) > 16000:
            raise RuntimeError("Missing or oversized final answer")
        return Reply(answer, list(tools.sources.values()), usage)
    finally:
        import anyio

        with anyio.move_on_after(5, shield=True):
            try:
                if runner:
                    await runner.close()
            finally:
                if client:
                    await client.aio.aclose()
                    client.close()
