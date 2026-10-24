ALTER TABLE turns ADD COLUMN sources jsonb NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE turns ADD CONSTRAINT sources_array CHECK (jsonb_typeof(sources) = 'array');
