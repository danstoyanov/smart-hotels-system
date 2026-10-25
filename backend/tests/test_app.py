from contextlib import asynccontextmanager

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.app.main import create_app
from backend.app.runtime import new_loop
from backend.app.settings import Settings


class Cursor:
    async def fetchone(self):
        return (1,)


class Connection:
    async def execute(self, query):
        assert query.startswith("SELECT")
        return Cursor()


class Pool:
    def __init__(self, fail=False):
        self.fail = fail

    @asynccontextmanager
    async def connection(self):
        if self.fail:
            raise OSError("secret database details")
        yield Connection()


def test_pages_and_public_configuration():
    app = create_app(Settings(_env_file=None, hotel_name="Example <Hotel>"))
    with TestClient(app, backend_options={"loop_factory": new_loop}) as client:
        assert client.get("/").status_code == 200
        assert client.get("/assets/site.js").status_code == 200
        assert client.get("/api/missing").status_code == 404
        assert client.get("/.env").status_code == 404
        site = client.get("/api/site").json()
        assert site == {
            "name": "Example <Hotel>",
            "language": "en",
            "timezone": "Europe/Kyiv",
            "demo": True,
            "assistant_mode": "stub",
        }
        assert "database_url" not in site


@pytest.mark.parametrize("path", ["/api/chat", "/api/bookings", "/api/session"])
def test_large_post_body_is_rejected_before_route(path):
    app = create_app(Settings(_env_file=None))
    with TestClient(app, backend_options={"loop_factory": new_loop}) as client:
        response = client.post(path, content=b"x" * 16385)
        assert response.status_code == 413
        assert response.json() == {"detail": "Request body is too large."}


@pytest.mark.parametrize("fail,code", [(False, 200), (True, 503)])
def test_health_checks_database_and_hides_errors(fail, code):
    app = create_app(Settings(_env_file=None))
    with TestClient(app, backend_options={"loop_factory": new_loop}) as client:
        app.state.pool = Pool(fail)
        response = client.get("/api/health")
        assert response.status_code == code
        assert "secret" not in response.text
        assert response.json()["database"] == ("unavailable" if fail else "ok")


def test_invalid_timezone_is_rejected():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, hotel_timezone="Invalid/Place")


def test_cloud_demo_rejects_stub_or_insecure_origin():
    with pytest.raises(ValidationError, match="Cloud demo requires"):
        Settings(_env_file=None, cloud_demo=True)
    with pytest.raises(ValidationError, match="Cloud demo requires"):
        Settings(
            _env_file=None,
            cloud_demo=True,
            assistant_mode="vertex",
            google_cloud_project="demo-project",
            google_cloud_location="global",
            app_origin="http://example.com",
            cookie_secure=True,
        )
    settings = Settings(
        _env_file=None,
        cloud_demo=True,
        assistant_mode="vertex",
        google_cloud_project="demo-project",
        google_cloud_location="global",
        app_origin="https://example.com",
        cookie_secure=True,
    )
    assert settings.cloud_demo


def test_windows_loop_uses_selector():
    import asyncio
    import sys

    loop = new_loop()
    try:
        if sys.platform == "win32":
            assert isinstance(loop, asyncio.SelectorEventLoop)
    finally:
        loop.close()
