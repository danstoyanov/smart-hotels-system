"""Explicit, owned demo reservations with database-backed retry safety."""

import secrets
from uuid import UUID, uuid4

import psycopg
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt

from backend.app.inventory import validate_stay
from backend.app.sessions import COOKIE, GuestStore


class BookingInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: UUID
    room_id: str = Field(min_length=1, max_length=80, pattern=r"^[a-z0-9-]+$")
    check_in: str
    check_out: str
    guests: StrictInt
    confirmed: StrictBool


def booking_result(row):
    return {
        "demo": True,
        "reference": row[0],
        "room_id": row[1],
        "check_in": row[2].isoformat(),
        "check_out": row[3].isoformat(),
        "guests": row[4],
        "message": "Demo reservation only. This is not a real hotel booking.",
    }


class BookingStore:
    def __init__(self, pool, hotel):
        self.pool = pool
        self.hotel = hotel

    async def confirm(self, token, body: BookingInput):
        if body.confirmed is not True:
            raise HTTPException(422, "Explicit confirmation is required.")
        try:
            async with self.pool.connection() as conn, conn.transaction():
                session, _, _, _ = await GuestStore(self.pool).owned(conn, token)
                # Request locks serialize lost-response retries, including from two workers.
                await conn.execute(
                    "SELECT pg_advisory_xact_lock(hashtextextended(%s, 65001))",
                    (str(body.request_id),),
                )
                prior = await (
                    await conn.execute(
                        "SELECT reference, room_id, check_in, check_out, guests, session_id "
                        "FROM demo_bookings WHERE request_id = %s",
                        (body.request_id,),
                    )
                ).fetchone()
                if prior:
                    if prior[5] != session or (
                        prior[1],
                        prior[2].isoformat(),
                        prior[3].isoformat(),
                        prior[4],
                    ) != (
                        body.room_id,
                        body.check_in,
                        body.check_out,
                        body.guests,
                    ):
                        raise HTTPException(409, "Reservation request ID is already used.")
                    return booking_result(prior), False

                active = self.hotel.catalogue().get("active")
                if not active:
                    raise HTTPException(503, "Demo inventory is unavailable.")
                timezone = self.hotel.read("rooms", **active)["hotel"]["timezone"]
                try:
                    arrival, departure = validate_stay(
                        body.check_in, body.check_out, body.guests, timezone
                    )
                except ValueError as exc:
                    raise HTTPException(422, str(exc)) from None
                # Use a room lock across source revisions, then recheck all facts in
                # this transaction. The exclusion constraint is a final database guard.
                await conn.execute(
                    "SELECT pg_advisory_xact_lock(hashtextextended(%s, 65002))",
                    (body.room_id,),
                )
                room = await (
                    await conn.execute(
                        "SELECT capacity FROM inventory_rooms WHERE source_id=%s "
                        "AND version=%s AND room_id=%s",
                        (active["source_id"], active["version"], body.room_id),
                    )
                ).fetchone()
                if not room or room[0] < body.guests:
                    raise HTTPException(409, "This room cannot fit the selected guest count.")
                available = await (
                    await conn.execute(
                        "SELECT availability FROM search_inventory(%s,%s,%s,%s,%s) "
                        "WHERE facts->>'id'=%s",
                        (
                            active["source_id"],
                            active["version"],
                            arrival,
                            departure,
                            body.guests,
                            body.room_id,
                        ),
                    )
                ).fetchone()
                if not available or available[0] != "available":
                    raise HTTPException(409, "This room is no longer available for the full stay.")
                reference = "DEM-" + secrets.token_hex(6).upper()
                row = await (
                    await conn.execute(
                        "INSERT INTO demo_bookings "
                        "(id, request_id, session_id, reference, room_id, source_id, "
                        "version, check_in, check_out, guests) "
                        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                        "RETURNING reference, room_id, check_in, check_out, guests",
                        (
                            uuid4(),
                            body.request_id,
                            session,
                            reference,
                            body.room_id,
                            active["source_id"],
                            active["version"],
                            arrival,
                            departure,
                            body.guests,
                        ),
                    )
                ).fetchone()
                return booking_result(row), True
        except psycopg.errors.ExclusionViolation:
            raise HTTPException(
                409, "This room is no longer available for the full stay."
            ) from None

    async def find(self, token, *, reference=None, request_id=None):
        async with self.pool.connection() as conn:
            session, _, _, _ = await GuestStore(self.pool).owned(conn, token)
            column, value = (
                ("reference", reference) if reference is not None else ("request_id", request_id)
            )
            row = await (
                await conn.execute(
                    "SELECT reference, room_id, check_in, check_out, guests "
                    f"FROM demo_bookings WHERE session_id=%s AND {column}=%s",
                    (session, value),
                )
            ).fetchone()
            if row is None:
                raise HTTPException(404, "Demo reservation not found.")
            return booking_result(row)


def booking_routes(settings):
    router = APIRouter()

    def store(request):
        return BookingStore(request.app.state.pool, request.app.state.hotel)

    @router.post("/api/bookings")
    async def confirm(request: Request, body: BookingInput):
        if request.headers.get("origin") != settings.app_origin:
            raise HTTPException(403, "Open the reservation page from the hotel website.")
        result, created = await store(request).confirm(request.cookies.get(COOKIE), body)
        return JSONResponse(result, status_code=201 if created else 200)

    @router.get("/api/bookings/by-request/{request_id}")
    async def by_request(request: Request, request_id: UUID):
        return await store(request).find(request.cookies.get(COOKIE), request_id=request_id)

    @router.get("/api/bookings/{reference}")
    async def by_reference(request: Request, reference: str):
        return await store(request).find(request.cookies.get(COOKIE), reference=reference)

    return router
