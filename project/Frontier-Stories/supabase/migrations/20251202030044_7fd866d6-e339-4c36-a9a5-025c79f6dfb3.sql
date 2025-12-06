-- Create storage bucket for actor images
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
  'actor-images',
  'actor-images',
  true,
  5242880, -- 5MB limit
  ARRAY['image/png', 'image/jpeg', 'image/jpg', 'image/webp']
);

-- RLS policies for actor images
CREATE POLICY "Anyone can view actor images"
ON storage.objects
FOR SELECT
USING (bucket_id = 'actor-images');

CREATE POLICY "Authenticated users can upload actor images"
ON storage.objects
FOR INSERT
WITH CHECK (bucket_id = 'actor-images');

CREATE POLICY "Authenticated users can update actor images"
ON storage.objects
FOR UPDATE
USING (bucket_id = 'actor-images');

CREATE POLICY "Authenticated users can delete actor images"
ON storage.objects
FOR DELETE
USING (bucket_id = 'actor-images');