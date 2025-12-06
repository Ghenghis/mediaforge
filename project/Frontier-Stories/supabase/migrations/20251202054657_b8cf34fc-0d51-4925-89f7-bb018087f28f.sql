-- Create preset reviews table (if not exists)
CREATE TABLE IF NOT EXISTS public.portrait_preset_reviews (
  id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  preset_id uuid NOT NULL,
  reviewer_name text,
  rating integer NOT NULL CHECK (rating >= 1 AND rating <= 5),
  review_text text,
  is_verified boolean NOT NULL DEFAULT false
);

-- Add foreign key if it doesn't exist
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'portrait_preset_reviews_preset_id_fkey'
  ) THEN
    ALTER TABLE public.portrait_preset_reviews
    ADD CONSTRAINT portrait_preset_reviews_preset_id_fkey
    FOREIGN KEY (preset_id) REFERENCES public.portrait_presets(id) ON DELETE CASCADE;
  END IF;
END $$;

-- Enable RLS if not already enabled
ALTER TABLE public.portrait_preset_reviews ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist and recreate
DROP POLICY IF EXISTS "Anyone can view reviews" ON public.portrait_preset_reviews;
CREATE POLICY "Anyone can view reviews"
  ON public.portrait_preset_reviews
  FOR SELECT
  USING (true);

DROP POLICY IF EXISTS "Authenticated users can insert reviews" ON public.portrait_preset_reviews;
CREATE POLICY "Authenticated users can insert reviews"
  ON public.portrait_preset_reviews
  FOR INSERT
  WITH CHECK (true);

DROP POLICY IF EXISTS "Authenticated users can update reviews" ON public.portrait_preset_reviews;
CREATE POLICY "Authenticated users can update reviews"
  ON public.portrait_preset_reviews
  FOR UPDATE
  USING (true);

-- Add rating columns to presets table if not exists
ALTER TABLE public.portrait_presets 
ADD COLUMN IF NOT EXISTS average_rating numeric DEFAULT 0,
ADD COLUMN IF NOT EXISTS review_count integer DEFAULT 0;

-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_preset_reviews_preset_id ON public.portrait_preset_reviews(preset_id);
CREATE INDEX IF NOT EXISTS idx_presets_average_rating ON public.portrait_presets(average_rating DESC);
CREATE INDEX IF NOT EXISTS idx_presets_download_count ON public.portrait_presets(download_count DESC);
CREATE INDEX IF NOT EXISTS idx_presets_created_at ON public.portrait_presets(created_at DESC);