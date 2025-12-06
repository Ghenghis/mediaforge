-- Create story templates table
CREATE TABLE public.story_templates (
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

-- Create story template lines table
CREATE TABLE public.story_template_lines (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  template_id UUID NOT NULL REFERENCES public.story_templates(id) ON DELETE CASCADE,
  line_number INTEGER NOT NULL,
  actor_role TEXT NOT NULL,
  actor_first_name TEXT NOT NULL,
  actor_last_name TEXT NOT NULL,
  text TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE public.story_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.story_template_lines ENABLE ROW LEVEL SECURITY;

-- RLS Policies - public read access for templates
CREATE POLICY "Anyone can view active templates"
ON public.story_templates
FOR SELECT
USING (is_active = true);

CREATE POLICY "Anyone can view template lines"
ON public.story_template_lines
FOR SELECT
USING (true);

-- RLS Policies - authenticated users can manage templates
CREATE POLICY "Authenticated users can insert templates"
ON public.story_templates
FOR INSERT
WITH CHECK (true);

CREATE POLICY "Authenticated users can update templates"
ON public.story_templates
FOR UPDATE
USING (true);

CREATE POLICY "Authenticated users can delete templates"
ON public.story_templates
FOR DELETE
USING (true);

CREATE POLICY "Authenticated users can insert template lines"
ON public.story_template_lines
FOR INSERT
WITH CHECK (true);

CREATE POLICY "Authenticated users can update template lines"
ON public.story_template_lines
FOR UPDATE
USING (true);

CREATE POLICY "Authenticated users can delete template lines"
ON public.story_template_lines
FOR DELETE
USING (true);

-- Trigger for auto-updating updated_at
CREATE TRIGGER update_story_templates_updated_at
BEFORE UPDATE ON public.story_templates
FOR EACH ROW
EXECUTE FUNCTION public.update_updated_at_column();

-- Index for performance
CREATE INDEX idx_story_templates_active ON public.story_templates(is_active);
CREATE INDEX idx_story_template_lines_template_id ON public.story_template_lines(template_id);
CREATE INDEX idx_story_template_lines_line_number ON public.story_template_lines(template_id, line_number);