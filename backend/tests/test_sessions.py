import asyncio
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from starlette.requests import ClientDisconnect

from backend.app.chat import GuestStream, event
from backend.app.db import migrate
from backend.app.main import create_app
from backend.app.runtime import new_loop
from backend.app.sessions import COOKIE, GuestStore, token_hash
from backend.app.settings import Settings

ORIGIN = "http://testserver"


@pytest.fixture
def guest_client(database_url):
    asyncio.run(migrate(database_url), loop_factory=new_loop)
    app = create_app(Settings(_env_file=None, database_url=database_url, app_origin=ORIGIN))
    with TestClient(app, backend_options={"loop_factory": new_loop}) as client:
        yield client


def call(client, method, path, token=None, **kwargs):
    client.cookies.clear()
    headers = {"Origin": ORIGIN}
    if token:
        headers["Cookie"] = f"{COOKIE}={token}"
    return client.request(method, path, headers=headers, **kwargs)


def new_guest(client):
    response = call(client, "POST", "/api/session")
    assert response.status_code == 200
    return response.cookies[COOKIE]


def sql(client, query, params=()):
    async def run():
        async with client.app.state.pool.connection() as conn:
            cursor = await conn.execute(query, params)
            return await cursor.fetchall() if cursor.description else None

    return client.portal.call(run)


def test_cookie_origin_validation_and_no_cache(guest_client):
    client = guest_client
    client.cookies.clear()
    assert client.post("/api/session").status_code == 403
    assert client.post("/api/session", headers={"Origin": "https://other.test"}).status_code == 403
    token = new_guest(client)
    response = call(client, "POST", "/api/session", token)
    assert "set-cookie" not in response.headers
    assert response.headers["cache-control"] == "no-store"
    assert call(client, "GET", "/api/history").status_code == 401
    assert call(client, "GET", "/api/history", "invalid").status_code == 401
    assert (
        call(
            client, "POST", "/api/chat", token, json={"turn_id": str(uuid4()), "message": "   "}
        ).status_code
        == 422
    )
    assert (
        call(
            client,
            "POST",
            "/api/chat",
            token,
            json={"turn_id": str(uuid4()), "message": "x" * 2001},
        ).status_code
        == 422
    )
    assert (
        call(
            client, "POST", "/api/chat", token, json={"turn_id": "bad", "message": "hello"}
        ).status_code
        == 422
    )
    assert call(client, "POST", "/api/conversation").status_code == 401
    rows = sql(
        client, "SELECT token_hash FROM guest_sessions WHERE token_hash = %s", (token_hash(token),)
    )
    assert rows == [(token_hash(token),)]
    assert token != rows[0][0]


def test_secure_cookie_configuration():
    from unittest.mock import AsyncMock, patch

    app = create_app(Settings(_env_file=None, app_origin=ORIGIN, cookie_secure=True))
    with TestClient(app, backend_options={"loop_factory": new_loop}) as client:
        with patch.object(GuestStore, "session", AsyncMock(return_value=("a" * 43, uuid4()))):
            response = call(client, "POST", "/api/session")
    cookie = response.headers["set-cookie"].lower()
    for flag in ("httponly", "secure", "samesite=strict", "max-age=86400", "path=/"):
        assert flag in cookie
    assert "domain=" not in cookie


