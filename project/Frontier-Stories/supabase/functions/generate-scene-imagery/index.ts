import "https://deno.land/x/xhr@0.1.0/mod.ts";
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.7.1';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { sceneId } = await req.json();
    
    console.log(`Generating 4K color imagery for scene: ${sceneId}`);

    const LOVABLE_API_KEY = Deno.env.get('LOVABLE_API_KEY');
    if (!LOVABLE_API_KEY) {
      throw new Error('LOVABLE_API_KEY not configured');
    }

    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    // Fetch scene details
    const { data: scene, error: sceneError } = await supabase
      .from('storyboard_scenes')
      .select('*')
      .eq('id', sceneId)
      .single();

    if (sceneError || !scene) {
      throw new Error('Scene not found');
    }

    // Build detailed prompt for 4K color imagery
    const prompt = `Create a highly detailed, photorealistic 4K color landscape image of an ${scene.era} Old West scene.

SETTING: ${scene.setting}
DESCRIPTION: ${scene.scene_description}
TIME OF DAY: ${scene.time_of_day}
WEATHER: ${scene.weather}
MOOD: ${scene.mood}

Style requirements:
- Ultra high resolution 4K quality (1920x1920)
- Rich, vibrant period-accurate colors
- Photorealistic rendering with dramatic lighting
- Authentic ${scene.era} Old West aesthetics
- Detailed textures (wood, dirt, rock, fabric)
- Atmospheric depth and perspective
- Cinematic composition suitable for storyboarding
- ${scene.time_of_day} lighting with appropriate shadows and highlights
- ${scene.weather} weather conditions affecting the scene
- ${scene.mood} emotional atmosphere`;

    console.log('Generating 4K image with AI...');

    // Use Lovable AI to generate the image
    const aiResponse = await fetch("https://ai.gateway.lovable.dev/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${LOVABLE_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "google/gemini-2.5-flash-image",
        messages: [
          {
            role: "user",
            content: prompt
          }
        ],
        modalities: ["image", "text"]
      })
    });

    if (!aiResponse.ok) {
      const errorText = await aiResponse.text();
      console.error('AI API error:', aiResponse.status, errorText);
      throw new Error(`AI API error: ${aiResponse.status}`);
    }

    const aiData = await aiResponse.json();
    const generatedImageUrl = aiData.choices?.[0]?.message?.images?.[0]?.image_url?.url;

    if (!generatedImageUrl) {
      throw new Error('No image generated from AI');
    }

    console.log('4K image generated, uploading to storage...');

    // Convert base64 to blob
    const base64Data = generatedImageUrl.split(',')[1];
    const binaryData = Uint8Array.from(atob(base64Data), c => c.charCodeAt(0));
    const blob = new Blob([binaryData], { type: 'image/png' });

    // Upload to storage
    const fileName = `storyboard/${scene.story_id}/${scene.scene_number}-${Date.now()}.png`;
    const { data: uploadData, error: uploadError } = await supabase.storage
      .from('actor-images')
      .upload(fileName, blob, {
        contentType: 'image/png',
        upsert: false
      });

    if (uploadError) {
      console.error('Upload error:', uploadError);
      throw uploadError;
    }

    // Get public URL
    const { data: { publicUrl } } = supabase.storage
      .from('actor-images')
      .getPublicUrl(fileName);

    // Update scene with image URL
    const { error: updateError } = await supabase
      .from('storyboard_scenes')
      .update({ image_url: publicUrl })
      .eq('id', sceneId);

    if (updateError) {
      console.error('Update error:', updateError);
      throw updateError;
    }

    console.log('Scene imagery updated successfully');

    return new Response(
      JSON.stringify({ 
        success: true, 
        imageUrl: publicUrl 
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error: any) {
    console.error('Error in generate-scene-imagery function:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to generate scene imagery' }),
      { 
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    );
  }
});
