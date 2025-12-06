-- Create portrait history table to track all generated versions
CREATE TABLE public.actor_portrait_history (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  actor_id UUID NOT NULL REFERENCES public.actors(id) ON DELETE CASCADE,
  image_url TEXT NOT NULL,
  color_mode TEXT NOT NULL DEFAULT 'bw',
  generation_params JSONB,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  is_current BOOLEAN NOT NULL DEFAULT false
);

-- Enable RLS
ALTER TABLE public.actor_portrait_history ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Anyone can view portrait history" 
ON public.actor_portrait_history 
FOR SELECT 
USING (true);

CREATE POLICY "Authenticated users can insert portrait history" 
ON public.actor_portrait_history 
FOR INSERT 
WITH CHECK (true);

CREATE POLICY "Authenticated users can update portrait history" 
ON public.actor_portrait_history 
FOR UPDATE 
USING (true);

CREATE POLICY "Authenticated users can delete portrait history" 
ON public.actor_portrait_history 
FOR DELETE 
USING (true);

-- Create index for faster queries
CREATE INDEX idx_actor_portrait_history_actor_id ON public.actor_portrait_history(actor_id);
CREATE INDEX idx_actor_portrait_history_created_at ON public.actor_portrait_history(created_at DESC);