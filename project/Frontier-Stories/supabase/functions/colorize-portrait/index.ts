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
    const { actorId, imageUrl, era, fullName, role } = await req.json();

    if (!actorId || !imageUrl || !era) {
      throw new Error('Actor ID, image URL, and era are required');
    }

    const LOVABLE_API_KEY = Deno.env.get('LOVABLE_API_KEY');
    const SUPABASE_URL = Deno.env.get('SUPABASE_URL');
    const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

    if (!LOVABLE_API_KEY || !SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
      throw new Error('Missing required environment variables');
    }

    const prompt = `Colorize this black and white ${era} historical photograph with period-accurate colors.

CRITICAL COLORIZATION REQUIREMENTS:
- Add authentic ${era} Old West colors while preserving all details
- Skin tones: Natural, realistic complexion appropriate for the person
- Clothing: Period-accurate fabric colors (browns, grays, earth tones, deep blues)
- Background: Sepia-toned or muted historical colors
- Maintain the aged, vintage photograph aesthetic
- Keep all weathering, grain, and damage from the original
- Colors should look like restored historical photos, NOT modern
- Faded, muted color palette as colors would have appeared in ${era}
- Natural lighting and tones from period photography
- Preserve vignette edges and soft focus
- DO NOT make it look modern or digitally enhanced
- Keep the authentic ${era} frontier atmosphere

The result should look like a professionally restored historical color photograph from ${era}.`;

    console.log('Colorizing portrait for:', fullName);

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
            content: [
              {
                type: 'text',
                text: prompt
              },
              {
                type: 'image_url',
                image_url: {
                  url: imageUrl
                }
              }
            ]
          }
        ],
        modalities: ['image', 'text']
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

    console.log('Image colorized, uploading to storage...');

    // Convert base64 to binary
    const base64Data = imageBase64.replace(/^data:image\/\w+;base64,/, '');
    const binaryData = Uint8Array.from(atob(base64Data), c => c.charCodeAt(0));

    // Upload to Supabase Storage
    const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);
    const fileName = `${actorId}-colorized-${Date.now()}.png`;
    const filePath = `portraits/${fileName}`;

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

    // Save colorized version to history
    await supabase
      .from('actor_portrait_history')
      .insert({
        actor_id: actorId,
        image_url: publicUrl,
        color_mode: 'color',
        generation_params: { colorized: true, source_image: imageUrl },
        is_current: false,
      });

    console.log('Portrait colorized and uploaded successfully');

    return new Response(
      JSON.stringify({ 
        success: true,
        imageUrl: publicUrl,
        actorId 
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );
  } catch (error) {
    console.error('Error colorizing portrait:', error);
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
