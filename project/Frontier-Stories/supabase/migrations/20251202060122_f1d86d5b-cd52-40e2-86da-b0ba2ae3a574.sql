-- Create user favorites table for bookmarking presets
CREATE TABLE IF NOT EXISTS public.user_favorite_presets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  preset_id UUID REFERENCES public.portrait_presets(id) ON DELETE CASCADE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  UNIQUE(user_id, preset_id)
);

-- Add detailed attributes to portrait_presets
ALTER TABLE public.portrait_presets
ADD COLUMN IF NOT EXISTS min_age INTEGER DEFAULT 18,
ADD COLUMN IF NOT EXISTS max_age INTEGER DEFAULT 100,
ADD COLUMN IF NOT EXISTS character_style TEXT,
ADD COLUMN IF NOT EXISTS clothing_type TEXT,
ADD COLUMN IF NOT EXISTS clothing_style TEXT,
ADD COLUMN IF NOT EXISTS character_details JSONB DEFAULT '{}'::jsonb;

-- Add detailed attributes to portrait_preset_versions for history
ALTER TABLE public.portrait_preset_versions
ADD COLUMN IF NOT EXISTS min_age INTEGER,
ADD COLUMN IF NOT EXISTS max_age INTEGER,
ADD COLUMN IF NOT EXISTS character_style TEXT,
ADD COLUMN IF NOT EXISTS clothing_type TEXT,
ADD COLUMN IF NOT EXISTS clothing_style TEXT,
ADD COLUMN IF NOT EXISTS character_details JSONB;

-- Add collection attributes for randomization
ALTER TABLE public.portrait_preset_collections
ADD COLUMN IF NOT EXISTS is_randomized BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS randomization_rules JSONB DEFAULT '{}'::jsonb;

-- Enable RLS on user_favorite_presets
ALTER TABLE public.user_favorite_presets ENABLE ROW LEVEL SECURITY;

-- RLS policies for favorites
CREATE POLICY "Users can view their own favorites"
  ON public.user_favorite_presets
  FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can add their own favorites"
  ON public.user_favorite_presets
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can remove their own favorites"
  ON public.user_favorite_presets
  FOR DELETE
  USING (auth.uid() = user_id);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_favorite_presets_user_id ON public.user_favorite_presets(user_id);
CREATE INDEX IF NOT EXISTS idx_user_favorite_presets_preset_id ON public.user_favorite_presets(preset_id);
CREATE INDEX IF NOT EXISTS idx_portrait_presets_age_range ON public.portrait_presets(min_age, max_age);
CREATE INDEX IF NOT EXISTS idx_portrait_presets_character_style ON public.portrait_presets(character_style);
CREATE INDEX IF NOT EXISTS idx_portrait_presets_clothing_type ON public.portrait_presets(clothing_type);