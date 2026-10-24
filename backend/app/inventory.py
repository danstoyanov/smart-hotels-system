"""Read-only whole-stay search and explicit, atomic demo fixture loading."""

import asyncio
import re
from datetime import date, datetime
from zoneinfo import ZoneInfo

import psycopg
from psycopg.types.json import Jsonb
from psycopg_pool import PoolTimeout

from backend.app.db import create_pool
from backend.app.hotel import HotelStore
from backend.app.runtime import new_loop
from backend.app.settings import Settings


def validate_stay(check_in, check_out, guests, timezone, *, now=None):
    if type(guests) is not int or not 1 <= guests <= 20:
        raise ValueError("Guests must be a total from 1 to 20, including children and infants.")
    if any(
        not isinstance(day, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day)
        for day in (check_in, check_out)
    ):
        raise ValueError("Use exact dates in YYYY-MM-DD format.")
    try:
        arrival, departure = date.fromisoformat(check_in), date.fromisoformat(check_out)
    except ValueError:
        raise ValueError("Use valid calendar dates.") from None
    today = (now or datetime.now(ZoneInfo(timezone))).astimezone(ZoneInfo(timezone)).date()
    if arrival < today or departure <= arrival or (departure - arrival).days > 366:
        raise ValueError(
            "Check-in must be today or later; checkout must be later, within 366 nights."
        )
    return arrival, departure


async def load_inventory(pool, hotel):
    """Load a validated active revision once. Reject changes under the same version."""
    active = hotel.catalogue().get("active")
    if not active:
        raise ValueError("Hotel data is not loaded")
    rooms = hotel.read("rooms", **active)
    nights = hotel.read("inventory", **active)
    snapshot = {"hotel": rooms["hotel"], "rooms": rooms["data"], "inventory": nights["data"]}
    key = (active["source_id"], active["version"])
    async with pool.connection() as conn, conn.transaction():
        await conn.execute("SELECT pg_advisory_xact_lock(59063)")
        old = await (
            await conn.execute(
                "SELECT snapshot FROM inventory_sources WHERE source_id=%s AND version=%s", key
            )
        ).fetchone()
        if old:
            if old[0] != snapshot:
                raise ValueError("Inventory revision changed; publish a new hotel version")
            return
        await conn.execute(
            "INSERT INTO inventory_sources VALUES (%s,%s,%s,%s)",
            (*key, rooms["hotel"]["timezone"], Jsonb(snapshot)),
        )
        for room in rooms["data"]:
            await conn.execute(
                "INSERT INTO inventory_rooms VALUES (%s,%s,%s,%s,%s)",
                (*key, room["id"], room["capacity"], Jsonb(room)),
            )
        for night in nights["data"]:
            await conn.execute(
                "INSERT INTO inventory_nights VALUES (%s,%s,%s,%s,%s)",
                (*key, night["room_id"], night["night"], night["open"]),
            )


class Availability:
    def __init__(self, pool, hotel):
        self.pool = pool
        active = hotel.catalogue().get("active")
        self.source = active
        self.timezone = hotel.read("rooms", **active)["hotel"]["timezone"] if active else None

    async def search(self, check_in: str, check_out: str, guests: int) -> dict:
        if not self.source:
            return {"status": "unavailable", "message": "Hotel data is not loaded."}
        try:
            arrival, departure = validate_stay(check_in, check_out, guests, self.timezone)
        except ValueError as exc:
            return {"status": "invalid_input", "message": str(exc)}
        try:
            async with self.pool.connection() as conn:
                rows = await (
                    await conn.execute(
                        "SELECT * FROM search_inventory(%s,%s,%s,%s,%s)",
                        (
                            self.source["source_id"],
                            self.source["version"],
                            arrival,
                            departure,
                            guests,
                        ),
                    )
                ).fetchall()
        except psycopg.errors.InvalidParameterValue:
            return {"status": "invalid_input", "message": "Invalid stay dates or guest count."}
        except (psycopg.Error, PoolTimeout):
            return {
                "status": "unavailable",
                "message": "Availability is unavailable. Try again later.",
            }
        available = [room for room, status in rows if status == "available"]
        unknown = [room["id"] for room, status in rows if status == "unknown"]
        return {
            "status": "ok" if available else "unknown_inventory" if unknown else "no_match",
            "demo": True,
            "source": {**self.source, "demo": True},
            "check_in": check_in,
            "check_out": check_out,
            "guests": guests,
            "nights": (departure - arrival).days,
            "timezone": self.timezone,
            "rooms": available,
            "unknown_room_ids": unknown,
            "message": "Fictional demo inventory. Search does not reserve or hold a room.",
        }


async def main():
    settings = Settings()
    hotel = HotelStore(
        expected_hotel=(settings.hotel_name, settings.hotel_language, settings.hotel_timezone)
    )
    hotel.reload()
    async with create_pool(settings.database_url) as pool:
        await load_inventory(pool, hotel)
    print("Demo inventory is loaded.")


if __name__ == "__main__":
    asyncio.run(main(), loop_factory=new_loop)
