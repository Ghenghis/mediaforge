-- Frontier-Stories Database Initialization Script
-- This script sets up the local PostgreSQL database with all required tables

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create update_updated_at_column function
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create actors table
CREATE TABLE IF NOT EXISTS public.actors (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  full_name TEXT GENERATED ALWAYS AS (first_name || ' ' || last_name) STORED,
  role TEXT NOT NULL,
  era TEXT NOT NULL DEFAULT '1870s',
  ethnicity TEXT,
  voice_id TEXT,
  voice_name TEXT,
  image_url TEXT,
  bio TEXT,
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create stories table
CREATE TABLE IF NOT EXISTS public.stories (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT,
  genre TEXT,
  era TEXT NOT NULL DEFAULT '1870s',
  is_published BOOLEAN NOT NULL DEFAULT false,
  master_volume DECIMAL(3,2) DEFAULT 1.00,
  pause_duration DECIMAL(3,2) DEFAULT 0.50,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create story_lines table
CREATE TABLE IF NOT EXISTS public.story_lines (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  story_id UUID NOT NULL REFERENCES public.stories(id) ON DELETE CASCADE,
  actor_id UUID NOT NULL REFERENCES public.actors(id) ON DELETE CASCADE,
  line_number INTEGER NOT NULL,
  text TEXT NOT NULL,
  audio_url TEXT,
  volume DECIMAL(3,2) NOT NULL DEFAULT 0.80,
  fade_in BOOLEAN NOT NULL DEFAULT false,
  fade_out BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create story_templates table
CREATE TABLE IF NOT EXISTS public.story_templates (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT,
  genre TEXT NOT NULL,
  era TEXT NOT NULL DEFAULT '1870s',
  icon_name TEXT DEFAULT 'Heart',
  is_active BOOLEAN NOT NULL DEFAULT true,
  use_count INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create story_template_lines table
CREATE TABLE IF NOT EXISTS public.story_template_lines (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  template_id UUID NOT NULL REFERENCES public.story_templates(id) ON DELETE CASCADE,
  line_number INTEGER NOT NULL,
  actor_role TEXT NOT NULL,
  actor_first_name TEXT NOT NULL,
  actor_last_name TEXT NOT NULL,
  text TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create portrait_presets table
CREATE TABLE IF NOT EXISTS public.portrait_presets (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  settings JSONB NOT NULL DEFAULT '{}',
  is_default BOOLEAN NOT NULL DEFAULT false,
  min_age INTEGER DEFAULT 18,
  max_age INTEGER DEFAULT 100,
  character_style TEXT,
  clothing_type TEXT,
  clothing_style TEXT,
  character_details JSONB DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create portrait_preset_versions table
CREATE TABLE IF NOT EXISTS public.portrait_preset_versions (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  preset_id UUID NOT NULL REFERENCES public.portrait_presets(id) ON DELETE CASCADE,
  version_number INTEGER NOT NULL,
  settings JSONB NOT NULL,
  min_age INTEGER,
  max_age INTEGER,
  character_style TEXT,
  clothing_type TEXT,
  clothing_style TEXT,
  character_details JSONB,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create portrait_preset_collections table
CREATE TABLE IF NOT EXISTS public.portrait_preset_collections (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  is_randomized BOOLEAN DEFAULT false,
  randomization_rules JSONB DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create actor_portrait_history table
CREATE TABLE IF NOT EXISTS public.actor_portrait_history (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  actor_id UUID NOT NULL REFERENCES public.actors(id) ON DELETE CASCADE,
  image_url TEXT NOT NULL,
  color_mode TEXT DEFAULT 'bw',
  generation_params JSONB DEFAULT '{}',
  is_current BOOLEAN DEFAULT false,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create app_settings table for storing configuration
CREATE TABLE IF NOT EXISTS public.app_settings (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  key TEXT NOT NULL UNIQUE,
  value JSONB NOT NULL,
  description TEXT,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create model_configs table for LM Studio model settings
CREATE TABLE IF NOT EXISTS public.model_configs (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT NOT NULL,
  model_type TEXT NOT NULL, -- 'vision', 'text', 'tts'
  model_path TEXT,
  api_url TEXT,
  settings JSONB DEFAULT '{}',
  is_default BOOLEAN DEFAULT false,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_story_lines_story_id ON public.story_lines(story_id);
CREATE INDEX IF NOT EXISTS idx_story_lines_line_number ON public.story_lines(story_id, line_number);
CREATE INDEX IF NOT EXISTS idx_story_templates_active ON public.story_templates(is_active);
CREATE INDEX IF NOT EXISTS idx_story_template_lines_template_id ON public.story_template_lines(template_id);
CREATE INDEX IF NOT EXISTS idx_actor_portrait_history_actor_id ON public.actor_portrait_history(actor_id);
CREATE INDEX IF NOT EXISTS idx_model_configs_type ON public.model_configs(model_type);

-- Create triggers
CREATE TRIGGER update_actors_updated_at
  BEFORE UPDATE ON public.actors
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_stories_updated_at
  BEFORE UPDATE ON public.stories
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_story_lines_updated_at
  BEFORE UPDATE ON public.story_lines
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_story_templates_updated_at
  BEFORE UPDATE ON public.story_templates
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_portrait_presets_updated_at
  BEFORE UPDATE ON public.portrait_presets
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_app_settings_updated_at
  BEFORE UPDATE ON public.app_settings
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_model_configs_updated_at
  BEFORE UPDATE ON public.model_configs
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Insert default app settings
INSERT INTO public.app_settings (key, value, description) VALUES
  ('lm_studio', '{"url": "http://localhost:1234", "modelsPath": "C:\\Users\\Admin\\.lmstudio\\models"}', 'LM Studio configuration'),
  ('default_era', '"1870s"', 'Default era for stories'),
  ('adult_content', 'true', 'Enable adult content generation'),
  ('image_quality', '"high"', 'Default image generation quality')
ON CONFLICT (key) DO NOTHING;

-- Insert default model configs
INSERT INTO public.model_configs (name, model_type, api_url, is_default, settings) VALUES
  ('Default Vision Model', 'vision', 'http://localhost:1234/v1', true, '{"temperature": 0.8, "maxTokens": 4096}'),
  ('Default Text Model', 'text', 'http://localhost:1234/v1', true, '{"temperature": 0.9, "maxTokens": 4096}')
ON CONFLICT DO NOTHING;

-- Grant permissions (for local development, open access)
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres;

SELECT 'Database initialization complete!' as status;
