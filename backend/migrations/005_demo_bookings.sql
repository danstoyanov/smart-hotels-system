CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE TABLE demo_bookings (
    id uuid PRIMARY KEY,
    request_id uuid NOT NULL UNIQUE,
    session_id uuid NOT NULL REFERENCES guest_sessions(id),
    reference text NOT NULL UNIQUE CHECK (reference ~ '^DEM-[A-Z0-9]{12}$'),
    room_id text NOT NULL,
    source_id text NOT NULL,
    version integer NOT NULL,
    check_in date NOT NULL,
    check_out date NOT NULL,
    guests integer NOT NULL CHECK (guests BETWEEN 1 AND 20),
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    FOREIGN KEY (source_id, version, room_id)
        REFERENCES inventory_rooms(source_id, version, room_id),
    CHECK (check_out > check_in AND check_out - check_in <= 366),
    EXCLUDE USING gist (room_id WITH =, daterange(check_in, check_out, '[)') WITH &&)
);
CREATE INDEX demo_bookings_owner ON demo_bookings(session_id, request_id);

CREATE OR REPLACE FUNCTION search_inventory(
    requested_source text, requested_version integer,
    arrival date, departure date, guests integer
) RETURNS TABLE (facts jsonb, availability text)
LANGUAGE plpgsql STABLE AS $$
DECLARE property_timezone text;
BEGIN
    SELECT timezone INTO property_timezone FROM inventory_sources
    WHERE source_id = requested_source AND version = requested_version;
    IF property_timezone IS NULL THEN
        RAISE EXCEPTION 'Inventory source is not loaded' USING ERRCODE = 'P0002';
    END IF;
    IF arrival IS NULL OR departure IS NULL OR guests IS NULL
       OR guests < 1 OR guests > 20
       OR arrival < (CURRENT_TIMESTAMP AT TIME ZONE property_timezone)::date
       OR departure <= arrival OR departure - arrival > 366 THEN
        RAISE EXCEPTION 'Invalid stay dates or guest count' USING ERRCODE = '22023';
    END IF;
    RETURN QUERY
    SELECT r.facts,
        CASE WHEN count(n.night) FILTER (WHERE NOT n.is_open) > 0
                       OR EXISTS (
                           SELECT 1 FROM demo_bookings b
                           WHERE b.room_id = r.room_id
                             AND b.check_in < departure AND b.check_out > arrival
                       ) THEN 'unavailable'
             WHEN count(n.night) <> departure - arrival THEN 'unknown'
             ELSE 'available' END
    FROM inventory_rooms r
    LEFT JOIN inventory_nights n
      ON (n.source_id, n.version, n.room_id) = (r.source_id, r.version, r.room_id)
      AND n.night >= arrival AND n.night < departure
    WHERE r.source_id = requested_source AND r.version = requested_version
      AND r.capacity >= guests
    GROUP BY r.room_id, r.facts
    ORDER BY r.room_id;
END;
$$;
