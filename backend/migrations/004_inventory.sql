CREATE TABLE inventory_sources (
    source_id text NOT NULL,
    version integer NOT NULL CHECK (version > 0),
    timezone text NOT NULL,
    snapshot jsonb NOT NULL,
    PRIMARY KEY (source_id, version)
);
CREATE TABLE inventory_rooms (
    source_id text NOT NULL,
    version integer NOT NULL,
    room_id text NOT NULL,
    capacity integer NOT NULL CHECK (capacity BETWEEN 1 AND 20),
    facts jsonb NOT NULL,
    PRIMARY KEY (source_id, version, room_id),
    FOREIGN KEY (source_id, version) REFERENCES inventory_sources,
    CHECK (facts->>'id' = room_id),
    CHECK ((facts->>'capacity')::integer = capacity)
);
CREATE TABLE inventory_nights (
    source_id text NOT NULL,
    version integer NOT NULL,
    room_id text NOT NULL,
    night date NOT NULL,
    is_open boolean NOT NULL,
    PRIMARY KEY (source_id, version, room_id, night),
    FOREIGN KEY (source_id, version, room_id) REFERENCES inventory_rooms
);

CREATE FUNCTION search_inventory(
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
        CASE WHEN count(n.night) FILTER (WHERE NOT n.is_open) > 0 THEN 'unavailable'
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
