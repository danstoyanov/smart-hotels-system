CREATE TABLE guest_sessions (
    id uuid PRIMARY KEY,
    token_hash text NOT NULL UNIQUE,
    expires_at timestamptz NOT NULL,
    conversation_id uuid NOT NULL,
    active_turn uuid,
    busy_until timestamptz
);
CREATE TABLE turns (
    id uuid PRIMARY KEY,
    session_id uuid NOT NULL REFERENCES guest_sessions(id) ON DELETE CASCADE,
    conversation_id uuid NOT NULL,
    question text NOT NULL CHECK (length(question) BETWEEN 1 AND 2000),
    status text NOT NULL CHECK (status IN ('running', 'completed', 'interrupted')),
    answer text,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    completed_at timestamptz,
    CHECK ((status = 'completed') = (answer IS NOT NULL))
);
CREATE INDEX turns_history ON turns(session_id, conversation_id, created_at)
    WHERE status = 'completed';
