-- Create story_lines table to store dialogue lines
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

-- Add index for faster queries
CREATE INDEX idx_story_lines_story_id ON public.story_lines(story_id);
CREATE INDEX idx_story_lines_line_number ON public.story_lines(story_id, line_number);

-- Enable RLS
ALTER TABLE public.story_lines ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Anyone can view story lines"
  ON public.story_lines
  FOR SELECT
  USING (true);

CREATE POLICY "Authenticated users can insert story lines"
  ON public.story_lines
  FOR INSERT
  WITH CHECK (true);

CREATE POLICY "Authenticated users can update story lines"
  ON public.story_lines
  FOR UPDATE
  USING (true);

CREATE POLICY "Authenticated users can delete story lines"
  ON public.story_lines
  FOR DELETE
  USING (true);

-- Add master_volume and pause_duration to stories table
ALTER TABLE public.stories
ADD COLUMN IF NOT EXISTS master_volume DECIMAL(3,2) DEFAULT 1.00,
ADD COLUMN IF NOT EXISTS pause_duration DECIMAL(3,2) DEFAULT 0.50;

-- Update RLS policies for stories table to allow insert/update/delete
DROP POLICY IF EXISTS "Anyone can view published stories" ON public.stories;

CREATE POLICY "Anyone can view stories"
  ON public.stories
  FOR SELECT
  USING (true);

CREATE POLICY "Authenticated users can insert stories"
  ON public.stories
  FOR INSERT
  WITH CHECK (true);

CREATE POLICY "Authenticated users can update stories"
  ON public.stories
  FOR UPDATE
  USING (true);

CREATE POLICY "Authenticated users can delete stories"
  ON public.stories
  FOR DELETE
  USING (true);

-- Enable realtime for story_lines
ALTER TABLE public.story_lines REPLICA IDENTITY FULL;
ALTER PUBLICATION supabase_realtime ADD TABLE public.story_lines;

-- Create trigger for story_lines updated_at
CREATE TRIGGER update_story_lines_updated_at
  BEFORE UPDATE ON public.story_lines
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();