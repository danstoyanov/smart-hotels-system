import asyncio
import hashlib
from pathlib import Path

import psycopg
from psycopg_pool import AsyncConnectionPool

from backend.app.runtime import new_loop
from backend.app.settings import Settings

MIGRATIONS = Path(__file__).resolve().parents[1] / "migrations"


def create_pool(database_url: str) -> AsyncConnectionPool:
    return AsyncConnectionPool(
        database_url,
        min_size=0,
        max_size=5,
        timeout=3,
        open=False,
        kwargs={"connect_timeout": 3, "options": "-c statement_timeout=5000"},
    )


async def migrate(database_url: str, directory: Path = MIGRATIONS) -> list[str]:
    """Apply ordered SQL files atomically; reject edits to applied files."""
    applied = []
    async with await psycopg.AsyncConnection.connect(database_url, connect_timeout=5) as conn:
        async with conn.transaction():
            await conn.execute("SELECT pg_advisory_xact_lock(59002)")
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations ("
                "name text PRIMARY KEY, checksum text NOT NULL, "
                "applied_at timestamptz NOT NULL DEFAULT now())"
            )
            rows = await (
                await conn.execute("SELECT name, checksum FROM schema_migrations")
            ).fetchall()
            known = dict(rows)
            paths = sorted(directory.glob("[0-9]*.sql"))
            if set(known) - {path.name for path in paths}:
                raise RuntimeError("An applied migration file is missing")
            for path in paths:
                sql = path.read_text(encoding="utf-8")
                checksum = hashlib.sha256(sql.encode()).hexdigest()
                if path.name in known:
                    if known[path.name] != checksum:
                        raise RuntimeError(f"Applied migration changed: {path.name}")
                    continue
                await conn.execute(sql)
                await conn.execute(
                    "INSERT INTO schema_migrations (name, checksum) VALUES (%s, %s)",
                    (path.name, checksum),
                )
                applied.append(path.name)
    return applied


async def main() -> None:
    try:
        applied = await migrate(Settings().database_url)
    except (psycopg.Error, RuntimeError):
        raise SystemExit("Migration failed. Check the database and migration files.") from None
    print("Applied: " + ", ".join(applied) if applied else "Database is up to date.")


if __name__ == "__main__":
    asyncio.run(main(), loop_factory=new_loop)
