import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

import psycopg
from fastapi import FastAPI, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from psycopg_pool import PoolTimeout

from backend.app.bookings import booking_routes
from backend.app.chat import guest_routes, stub_reply
from backend.app.db import create_pool
from backend.app.hotel import HotelDataError, HotelStore
from backend.app.inventory import Availability
from backend.app.settings import ROOT, Settings


def create_app(settings: Settings | None = None, *, hotel_directory: Path | None = None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.hotel = HotelStore(
            hotel_directory or ROOT / "hotel",
            expected_hotel=(settings.hotel_name, settings.hotel_language, settings.hotel_timezone),
        )
        try:
            app.state.hotel.reload()
        except HotelDataError:
            logging.warning("Hotel data is unavailable; run python -m backend.app.hotel")
        async with create_pool(settings.database_url) as pool:
            app.state.pool = pool
            yield

    app = FastAPI(title="Smart Hotels", lifespan=lifespan)

    app.state.reply = stub_reply
    app.include_router(guest_routes(settings))
    app.include_router(booking_routes(settings))

    @app.middleware("http")
    async def private_cache(request: Request, call_next):
        response = await call_next(request)
        if request.url.path in {
            "/api/session",
            "/api/history",
            "/api/conversation",
            "/api/chat",
        } or request.url.path.startswith("/api/bookings"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(psycopg.Error)
    @app.exception_handler(PoolTimeout)
    async def database_error(request, exc):
        return JSONResponse(
            {"detail": "Chat storage unavailable. Try again shortly."}, status_code=503
        )

    @app.get("/api/health")
    async def health():
        try:
            async with asyncio.timeout(5):
                async with app.state.pool.connection() as conn:
                    await conn.execute("SELECT 1")
                    # Readiness also requires saved answer sources.
                    row = await (
                        await conn.execute(
                            "SELECT 1 FROM schema_migrations WHERE name = '003_answer_sources.sql'"
                        )
                    ).fetchone()
                    if row is None:
                        raise RuntimeError("Migrations required")
        except Exception:
            return JSONResponse(
                {"status": "unavailable", "database": "unavailable"}, status_code=503
            )
        return {"status": "ok", "database": "ok"}

    @app.get("/api/availability")
    async def availability(check_in: str, check_out: str, guests: int):
        result = await Availability(app.state.pool, app.state.hotel).search(
            check_in, check_out, guests
        )
        code = {"invalid_input": 422, "unavailable": 503}.get(result["status"], 200)
        return JSONResponse(result, status_code=code, headers={"Cache-Control": "no-store"})

    @app.get("/api/site")
    async def site():
        return {
            "name": settings.hotel_name,
            "language": settings.hotel_language,
            "timezone": settings.hotel_timezone,
            "demo": True,
            "assistant_mode": settings.assistant_mode,
        }

    def hotel_response(result):
        codes = {
            "ok": 200,
            "unknown": 200,
            "not_found": 404,
            "invalid_input": 422,
            "unavailable": 503,
        }
        return JSONResponse(result, status_code=codes[result["status"]])

    @app.get("/api/hotel/catalogue")
    async def hotel_catalogue():
        return hotel_response(app.state.hotel.catalogue())

    @app.get("/api/hotel/{section}")
    @app.get("/api/hotel/{section}/{item_id}")
    async def hotel_information(
        section: Literal["rooms", "amenities", "policies", "inventory"],
        item_id: str | None = None,
        source_id: str | None = None,
        version: int | None = Query(default=None, ge=1),
    ):
        return hotel_response(
            app.state.hotel.read(section, item_id, source_id=source_id, version=version)
        )

    @app.get("/", include_in_schema=False)
    async def index():
        return FileResponse(ROOT / "frontend" / "index.html")

    @app.get("/rooms/{room_id}", include_in_schema=False)
    @app.get("/review", include_in_schema=False)
    async def guest_page(room_id: str | None = None):
        return FileResponse(ROOT / "frontend" / "index.html")

    app.mount("/assets", StaticFiles(directory=ROOT / "frontend" / "assets"), name="assets")
    return app


app = create_app()