def test_history_ownership_reset_and_duplicates(guest_client):
    client = guest_client
    first, second = new_guest(client), new_guest(client)
    turn_id = str(uuid4())
    response = call(
        client,
        "POST",
        "/api/chat",
        first,
        json={"turn_id": turn_id, "message": "<script>private</script>"},
    )
    assert response.status_code == 200
    assert response.text.index("event: result") < response.text.index("event: done")
    assert response.headers["cache-control"] == "no-store"
    own = call(client, "GET", "/api/history", first).json()
    assert own["turns"][0]["question"] == "<script>private</script>"
    assert own["turns"][0]["answer"].startswith("This is a demo reply.")
    assert call(client, "GET", "/api/history", second).json()["turns"] == []
    assert (
        call(
            client, "POST", "/api/chat", second, json={"turn_id": turn_id, "message": "steal"}
        ).status_code
        == 409
    )
    assert (
        call(
            client, "POST", "/api/chat", first, json={"turn_id": turn_id, "message": "repeat"}
        ).status_code
        == 409
    )
    call(client, "POST", "/api/conversation", second).raise_for_status()
    assert call(client, "GET", "/api/history", first).json() == own
    reset = call(client, "POST", "/api/conversation", first).json()
    assert reset["conversation_id"] != own["conversation_id"]
    assert call(client, "GET", "/api/history", first).json()["turns"] == []
    assert call(client, "GET", "/api/history", second).json()["turns"] == []


def test_expiry_and_replacement(guest_client):
    client = guest_client
    token = new_guest(client)
    sql(
        client,
        "UPDATE guest_sessions SET expires_at = clock_timestamp() - interval '1 second' "
        "WHERE token_hash = %s",
        (token_hash(token),),
    )
    assert call(client, "GET", "/api/history", token).status_code == 401
    assert call(client, "POST", "/api/conversation", token).status_code == 401
    assert (
        call(
            client, "POST", "/api/chat", token, json={"turn_id": str(uuid4()), "message": "hello"}
        ).status_code
        == 401
    )
    response = call(client, "POST", "/api/session", token)
    assert response.cookies[COOKIE] != token
    assert call(client, "GET", "/api/history", response.cookies[COOKIE]).json()["turns"] == []


@pytest.mark.parametrize("before_start", [True, False])
def test_disconnect_releases_busy_session(guest_client, before_start):
    client = guest_client
    token = new_guest(client)
    turn_id = uuid4()

    async def exercise():
        store = GuestStore(client.app.state.pool)
        session, _ = await store.admit(token, turn_id, "interrupted question")

        async def content():
            yield event("text", {"text": "provisional"})

        async def send(message):
            if before_start or message["type"] == "http.response.body":
                raise OSError("guest disconnected")

        async def receive():
            return {"type": "http.disconnect"}

        response = GuestStream(content(), store, session, turn_id)
        with pytest.raises((OSError, ClientDisconnect)):
            await response({"type": "http", "asgi": {"spec_version": "2.4"}}, receive, send)

    client.portal.call(exercise)
    assert sql(client, "SELECT status FROM turns WHERE id = %s", (turn_id,)) == [("interrupted",)]
    assert call(client, "GET", "/api/history", token).json()["turns"] == []
    assert (
        call(
            client,
            "POST",
            "/api/chat",
            token,
            json={"turn_id": str(uuid4()), "message": "try again"},
        ).status_code
        == 200
    )


def test_busy_lease_stale_worker_and_expiry_during_reply(guest_client):
    client = guest_client
    token = new_guest(client)
    store = GuestStore(client.app.state.pool)
    old_turn = uuid4()
    session, conversation = client.portal.call(store.admit, token, old_turn, "old")
    assert call(client, "POST", "/api/conversation", token).status_code == 409
    assert (
        call(
            client, "POST", "/api/chat", token, json={"turn_id": str(uuid4()), "message": "busy"}
        ).status_code
        == 409
    )
    sql(
        client,
        "UPDATE guest_sessions SET busy_until = clock_timestamp() - interval '1 second' "
        "WHERE id = %s",
        (session,),
    )
    next_turn = uuid4()
    client.portal.call(store.admit, token, next_turn, "new")
    with pytest.raises(RuntimeError, match="no longer active"):
        client.portal.call(store.complete, session, conversation, old_turn, "late reply")
    client.portal.call(store.interrupt, session, old_turn)
    assert sql(client, "SELECT active_turn FROM guest_sessions WHERE id = %s", (session,)) == [
        (next_turn,)
    ]
    sql(
        client,
        "UPDATE guest_sessions SET expires_at = clock_timestamp() - interval '1 second' "
        "WHERE id = %s",
        (session,),
    )
    with pytest.raises(RuntimeError, match="no longer active"):
        client.portal.call(store.complete, session, conversation, next_turn, "expired reply")
    client.portal.call(store.interrupt, session, next_turn)
    assert sql(client, "SELECT answer FROM turns WHERE id IN (%s, %s)", (old_turn, next_turn)) == [
        (None,),
        (None,),
    ]


