import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.3';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { storyId, era, sceneryType, description } = await req.json();

    if (!storyId || !era || !sceneryType) {
      throw new Error('Story ID, era, and scenery type are required');
    }

    const LOVABLE_API_KEY = Deno.env.get('LOVABLE_API_KEY');
    const SUPABASE_URL = Deno.env.get('SUPABASE_URL');
    const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

    if (!LOVABLE_API_KEY || !SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
      throw new Error('Missing required environment variables');
    }

    // Create detailed prompt for authentic 1800s Old West scenery
    const sceneryPrompts: Record<string, string> = {
      town: `A detailed panoramic view of an authentic ${era} Old West frontier town. Dusty main street with wooden buildings, saloon with swinging doors, general store, sheriff's office, hitching posts with horses. Weathered wooden sidewalks, wagon wheel tracks in dirt road. Mountains in background, clear blue sky with scattered clouds. Period-accurate architecture and details.`,
      landscape: `A sweeping landscape of the ${era} American frontier. Rolling plains with sagebrush, distant mesas and buttes, dramatic sky with clouds. Perhaps a lone rider on horseback in the distance. Natural terrain with dirt trails, rocky outcrops. Authentic wilderness as it appeared in ${era}.`,
      interior: `The interior of an authentic ${era} Old West building. Wooden plank walls and floors, oil lamps for lighting, period furniture, worn textures. Could be a saloon with bar and tables, a homestead cabin, or a general store. Dim natural lighting through windows, authentic period details and artifacts.`,
      ranch: `An authentic ${era} cattle ranch or homestead. Wooden ranch house, corrals with horses, barn in background. Split-rail fencing, windmill, water trough. Open prairie landscape surrounding. Mountains in distance. Period-accurate ranch equipment and structures.`,
      canyon: `A dramatic Western canyon landscape from ${era}. Red rock formations, steep canyon walls, winding river or dry riverbed below. Native American cliff dwellings visible in rock face. Clear sky, natural lighting showcasing the rugged terrain.`,
    };

    const basePrompt = sceneryPrompts[sceneryType] || sceneryPrompts.landscape;
    const customDescription = description ? `\n\nAdditional scene details: ${description}` : '';

    const prompt = `Create an ultra-high resolution authentic ${era} Old West photograph scenery.

${basePrompt}${customDescription}

CRITICAL REQUIREMENTS:
- Sepia-toned or early color photograph aesthetic from ${era}
- Authentic historical accuracy for the time period
- Weathered and aged photograph texture
- Natural lighting as in period photography
- Grainy texture with slight imperfections
- Faded colors or black and white tones
- Must look like a real historical photograph, NOT modern
- Wide aspect ratio suitable for background scenery
- Ultra high resolution, maximum detail for 4K quality
- Include authentic ${era} details: no modern elements whatsoever

STYLE NOTES:
- If color: Muted, faded colors as in restored historical photos
- If black and white: Rich tonal range with authentic silver gelatin print aesthetic
- Slight vignette on edges typical of vintage photography
- Dust, scratches, and aging appropriate for a ${era} photograph
- Natural imperfections that add authenticity`;

    console.log('Generating scenery with AI for:', sceneryType, era);

    const response = await fetch('https://ai.gateway.lovable.dev/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${LOVABLE_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'google/gemini-2.5-flash-image',
        messages: [
          {
            role: 'user',
            content: prompt
          }
        ],
        modalities: ['image', 'text'],
        size: '1920x1024'
      }),
    });

    if (!response.ok) {
      if (response.status === 429) {
        return new Response(
          JSON.stringify({ error: 'Rate limit exceeded. Please try again later.' }),
          { status: 429, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        );
      }
      if (response.status === 402) {
        return new Response(
          JSON.stringify({ error: 'AI credits exhausted. Please add credits to continue.' }),
          { status: 402, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        );
      }
      const errorText = await response.text();
      console.error('AI gateway error:', response.status, errorText);
      throw new Error(`AI gateway error: ${response.status}`);
    }

    const data = await response.json();
    const imageBase64 = data.choices?.[0]?.message?.images?.[0]?.image_url?.url;

    if (!imageBase64) {
      throw new Error('No image generated from AI');
    }

    console.log('Scenery generated, uploading to storage...');

    // Convert base64 to binary
    const base64Data = imageBase64.replace(/^data:image\/\w+;base64,/, '');
    const binaryData = Uint8Array.from(atob(base64Data), c => c.charCodeAt(0));

    // Upload to Supabase Storage
    const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);
    const fileName = `${storyId}-${sceneryType}-${Date.now()}.png`;
    const filePath = `scenery/${fileName}`;

    const { data: uploadData, error: uploadError } = await supabase.storage
      .from('actor-images')
      .upload(filePath, binaryData, {
        contentType: 'image/png',
        upsert: true
      });

    if (uploadError) {
      console.error('Storage upload error:', uploadError);
      throw new Error(`Failed to upload image: ${uploadError.message}`);
    }

    // Get public URL
    const { data: urlData } = supabase.storage
      .from('actor-images')
      .getPublicUrl(filePath);

    const publicUrl = urlData.publicUrl;

    console.log('Scenery generated and uploaded successfully');

    return new Response(
      JSON.stringify({ 
        success: true,
        imageUrl: publicUrl,
        sceneryType,
        storyId 
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );
  } catch (error) {
    console.error('Error generating scenery:', error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    return new Response(
      JSON.stringify({ error: errorMessage }),
      {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );
  }
});
