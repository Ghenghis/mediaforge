-- Create portrait presets table for marketplace
CREATE TABLE public.portrait_presets (
  id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  name text NOT NULL,
  description text,
  creator_name text,
  thumbnail_url text,
  download_count integer NOT NULL DEFAULT 0,
  is_public boolean NOT NULL DEFAULT true,
  tags text[] DEFAULT '{}',
  
  -- Customization parameters
  age integer DEFAULT 35,
  weathering integer DEFAULT 50,
  detail_level integer DEFAULT 50,
  clothing_formality integer DEFAULT 50,
  coverage integer DEFAULT 60,
  fit text DEFAULT 'regular',
  style_profile text DEFAULT 'casual',
  accent_focus text DEFAULT 'balanced',
  texture_detail integer DEFAULT 60,
  contrast integer DEFAULT 55,
  rating text DEFAULT 'general',
  
  CONSTRAINT portrait_presets_age_check CHECK (age >= 21 AND age <= 80),
  CONSTRAINT portrait_presets_weathering_check CHECK (weathering >= 0 AND weathering <= 100),
  CONSTRAINT portrait_presets_detail_level_check CHECK (detail_level >= 0 AND detail_level <= 100)
);

-- Enable RLS
ALTER TABLE public.portrait_presets ENABLE ROW LEVEL SECURITY;

-- Anyone can view public presets
CREATE POLICY "Anyone can view public presets"
  ON public.portrait_presets
  FOR SELECT
  USING (is_public = true);

-- Authenticated users can insert presets
CREATE POLICY "Authenticated users can insert presets"
  ON public.portrait_presets
  FOR INSERT
  WITH CHECK (true);

-- Authenticated users can update presets
CREATE POLICY "Authenticated users can update presets"
  ON public.portrait_presets
  FOR UPDATE
  USING (true);

-- Authenticated users can delete presets
CREATE POLICY "Authenticated users can delete presets"
  ON public.portrait_presets
  FOR DELETE
  USING (true);

-- Add trigger for updated_at
CREATE TRIGGER update_portrait_presets_updated_at
  BEFORE UPDATE ON public.portrait_presets
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();