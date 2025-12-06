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
    const { actorId, imageUrl, style, fullName, role } = await req.json();
    
    console.log(`Applying ${style} style to portrait for: ${fullName}`);

    const LOVABLE_API_KEY = Deno.env.get('LOVABLE_API_KEY');
    if (!LOVABLE_API_KEY) {
      throw new Error('LOVABLE_API_KEY not configured');
    }

    const stylePrompts = {
      'oil-painting': 'Transform this into a classical oil painting portrait with thick brush strokes, rich colors, and a painted texture. Maintain the person\'s likeness but add artistic oil painting characteristics with visible brush work and layered paint effects.',
      'charcoal-sketch': 'Convert this into a detailed charcoal sketch drawing with dramatic shading, cross-hatching, smudging effects, and visible charcoal texture. Keep the portrait recognizable but rendered entirely in black and white charcoal medium with artistic sketch lines.',
      'daguerreotype': 'Transform this into an authentic 1850s daguerreotype photograph with silvery metallic sheen, slight haziness, vignetting around edges, subtle brass tones, and the characteristic mirror-like quality of early photography. Add period-accurate wear and aging.',
    };

    const prompt = stylePrompts[style as keyof typeof stylePrompts] || stylePrompts['oil-painting'];

    // Use Lovable AI to apply style transfer
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
            content: [
              {
                type: "text",
                text: prompt
              },
              {
                type: "image_url",
                image_url: {
                  url: imageUrl
                }
              }
            ]
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

    console.log('Style applied, uploading to storage...');

    // Convert base64 to blob
    const base64Data = generatedImageUrl.split(',')[1];
    const binaryData = Uint8Array.from(atob(base64Data), c => c.charCodeAt(0));
    const blob = new Blob([binaryData], { type: 'image/png' });

    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    // Upload to storage
    const fileName = `${actorId}-${style}-${Date.now()}.png`;
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

    console.log('Styled portrait uploaded successfully');

    // Save to portrait history
    const { error: historyError } = await supabase
      .from('actor_portrait_history')
      .insert({
        actor_id: actorId,
        image_url: publicUrl,
        color_mode: 'styled',
        generation_params: {
          style: style,
          original_image: imageUrl,
          role: role,
          full_name: fullName,
        },
        is_current: false
      });

    if (historyError) {
      console.error('History save error:', historyError);
    }

    return new Response(
      JSON.stringify({ 
        success: true, 
        imageUrl: publicUrl,
        style: style 
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error: any) {
    console.error('Error in style-transfer function:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to apply style' }),
      { 
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    );
  }
});
