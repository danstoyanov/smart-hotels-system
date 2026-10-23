import asyncio

import psycopg
import pytest
from fastapi.testclient import TestClient

from backend.app.db import migrate
from backend.app.main import create_app
from backend.app.runtime import new_loop
from backend.app.settings import Settings


def test_migrations_repeat_health_and_rollback(database_url, tmp_path):
    async def exercise():
        await migrate(database_url)
        assert await migrate(database_url) == []
        async with await psycopg.AsyncConnection.connect(database_url) as conn:
            rows = await (await conn.execute("SELECT name FROM schema_migrations")).fetchall()
            assert set(rows) == {("001_foundation.sql",), ("002_guest_sessions.sql",)}

        # Include the original file, then test a failed new migration transaction.
        from backend.app.db import MIGRATIONS

        original = (MIGRATIONS / "001_foundation.sql").read_text()
        for path in MIGRATIONS.glob("*.sql"):
            (tmp_path / path.name).write_text(path.read_text())
        bad = tmp_path / "003_failure.sql"
        bad.write_text("CREATE TABLE rollback_probe (id int); SELECT 1 / 0;")
        with pytest.raises(psycopg.errors.DivisionByZero):
            await migrate(database_url, tmp_path)
        async with await psycopg.AsyncConnection.connect(database_url) as conn:
            result = await (await conn.execute("SELECT to_regclass('rollback_probe')")).fetchone()
            assert result == (None,)
        bad.unlink()
        (tmp_path / "001_foundation.sql").write_text(original + "\n-- changed")
        with pytest.raises(RuntimeError, match="Applied migration changed"):
            await migrate(database_url, tmp_path)

    asyncio.run(exercise(), loop_factory=new_loop)
    app = create_app(Settings(_env_file=None, database_url=database_url))
    with TestClient(app, backend_options={"loop_factory": new_loop}) as client:
        assert client.get("/api/health").json() == {"status": "ok", "database": "ok"}


def test_real_database_failure_returns_503(database_url):
    # A refused local port verifies actual pool failure without changing the running DB.
    app = create_app(
        Settings(
            _env_file=None,
            database_url="postgresql://unused:unused@127.0.0.1:1/smart_hotels_test",
        )
    )
    with TestClient(app, backend_options={"loop_factory": new_loop}) as client:
        response = client.get("/api/health")
        assert response.status_code == 503
        assert response.json() == {"status": "unavailable", "database": "unavailable"}
