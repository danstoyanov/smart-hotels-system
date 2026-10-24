"""Whole-stay contracts against a disposable database; no provider calls."""

import asyncio
import json
from datetime import UTC, date, datetime, timedelta

import psycopg
import pytest
from fastapi.testclient import TestClient
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.genai import types
from pydantic import Field

from backend.app.agent import generate_reply
from backend.app.db import create_pool, migrate
from backend.app.hotel import HotelStore
from backend.app.inventory import Availability, load_inventory, validate_stay
from backend.app.main import create_app
from backend.app.runtime import new_loop
from backend.app.settings import ROOT, Settings
from backend.app.tools import HotelTools


def test_date_validation_uses_property_day():
    now = datetime(2026, 10, 24, 22, 30, tzinfo=UTC)
    with pytest.raises(ValueError, match="Check-in"):
        validate_stay("2026-10-24", "2026-10-26", 2, "Europe/Kyiv", now=now)
    assert validate_stay("2026-10-25", "2026-10-26", 2, "Europe/Kyiv", now=now)[0] == date(
        2026, 10, 25
    )
    for start, end, guests in [
        ("2026-10-25", "2026-10-25", 2),
        ("2026-10-26", "2026-10-25", 2),
        ("2026-02-30", "2026-10-26", 2),
        ("20261025", "2026-10-26", 2),
        ("2026-10-25", "2026-10-26", True),
        ("2026-10-25", "2026-10-26", 0),
        ("2026-10-25", "2026-10-26", 21),
        ("2026-10-25", "2028-10-26", 2),
    ]:
        with pytest.raises(ValueError):
            validate_stay(start, end, guests, "Europe/Kyiv", now=now)


class SearchModel(BaseLlm):
    model: str = "offline-search-contract"
    requests: list = Field(default_factory=list)
    arguments: dict = Field(default_factory=dict)

    async def generate_content_async(self, llm_request, stream=False):
        self.requests.append(
            {
                "contents": json.dumps(
                    [item.model_dump(mode="json") for item in llm_request.contents]
                ),
                "tools": str(llm_request.config.tools),
            }
        )
        part = (
            types.Part(
                function_call=types.FunctionCall(name="search_availability", args=self.arguments)
            )
            if len(self.requests) == 1
            else types.Part(text="Scripted demo search answer. No room held.")
        )
        yield LlmResponse(content=types.Content(role="model", parts=[part]))


