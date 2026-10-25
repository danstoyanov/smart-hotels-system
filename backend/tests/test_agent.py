"""Deterministic SDK/tool contracts. These checks never call a model provider."""

import asyncio

import pytest
from google.adk.agents.invocation_context import LlmCallsLimitExceededError
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.genai import types
from pydantic import Field, ValidationError

from backend.app.agent import bounded_history, generate_reply
from backend.app.hotel import HotelStore
from backend.app.settings import Settings
from backend.app.tools import HotelTools


def hotel():
    store = HotelStore()
    store.reload()
    return store


class ScriptedModel(BaseLlm):
    model: str = "offline-contract-model"
    requests: list = Field(default_factory=list)
    fail: bool = False
    empty: bool = False
    loop: bool = False

    async def generate_content_async(self, llm_request, stream=False):
        self.requests.append(llm_request.model_copy(deep=True))
        if self.fail:
            raise RuntimeError("provider private details")
        if self.loop or len(self.requests) == 1:
            yield LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            function_call=types.FunctionCall(
                                name="read_information",
                                args={"section": "policies", "item_id": "arrival"},
                            )
                        )
                    ],
                )
            )
        else:
            yield LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[
                        types.Part(text="internal reasoning", thought=True),
                        types.Part(text="" if self.empty else "scripted final"),
                    ],
                ),
                usage_metadata=types.GenerateContentResponseUsageMetadata(total_token_count=42),
            )


def test_tools_sources_unknown_isolation_and_bounds():
    store = hotel()
    first, second = HotelTools(store), HotelTools(store)
    assert "inventory" not in first.list_information()["sections"]
    assert first.sources == {}
    result = first.read_information("policies", "prices")
    assert result["status"] == "unknown"
    result["record"]["body"] = "changed"
    assert "changed" not in first.read_information("policies", "prices")["record"]["body"]
    source = next(iter(first.sources.values()))
    assert source["url"].endswith("source_id=royal-crest-demo&version=2")
    assert second.sources == {}
    assert first.read_information("inventory", "x")["status"] == "invalid_input"
    assert first.read_information("policies", "missing")["status"] == "not_found"
    first.characters = 24000
    assert first.read_information("policies", "arrival")["status"] == "limit_reached"
    for _ in range(8):
        first.list_information()
    assert first.read_information("policies", "arrival")["status"] == "limit_reached"
    assert HotelTools(HotelStore()).list_information()["status"] == "unavailable"
    oversized = HotelTools(store)
    oversized.sections["policies"]["data"][0]["title"] = "x" * 6001
    assert oversized.list_information()["status"] == "limit_reached"


def test_history_bounds_and_vertex_configuration():
    turns = [{"question": str(i), "answer": "a"} for i in range(25)]
    assert bounded_history(turns) == turns[-20:]
    assert bounded_history([{"question": "x" * 16001, "answer": ""}]) == []
    with pytest.raises(ValidationError):
        Settings(_env_file=None, assistant_mode="vertex")
    assert Settings(_env_file=None).assistant_mode == "stub"


def test_real_adk_tool_cycle_history_and_final_output():
    model = ScriptedModel()
    result = asyncio.run(
        generate_reply(
            Settings(_env_file=None),
            hotel(),
            "arrival?",
            [{"question": "private prior question", "answer": "prior answer"}],
            model_override=model,
        )
    )
    assert result.answer == "scripted final"
    assert len(result.sources) == 1
    assert result.sources[0]["title"] == "Arrival and departure"
    assert result.usage["total_tokens"] == 42
    request_text = str(model.requests[0].contents)
    instruction = str(model.requests[0].config.system_instruction)
    assert model.requests[0].config.temperature is None
    assert "Catalogue data" in instruction and '"id": "arrival"' in instruction
    assert "Records read by the application" in instruction
    assert "Check-in starts at 15:00" in instruction
    assert "private prior question" in request_text
    assert "prior answer" in request_text
    assert "15:00" in str(model.requests[1].contents)
    fresh = ScriptedModel()
    asyncio.run(generate_reply(Settings(_env_file=None), hotel(), "hello", model_override=fresh))
    assert "private prior question" not in str(fresh.requests[0].contents)


def test_prepared_context_reads_records_within_existing_budget():
    tools = HotelTools(hotel())
    assert any(
        row.get("record", {}).get("id") == "arrival"
        for row in tools.prepare_context("When can I check in and check out?")
    )
    prices = HotelTools(hotel())
    context = prices.prepare_context("What does the Manor Suite cost per night?")
    assert any(
        row.get("record", {}).get("id") == "prices" and row["status"] == "unknown"
        for row in context
    )
    assert len(context) <= 4 and prices.calls <= 4
    assert prices.characters <= 24000
    assert HotelTools(hotel()).prepare_context("nearest airport shuttle timetable?") == []


@pytest.mark.parametrize("options", [{"fail": True}, {"empty": True}, {"loop": True}])
def test_provider_failure_empty_output_and_call_limit(options):
    model = ScriptedModel(**options)
    with pytest.raises((RuntimeError, LlmCallsLimitExceededError)):
        asyncio.run(generate_reply(Settings(_env_file=None), hotel(), "test", model_override=model))
    assert len(model.requests) <= 8
