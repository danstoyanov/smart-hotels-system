"""Reservation invariants against the disposable PostgreSQL database."""

import asyncio
import json
from datetime import datetime, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.app.bookings import BookingInput, BookingStore
from backend.app.db import create_pool, migrate
from backend.app.hotel import HotelStore
from backend.app.inventory import load_inventory
from backend.app.main import create_app
from backend.app.runtime import new_loop
from backend.app.settings import ROOT, Settings

ORIGIN = "http://testserver"


def test_demo_booking_retries_isolation_and_inventory(database_url, tmp_path):
    start = datetime.now(ZoneInfo("Europe/Kyiv")).date() + timedelta(days=10)
    source = f"booking-{uuid4().hex}"
    data = json.loads((ROOT / "hotel/revisions/royal-crest-demo.v1.json").read_text())
    data["source_id"] = source
    room_ids = {
        "manor-suite": f"booking-manor-{uuid4().hex[:8]}",
        "garden-room": f"booking-garden-{uuid4().hex[:8]}",
    }
    for room in data["rooms"]:
        room["id"] = room_ids[room["id"]]
    for night in data["inventory"]:
        night["room_id"] = room_ids[night["room_id"]]
        offset = (datetime.fromisoformat(night["night"]).date() - datetime(2026, 11, 1).date()).days
        night["night"] = (start + timedelta(days=offset)).isoformat()
    (tmp_path / "data.json").write_text(json.dumps(data))
    (tmp_path / "catalogue.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "sources": [{"source_id": source, "version": 1, "file": "data.json"}],
                "active_source_id": source,
                "active_version": 1,
            }
        )
    )
    hotel = HotelStore(tmp_path)
    hotel.reload()

    async def setup():
        await migrate(database_url)
        async with create_pool(database_url) as pool:
            await load_inventory(pool, hotel)

    asyncio.run(setup(), loop_factory=new_loop)
    app = create_app(
        Settings(_env_file=None, database_url=database_url, app_origin=ORIGIN),
        hotel_directory=tmp_path,
    )
    with TestClient(app, backend_options={"loop_factory": new_loop}) as client:

        def guest():
            client.cookies.clear()
            response = client.post("/api/session", headers={"Origin": ORIGIN})
            assert response.status_code == 200
            return response.cookies["hotel_guest"]

        first, second = guest(), guest()
        dates = {
            "room_id": room_ids["manor-suite"],
            "check_in": start.isoformat(),
            "check_out": (start + timedelta(days=2)).isoformat(),
            "guests": 2,
        }
        key = str(uuid4())
        body = {**dates, "request_id": key, "confirmed": True}

        def post(token, payload):
            return client.post(
                "/api/bookings",
                json=payload,
                headers={"Origin": ORIGIN, "Cookie": f"hotel_guest={token}"},
            )

        assert post(first, {**body, "confirmed": False}).status_code == 422
        assert post(first, {k: v for k, v in body.items() if k != "confirmed"}).status_code == 422
        assert (
            client.post(
                "/api/bookings", json=body, headers={"Cookie": f"hotel_guest={first}"}
            ).status_code
            == 403
        )
        assert post(first, {**body, "guests": 3}).status_code == 409
        assert post(first, {**body, "check_out": dates["check_in"]}).status_code == 422
        created = post(first, body)
        assert created.status_code == 201
        reference = created.json()["reference"]
        assert created.json()["demo"] is True
        assert post(first, body).status_code == 200
        assert post(first, body).json() == created.json()
        assert post(first, {**body, "guests": 1}).status_code == 409
        assert post(second, body).status_code == 409
        assert post(second, {**body, "request_id": str(uuid4())}).status_code == 409
        assert (
            client.get(
                f"/api/bookings/{reference}", headers={"Cookie": f"hotel_guest={first}"}
            ).status_code
            == 200
        )
        assert (
            client.get(
                f"/api/bookings/{reference}", headers={"Cookie": f"hotel_guest={second}"}
            ).status_code
            == 404
        )
        assert (
            client.get(
                f"/api/bookings/by-request/{key}", headers={"Cookie": f"hotel_guest={first}"}
            ).json()
            == created.json()
        )
        assert (
            client.get(
                f"/api/bookings/by-request/{key}", headers={"Cookie": f"hotel_guest={second}"}
            ).status_code
            == 404
        )
        client.cookies.clear()
        assert client.get(f"/api/bookings/{reference}").status_code == 401
        assert created.headers["cache-control"] == "no-store"

        async def after_booking():
            async with app.state.pool.connection() as conn:
                count = await (
                    await conn.execute(
                        "SELECT count(*) FROM demo_bookings WHERE request_id=%s", (key,)
                    )
                ).fetchone()
                assert count[0] == 1
            await load_inventory(app.state.pool, app.state.hotel)
            # Publishing the same fixture nights as a new version must not
            # reopen nights reserved under the earlier version.
            newer = json.loads(json.dumps(data))
            newer["version"] = 2
            (tmp_path / "data-v2.json").write_text(json.dumps(newer))
            catalogue_path = tmp_path / "catalogue.json"
            catalogue = json.loads(catalogue_path.read_text())
            catalogue["sources"].append({"source_id": source, "version": 2, "file": "data-v2.json"})
            catalogue["active_version"] = 2
            catalogue_path.write_text(json.dumps(catalogue))
            app.state.hotel.reload()
            await load_inventory(app.state.pool, app.state.hotel)

        client.portal.call(after_booking)
        unavailable = client.get(
            "/api/availability",
            params={
                "check_in": dates["check_in"],
                "check_out": dates["check_out"],
                "guests": 2,
            },
        ).json()
        assert room_ids["manor-suite"] not in {room["id"] for room in unavailable["rooms"]}
        assert (
            post(
                second,
                {
                    **body,
                    "request_id": str(uuid4()),
                    "check_in": (start + timedelta(days=1)).isoformat(),
                    "check_out": (start + timedelta(days=3)).isoformat(),
                },
            ).status_code
            == 409
        )

        async def competing():
            store = BookingStore(app.state.pool, app.state.hotel)
            same_nights = {
                "room_id": room_ids["garden-room"],
                "check_in": start.isoformat(),
                "check_out": (start + timedelta(days=2)).isoformat(),
                "guests": 2,
                "confirmed": True,
            }
            calls = [
                store.confirm(token, BookingInput(**same_nights, request_id=uuid4()))
                for token in (first, second)
            ]
            results = await asyncio.gather(*calls, return_exceptions=True)
            assert sum(isinstance(item, tuple) for item in results) == 1
            assert (
                sum(isinstance(item, HTTPException) and item.status_code == 409 for item in results)
                == 1
            )
            async with app.state.pool.connection() as conn:
                row = await (
                    await conn.execute(
                        "SELECT count(*) FROM demo_bookings WHERE room_id=%s "
                        "AND check_in=%s AND check_out=%s",
                        (room_ids["garden-room"], start, start + timedelta(days=2)),
                    )
                ).fetchone()
                assert row[0] == 1

            retry_body = BookingInput(
                room_id=room_ids["garden-room"],
                check_in=(start + timedelta(days=5)).isoformat(),
                check_out=(start + timedelta(days=7)).isoformat(),
                guests=2,
                confirmed=True,
                request_id=uuid4(),
            )
            repeated = await asyncio.gather(
                store.confirm(first, retry_body), store.confirm(first, retry_body)
            )
            assert repeated[0][0] == repeated[1][0]
            assert {item[1] for item in repeated} == {True, False}

        client.portal.call(competing)