def test_stub_failure_does_not_save_or_block(guest_client):
    client = guest_client
    token = new_guest(client)

    async def broken(message):
        yield "not final"
        raise RuntimeError("private error details")

    client.app.state.reply = broken
    response = call(
        client, "POST", "/api/chat", token, json={"turn_id": str(uuid4()), "message": "hello"}
    )
    assert "event: error" in response.text
    assert "event: done" not in response.text
    assert "private error" not in response.text
    assert call(client, "GET", "/api/history", token).json()["turns"] == []
    assert call(client, "POST", "/api/conversation", token).status_code == 200


def test_commit_precedes_result_and_model_holds_no_connection(guest_client):
    client = guest_client
    token = new_guest(client)
    turn_id = str(uuid4())

    async def checked_reply(message):
        assert client.app.state.pool.get_stats().get("pool_available", 0) > 0
        async with client.app.state.pool.connection() as conn:
            row = await (
                await conn.execute("SELECT status FROM turns WHERE id = %s", (turn_id,))
            ).fetchone()
            assert row == ("running",)
        yield "saved answer"

    client.app.state.reply = checked_reply
    response = call(
        client, "POST", "/api/chat", token, json={"turn_id": turn_id, "message": "hello"}
    )
    assert "event: result" in response.text
    assert sql(client, "SELECT status, answer FROM turns WHERE id = %s", (turn_id,)) == [
        ("completed", "saved answer")
    ]
    # A new HTTP client and application restore the same database history.
    app = create_app(
        Settings(_env_file=None, database_url=client.app.state.pool.conninfo, app_origin=ORIGIN)
    )
    with TestClient(app, backend_options={"loop_factory": new_loop}) as refreshed:
        assert (
            call(refreshed, "GET", "/api/history", token).json()["turns"][0]["answer"]
            == "saved answer"
        )


def test_concurrent_admission_allows_one_turn(guest_client):
    from fastapi import HTTPException

    client = guest_client
    token = new_guest(client)
    store = GuestStore(client.app.state.pool)

    async def race():
        return await asyncio.gather(
            store.admit(token, uuid4(), "first"),
            store.admit(token, uuid4(), "second"),
            return_exceptions=True,
        )

    results = client.portal.call(race)
    assert sum(isinstance(result, tuple) for result in results) == 1
    errors = [result for result in results if isinstance(result, HTTPException)]
    assert len(errors) == 1 and errors[0].status_code == 409


def test_failed_commit_never_reports_completion(guest_client):
    from unittest.mock import AsyncMock, patch

    client = guest_client
    token = new_guest(client)
    with patch.object(GuestStore, "complete", AsyncMock(side_effect=RuntimeError("commit failed"))):
        response = call(
            client, "POST", "/api/chat", token, json={"turn_id": str(uuid4()), "message": "hello"}
        )
    assert "event: error" in response.text
    assert "event: result" not in response.text
    assert "event: done" not in response.text
    assert call(client, "GET", "/api/history", token).json()["turns"] == []
    assert call(client, "POST", "/api/conversation", token).status_code == 200


def test_history_returns_latest_twenty_completed_turns(guest_client):
    client = guest_client
    token = new_guest(client)
    store = GuestStore(client.app.state.pool)

    async def fill_history():
        for number in range(22):
            turn = uuid4()
            session, conversation = await store.admit(token, turn, f"question {number}")
            await store.complete(session, conversation, turn, f"answer {number}")

    client.portal.call(fill_history)
    turns = call(client, "GET", "/api/history", token).json()["turns"]
    assert len(turns) == 20
    assert [turn["question"] for turn in turns] == [f"question {n}" for n in range(2, 22)]
