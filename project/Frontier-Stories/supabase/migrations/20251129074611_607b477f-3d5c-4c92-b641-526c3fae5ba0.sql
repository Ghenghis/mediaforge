-- Enable realtime for actors table
ALTER TABLE public.actors REPLICA IDENTITY FULL;

-- Add the actors table to realtime publication
ALTER PUBLICATION supabase_realtime ADD TABLE public.actors;