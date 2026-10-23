"""Private guest state. No connection stays open while the assistant runs."""

import hashlib
import re
import secrets
from uuid import UUID, uuid4

from fastapi import HTTPException

COOKIE = "hotel_guest"
SESSION_SECONDS = 86400
LEASE_SECONDS = 120


def token_hash(token: str | None) -> str:
    if token is None or not re.fullmatch(r"[A-Za-z0-9_-]{43}", token):
        raise HTTPException(401, "Session expired. Start a new session.")
    return hashlib.sha256(token.encode()).hexdigest()


class GuestStore:
    def __init__(self, pool):
        self.pool = pool

    async def owned(self, conn, token, *, lock=False):
        row = await (
            await conn.execute(
                "SELECT id, conversation_id, active_turn, "
                "busy_until > clock_timestamp() FROM guest_sessions "
                "WHERE token_hash = %s AND expires_at > clock_timestamp()"
                + (" FOR UPDATE" if lock else ""),
                (token_hash(token),),
            )
        ).fetchone()
        if row is None:
            raise HTTPException(401, "Session expired. Start a new session.")
        return row

    async def session(self, token):
        async with self.pool.connection() as conn:
            if token:
                try:
                    row = await self.owned(conn, token)
                    return None, row[1]
                except HTTPException as exc:
                    if exc.status_code != 401:
                        raise
            token = secrets.token_urlsafe(32)
            conversation = uuid4()
            await conn.execute(
                "INSERT INTO guest_sessions (id, token_hash, expires_at, conversation_id) "
                "VALUES (%s, %s, clock_timestamp() + interval '24 hours', %s)",
                (uuid4(), token_hash(token), conversation),
            )
            return token, conversation

    async def history(self, token):
        async with self.pool.connection() as conn:
            session, conversation, _, _ = await self.owned(conn, token)
            rows = await (
                await conn.execute(
                    "SELECT id, question, answer FROM turns "
                    "WHERE session_id = %s AND conversation_id = %s AND status = 'completed' "
                    "ORDER BY created_at DESC, id DESC LIMIT 20",
                    (session, conversation),
                )
            ).fetchall()
            return {
                "conversation_id": str(conversation),
                "turns": [
                    {"turn_id": str(row[0]), "question": row[1], "answer": row[2]}
                    for row in reversed(rows)
                ],
            }

    async def clear_stale(self, conn, row):
        if row[2] and not row[3]:
            await conn.execute(
                "UPDATE turns SET status = 'interrupted' WHERE id = %s "
                "AND session_id = %s AND status = 'running'",
                (row[2], row[0]),
            )

    async def reset(self, token):
        async with self.pool.connection() as conn:
            row = await self.owned(conn, token, lock=True)
            if row[2] and row[3]:
                raise HTTPException(409, "A reply is still running. Stop it and try again shortly.")
            await self.clear_stale(conn, row)
            conversation = uuid4()
            await conn.execute(
                "UPDATE guest_sessions SET conversation_id = %s, active_turn = NULL, "
                "busy_until = NULL WHERE id = %s",
                (conversation, row[0]),
            )
            return {"conversation_id": str(conversation)}

    async def admit(self, token, turn_id: UUID, message: str):
        async with self.pool.connection() as conn:
            row = await self.owned(conn, token, lock=True)
            if row[2] and row[3]:
                raise HTTPException(409, "A reply is still running. Try again shortly.")
            await self.clear_stale(conn, row)
            inserted = await (
                await conn.execute(
                    "INSERT INTO turns (id, session_id, conversation_id, question, status) "
                    "VALUES (%s, %s, %s, %s, 'running') ON CONFLICT (id) DO NOTHING RETURNING id",
                    (turn_id, row[0], row[1], message),
                )
            ).fetchone()
            if inserted is None:
                raise HTTPException(
                    409, "Turn ID unavailable. Reload history before sending again."
                )
            await conn.execute(
                "UPDATE guest_sessions SET active_turn = %s, "
                "busy_until = clock_timestamp() + interval '120 seconds' WHERE id = %s",
                (turn_id, row[0]),
            )
            return row[0], row[1]

    async def complete(self, session, conversation, turn_id, answer):
        async with self.pool.connection() as conn:
            row = await (
                await conn.execute(
                    "SELECT id FROM guest_sessions WHERE id = %s AND conversation_id = %s "
                    "AND active_turn = %s AND expires_at > clock_timestamp() "
                    "AND busy_until > clock_timestamp() FOR UPDATE",
                    (session, conversation, turn_id),
                )
            ).fetchone()
            if row is None:
                raise RuntimeError("Turn no longer active")
            await conn.execute(
                "UPDATE turns SET status = 'completed', answer = %s, "
                "completed_at = clock_timestamp() WHERE id = %s AND session_id = %s "
                "AND status = 'running'",
                (answer, turn_id, session),
            )
            await conn.execute(
                "UPDATE guest_sessions SET active_turn = NULL, busy_until = NULL WHERE id = %s",
                (session,),
            )

    async def interrupt(self, session, turn_id):
        async with self.pool.connection() as conn:
            # Use the same lock order as admission and completion.
            await conn.execute("SELECT id FROM guest_sessions WHERE id = %s FOR UPDATE", (session,))
            await conn.execute(
                "UPDATE turns SET status = 'interrupted' WHERE id = %s "
                "AND session_id = %s AND status = 'running'",
                (turn_id, session),
            )
            await conn.execute(
                "UPDATE guest_sessions SET active_turn = NULL, busy_until = NULL "
                "WHERE id = %s AND active_turn = %s",
                (session, turn_id),
            )
