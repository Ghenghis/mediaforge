-- Add character_type column to actors table for detailed filtering
ALTER TABLE actors ADD COLUMN character_type text;

-- Create index for better filtering performance
CREATE INDEX idx_actors_character_type ON actors(character_type);

-- Update existing actors to have a default character type
UPDATE actors SET character_type = 'professional' WHERE character_type IS NULL;