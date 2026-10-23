import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.app.db import create_pool
from backend.app.settings import ROOT, Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        async with create_pool(settings.database_url) as pool:
            app.state.pool = pool
            yield

    app = FastAPI(title="Smart Hotels", lifespan=lifespan)

    @app.get("/api/health")
    async def health():
        try:
            async with asyncio.timeout(5):
                async with app.state.pool.connection() as conn:
                    await conn.execute("SELECT 1")
                    # Readiness also requires the initial migration.
                    row = await (
                        await conn.execute(
                            "SELECT 1 FROM schema_migrations WHERE name = '001_foundation.sql'"
                        )
                    ).fetchone()
                    if row is None:
                        raise RuntimeError("Migrations required")
        except Exception:
            return JSONResponse(
                {"status": "unavailable", "database": "unavailable"}, status_code=503
            )
        return {"status": "ok", "database": "ok"}

    @app.get("/api/site")
    async def site():
        return {
            "name": settings.hotel_name,
            "language": settings.hotel_language,
            "timezone": settings.hotel_timezone,
            "demo": True,
        }

    @app.get("/", include_in_schema=False)
    async def index():
        return FileResponse(ROOT / "frontend" / "index.html")

    app.mount("/assets", StaticFiles(directory=ROOT / "frontend" / "assets"), name="assets")
    return app


app = create_app()
