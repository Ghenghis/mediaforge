-- Import actors from CSV using staging table approach

-- Create staging table with all columns as TEXT
CREATE TEMPORARY TABLE actors_staging (
    id TEXT,
    first_name TEXT,
    middle_name TEXT,
    last_name TEXT,
    full_name TEXT,
    role TEXT,
    era TEXT,
    bio TEXT,
    voice_id TEXT,
    voice_provider TEXT,
    voice_settings TEXT,
    tags TEXT,
    image_url TEXT,
    metadata TEXT,
    created_at TEXT,
    updated_at TEXT,
    character_type TEXT
);

-- Import CSV data into staging table
\copy actors_staging FROM '/tmp/actors.csv' WITH DELIMITER ';' CSV HEADER;

-- Insert into main actors table (skip generated full_name column)
INSERT INTO public.actors (
    id, first_name, middle_name, last_name, role, era, bio, 
    voice_id, voice_provider, voice_settings, tags, image_url, 
    metadata, created_at, updated_at, character_type
)
SELECT 
    id::uuid, first_name, middle_name, last_name, role, era, bio,
    voice_id, voice_provider, voice_settings::jsonb, tags::jsonb,
    image_url, metadata::jsonb, created_at::timestamptz, 
    updated_at::timestamptz, character_type
FROM actors_staging;

-- Show results
SELECT COUNT(*) as imported_actors FROM public.actors;

-- Clean up
DROP TABLE actors_staging;
