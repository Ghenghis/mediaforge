-- Add user_id to portrait_preset_reviews for tracking user reviews
ALTER TABLE portrait_preset_reviews ADD COLUMN user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE;

-- Create index for faster user review lookups
CREATE INDEX idx_portrait_preset_reviews_user_id ON portrait_preset_reviews(user_id);

-- Update RLS policies to allow users to update/delete their own reviews
DROP POLICY IF EXISTS "Authenticated users can update reviews" ON portrait_preset_reviews;
DROP POLICY IF EXISTS "Authenticated users can delete reviews" ON portrait_preset_reviews;

CREATE POLICY "Users can update their own reviews" 
ON portrait_preset_reviews 
FOR UPDATE 
USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own reviews" 
ON portrait_preset_reviews 
FOR DELETE 
USING (auth.uid() = user_id);

-- Create preset_versions table for version history
CREATE TABLE portrait_preset_versions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  preset_id uuid NOT NULL REFERENCES portrait_presets(id) ON DELETE CASCADE,
  version_number integer NOT NULL,
  name text NOT NULL,
  description text,
  coverage integer,
  fit text,
  style_profile text,
  accent_focus text,
  age integer,
  weathering integer,
  detail_level integer,
  clothing_formality integer,
  texture_detail integer,
  contrast integer,
  rating text,
  tags text[],
  created_at timestamptz DEFAULT now() NOT NULL,
  change_notes text,
  UNIQUE(preset_id, version_number)
);

ALTER TABLE portrait_preset_versions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can view preset versions" 
ON portrait_preset_versions 
FOR SELECT 
USING (true);

CREATE POLICY "Authenticated users can insert preset versions" 
ON portrait_preset_versions 
FOR INSERT 
WITH CHECK (true);

CREATE INDEX idx_preset_versions_preset_id ON portrait_preset_versions(preset_id);

-- Add version tracking to portrait_presets
ALTER TABLE portrait_presets ADD COLUMN current_version integer DEFAULT 1;

-- Create preset_collections table
CREATE TABLE portrait_preset_collections (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  description text,
  creator_name text,
  thumbnail_url text,
  is_public boolean DEFAULT true,
  tags text[] DEFAULT '{}',
  created_at timestamptz DEFAULT now() NOT NULL,
  updated_at timestamptz DEFAULT now() NOT NULL
);

ALTER TABLE portrait_preset_collections ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can view public collections" 
ON portrait_preset_collections 
FOR SELECT 
USING (is_public = true);

CREATE POLICY "Authenticated users can insert collections" 
ON portrait_preset_collections 
FOR INSERT 
WITH CHECK (true);

CREATE POLICY "Authenticated users can update collections" 
ON portrait_preset_collections 
FOR UPDATE 
USING (true);

CREATE POLICY "Authenticated users can delete collections" 
ON portrait_preset_collections 
FOR DELETE 
USING (true);

-- Create junction table for collection presets (many-to-many)
CREATE TABLE portrait_collection_presets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  collection_id uuid NOT NULL REFERENCES portrait_preset_collections(id) ON DELETE CASCADE,
  preset_id uuid NOT NULL REFERENCES portrait_presets(id) ON DELETE CASCADE,
  display_order integer DEFAULT 0,
  created_at timestamptz DEFAULT now() NOT NULL,
  UNIQUE(collection_id, preset_id)
);

ALTER TABLE portrait_collection_presets ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can view collection presets" 
ON portrait_collection_presets 
FOR SELECT 
USING (true);

CREATE POLICY "Authenticated users can manage collection presets" 
ON portrait_collection_presets 
FOR ALL 
USING (true);

CREATE INDEX idx_collection_presets_collection_id ON portrait_collection_presets(collection_id);
CREATE INDEX idx_collection_presets_preset_id ON portrait_collection_presets(preset_id);