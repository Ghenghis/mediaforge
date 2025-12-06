-- Create storyboard scenes table to store scene-specific imagery
CREATE TABLE IF NOT EXISTS public.storyboard_scenes (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  story_id UUID NOT NULL REFERENCES public.stories(id) ON DELETE CASCADE,
  scene_number INTEGER NOT NULL,
  line_range_start INTEGER NOT NULL,
  line_range_end INTEGER NOT NULL,
  scene_description TEXT NOT NULL,
  image_url TEXT,
  era TEXT NOT NULL,
  setting TEXT,
  time_of_day TEXT,
  weather TEXT,
  mood TEXT,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  UNIQUE(story_id, scene_number)
);

-- Enable RLS
ALTER TABLE public.storyboard_scenes ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Anyone can view storyboard scenes"
  ON public.storyboard_scenes FOR SELECT
  USING (true);

CREATE POLICY "Authenticated users can insert storyboard scenes"
  ON public.storyboard_scenes FOR INSERT
  WITH CHECK (true);

CREATE POLICY "Authenticated users can update storyboard scenes"
  ON public.storyboard_scenes FOR UPDATE
  USING (true);

CREATE POLICY "Authenticated users can delete storyboard scenes"
  ON public.storyboard_scenes FOR DELETE
  USING (true);

-- Add updated_at trigger
CREATE TRIGGER update_storyboard_scenes_updated_at
  BEFORE UPDATE ON public.storyboard_scenes
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();

-- Create index for faster queries
CREATE INDEX idx_storyboard_scenes_story_id ON public.storyboard_scenes(story_id);
CREATE INDEX idx_storyboard_scenes_scene_number ON public.storyboard_scenes(story_id, scene_number);