def test_postgres_api_tool_full_stay(database_url, tmp_path):
    # Keep the accepted fixture pattern but move its dates so this test does not expire.
    from zoneinfo import ZoneInfo

    start = datetime.now(ZoneInfo("Europe/Kyiv")).date() + timedelta(days=10)
    data = json.loads((ROOT / "hotel/revisions/royal-crest-demo.v1.json").read_text())
    data["source_id"] = "availability-test"
    for night in data["inventory"]:
        offset = (date.fromisoformat(night["night"]) - date(2026, 11, 1)).days
        night["night"] = (start + timedelta(days=offset)).isoformat()
    (tmp_path / "data.json").write_text(json.dumps(data))
    (tmp_path / "catalogue.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "sources": [{"source_id": "availability-test", "version": 1, "file": "data.json"}],
                "active_source_id": "availability-test",
                "active_version": 1,
            }
        )
    )
    hotel = HotelStore(tmp_path)
    hotel.reload()

    def day(offset):
        return (start + timedelta(days=offset)).isoformat()

    async def exercise():
        await migrate(database_url)
        async with create_pool(database_url) as pool:
            # This dedicated source belongs only to this disposable integration check.
            async with pool.connection() as conn:
                await conn.execute(
                    "DELETE FROM inventory_nights WHERE source_id='availability-test'"
                )
                await conn.execute(
                    "DELETE FROM inventory_rooms WHERE source_id='availability-test'"
                )
                await conn.execute(
                    "DELETE FROM inventory_sources WHERE source_id='availability-test'"
                )
            await load_inventory(pool, hotel)
            await load_inventory(pool, hotel)
            changed = json.loads(json.dumps(data))
            changed["rooms"][0]["capacity"] = 3
            (tmp_path / "data.json").write_text(json.dumps(changed))
            altered = HotelStore(tmp_path)
            altered.reload()
            with pytest.raises(ValueError, match="revision changed"):
                await load_inventory(pool, altered)
            (tmp_path / "data.json").write_text(json.dumps(data))
            service = Availability(pool, hotel)
            before = await service.search(day(0), day(2), 2)
            assert {r["id"] for r in before["rooms"]} == {"manor-suite", "garden-room"}
            assert before["demo"] and before["nights"] == 2
            assert (await service.search(day(0), day(2), 3))["rooms"][0]["id"] == "garden-room"
            assert (await service.search(day(0), day(2), 5))["status"] == "no_match"
            # Garden is closed on day 4: checkout excludes it; adjacent arrival includes it.
            assert (await service.search(day(0), day(4), 4))["status"] == "ok"
            assert (await service.search(day(4), day(5), 4))["status"] == "no_match"
            assert (await service.search(day(3), day(6), 4))["status"] == "no_match"
            assert (await service.search(day(5), day(7), 4))["status"] == "ok"
            assert (await service.search(day(6), day(8), 2))["status"] == "unknown_inventory"
            assert (await service.search(day(20), day(21), 2))["status"] == "unknown_inventory"
            for arrival, departure, guests in [
                (day(1), day(0), 2),
                (day(0), day(0), 2),
                (day(0), day(1), 0),
                ("bad", day(1), 2),
            ]:
                assert (await service.search(arrival, departure, guests))[
                    "status"
                ] == "invalid_input"
            tool_result = await HotelTools(hotel, service).search_availability(day(0), day(2), 2)
            assert tool_result == before
            tools = HotelTools(hotel, service)
            tools.characters = 24000
            assert (await tools.search_availability(day(0), day(2), 2))["status"] == "limit_reached"
            tools = HotelTools(hotel, service)
            tools.calls = 8
            assert (await tools.search_availability(day(0), day(2), 2))["status"] == "limit_reached"
            # Missing one room-night must not erase a valid match for another room.
            async with pool.connection() as conn:
                await conn.execute(
                    "DELETE FROM inventory_nights WHERE source_id='availability-test' "
                    "AND room_id='garden-room' AND night=%s",
                    (start,),
                )
            partial = await service.search(day(0), day(2), 2)
            assert [r["id"] for r in partial["rooms"]] == ["manor-suite"]
            assert partial["unknown_room_ids"] == ["garden-room"]
            # Restore only the changed factor; all other fixture data stays unchanged.
            async with pool.connection() as conn:
                await conn.execute(
                    "INSERT INTO inventory_nights VALUES "
                    "('availability-test',1,'garden-room',%s,true)",
                    (start,),
                )
            # Direct SQL callers receive the same capacity and date safeguards.
            for arrival, departure, guests in [
                (start, start, 2),
                (start, start + timedelta(days=1), 0),
                (date(2000, 1, 1), start, 2),
                (start, start + timedelta(days=367), 2),
            ]:
                with pytest.raises(psycopg.errors.InvalidParameterValue):
                    async with pool.connection() as conn:
                        await conn.execute(
                            "SELECT * FROM search_inventory('availability-test',1,%s,%s,%s)",
                            (arrival, departure, guests),
                        )
            async with pool.connection() as conn:
                rows = await (
                    await conn.execute(
                        "SELECT * FROM search_inventory('availability-test',1,%s,%s,4)",
                        (start, start + timedelta(days=2)),
                    )
                ).fetchall()
                assert (
                    len(rows) == 1
                    and rows[0][0]["id"] == "garden-room"
                    and rows[0][1] == "available"
                )
                stored = await (
                    await conn.execute(
                        "SELECT snapshot FROM inventory_sources WHERE source_id='availability-test'"
                    )
                ).fetchone()
                nights = await (
                    await conn.execute(
                        "SELECT room_id,night,is_open FROM inventory_nights "
                        "WHERE source_id='availability-test' ORDER BY room_id,night"
                    )
                ).fetchall()
            model = SearchModel(arguments={"check_in": day(0), "check_out": day(2), "guests": 2})
            await generate_reply(
                Settings(_env_file=None),
                hotel,
                "Search these dates",
                model_override=model,
                availability=service,
            )
            assert "search_availability" in model.requests[0]["tools"]
            assert (
                "manor-suite" in model.requests[1]["contents"]
                and "garden-room" in model.requests[1]["contents"]
            )
            assert await service.search(day(0), day(2), 2) == before
            async with pool.connection() as conn:
                assert (
                    await (
                        await conn.execute(
                            "SELECT room_id,night,is_open FROM inventory_nights "
                            "WHERE source_id='availability-test' ORDER BY room_id,night"
                        )
                    ).fetchall()
                    == nights
                )
                assert (
                    await (
                        await conn.execute(
                            "SELECT snapshot FROM inventory_sources "
                            "WHERE source_id='availability-test'"
                        )
                    ).fetchone()
                ) == stored
            return before

    before = asyncio.run(exercise(), loop_factory=new_loop)
    app = create_app(Settings(_env_file=None, database_url=database_url), hotel_directory=tmp_path)
    with TestClient(app, backend_options={"loop_factory": new_loop}) as client:
        query = {"check_in": day(0), "check_out": day(2), "guests": 2}
        response = client.get("/api/availability", params=query)
        assert response.status_code == 200 and response.json() == before
        assert response.headers["cache-control"] == "no-store"
        for patch in [{"check_in": "bad"}, {"guests": 0}, {"guests": "2.5"}, {"check_out": day(0)}]:
            assert client.get("/api/availability", params={**query, **patch}).status_code == 422
        assert (
            client.get("/api/availability", params={**query, "guests": 5}).json()["status"]
            == "no_match"
        )
        assert (
            client.get("/api/availability", params={**query, "check_out": day(8)}).json()["status"]
            == "unknown_inventory"
        )
