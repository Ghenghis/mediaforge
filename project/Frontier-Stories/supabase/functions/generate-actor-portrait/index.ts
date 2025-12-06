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
    const { actorId, fullName, role, era, ethnicity, colorMode = 'bw', customization = {} } = await req.json();

    if (!actorId || !fullName || !role) {
      throw new Error('Actor ID, full name, and role are required');
    }

    // Extract customization parameters with defaults
    const age = customization.age || 50; // 21-80
    const weathering = customization.weathering || 50; // 0-100
    const detailLevel = customization.detailLevel || 50; // 0-100
    const clothingStyle = customization.clothingStyle || 50; // 0=worn, 100=formal
    const coverage = customization.coverage || 60; // 0-100 coverage level
    const fit = customization.fit || 'regular'; // relaxed, regular, tailored, form_fitting, compression
    const styleProfile = customization.styleProfile || 'casual'; // professional, casual, athletic, traditional, nightlife, editorial
    const accentFocus = customization.accentFocus || 'balanced'; // balanced, upper, lower, accessories
    const textureDetail = customization.textureDetail || 60; // 0-100
    const contrast = customization.contrast || 55; // 0-100
    const rating = customization.rating || 'general'; // general, teen_plus, adult_21_plus

    const LOVABLE_API_KEY = Deno.env.get('LOVABLE_API_KEY');
    const SUPABASE_URL = Deno.env.get('SUPABASE_URL');
    const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

    if (!LOVABLE_API_KEY || !SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
      throw new Error('Missing required environment variables');
    }

    // Create detailed prompt for authentic 1800s Old West portrait
    const ethnicityGuide = ethnicity || (
      role.toLowerCase().includes('native') || 
      role.toLowerCase().includes('apache') || 
      role.toLowerCase().includes('lakota') ||
      role.toLowerCase().includes('sioux') ||
      role.toLowerCase().includes('cheyenne') ||
      role.toLowerCase().includes('comanche')
        ? 'Native American indigenous person'
        : 'European-American settler'
    );

    // Generate age description
    const ageDesc = age < 35 ? 'young adult' : age < 55 ? 'middle-aged' : 'elderly';
    
    // Generate weathering description
    const weatheringDesc = weathering < 30 
      ? 'minimal wear, relatively clean'
      : weathering < 70
      ? 'moderate weathering with visible aging'
      : 'heavily weathered with significant damage and fading';
    
    // Generate detail level description
    const detailDesc = detailLevel < 30
      ? 'soft focus with minimal facial detail'
      : detailLevel < 70
      ? 'moderate detail with clear features'
      : 'extremely detailed with sharp focus on facial features, wrinkles, and textures';
    
    // Generate clothing description based on styleProfile
    const styleMap: Record<string, string> = {
      professional: 'professional business attire',
      casual: 'casual everyday clothing',
      athletic: 'athletic performance wear',
      traditional: 'traditional ceremonial clothing',
      nightlife: 'stylish nightlife outfit',
      editorial: 'bold high-fashion editorial outfit'
    };
    const styleDesc = styleMap[styleProfile] || 'contemporary clothing';
    
    const clothingDesc = clothingStyle < 30
      ? 'casual, relaxed styling'
      : clothingStyle < 70
      ? 'smart casual styling'
      : 'formal, elegant styling';

    // Coverage description (always fully clothed)
    const coverageDesc = coverage >= 85
      ? 'high coverage with layered garments, modest fashion'
      : coverage >= 60
      ? 'moderate overall coverage'
      : coverage >= 40
      ? 'bold outfit with reduced coverage, but clearly fully clothed'
      : 'bold, minimal coverage while still fully clothed (no nudity)';

    // Fit description
    const fitMap: Record<string, string> = {
      relaxed: 'relaxed, loose fit',
      regular: 'regular, natural fit',
      tailored: 'tailored, structured fit',
      form_fitting: 'form-fitting, body-following silhouette',
      compression: 'compression-style performance fabric'
    };
    const fitDesc = fitMap[fit] || 'regular fit';

    // Accent focus
    const accentMap: Record<string, string> = {
      balanced: 'balanced emphasis between upper and lower garments',
      upper: 'visually emphasized jackets and upper garments',
      lower: 'visually emphasized pants or skirts',
      accessories: 'distinct accessories such as belts, jewelry, or headwear'
    };
    const accentDesc = accentMap[accentFocus] || 'balanced styling';

    // Texture description
    const textureDesc = textureDetail >= 70
      ? 'highly visible fabric weave, seams, and stitching'
      : textureDetail >= 40
      ? 'moderate fabric texture and detail'
      : 'soft, minimal fabric texture';

    // Contrast description
    const contrastDesc = contrast >= 70
      ? 'dramatic, high-contrast lighting with deep shadows'
      : contrast >= 40
      ? 'balanced lighting and contrast'
      : 'soft, low-contrast lighting';

    // Rating-based constraints
    const ratingDesc = rating === 'general'
      ? 'modest fashion, suitable for general audiences'
      : rating === 'teen_plus'
      ? 'trendy fashion with slightly more revealing cuts'
      : 'bold, fashion-forward outfit for an adult audience, fully clothed';

    const colorInstructions = colorMode === 'color' 
      ? `- Full color 4K photograph with rich, authentic ${era} colors
- Vibrant but period-accurate color palette
- Natural skin tones and authentic fabric colors
- Weathered and faded colors as they would appear in restored historical photos`
      : `- Black and white 4K photograph
- High contrast monochrome with deep blacks and bright whites
- Authentic silver gelatin print aesthetic
- Rich tonal range from pure black to bright white`;

    const prompt = `Create an ultra-high resolution authentic ${era} vintage photograph portrait of ${fullName}, a ${role}.

CRITICAL REQUIREMENTS:
- ${ethnicityGuide} with period-accurate features and appearance
- Person appears to be ${ageDesc} (approximately ${age} years old)
- ${styleDesc} with ${clothingDesc}
- ${coverageDesc}
- ${fitDesc}
- ${accentDesc}
- ${textureDesc}
- ${contrastDesc}
- ${ratingDesc}
- SAFETY: chest, groin, and buttocks fully covered, no transparent fabrics on those areas, no nudity
- Photograph condition: ${weatheringDesc}
- Image detail: ${detailDesc}
${colorInstructions}
- Daguerreotype or tintype photograph style from ${era}
- Period-appropriate ${era} hairstyle
- Stoic, serious expression (people didn't smile in old photos)
- Soft focus and vignette edges typical of vintage photography
- Authentic Old West frontier aesthetic
- Head and shoulders portrait composition
- Ultra high resolution, maximum detail

STYLE NOTES:
- If Native American: Traditional tribal clothing, long hair, authentic ceremonial dress or warrior attire from the specific tribe
- If settler/cowboy: Frontier attire appropriate to the styling specified
- Must look like a real historical photograph from ${era}, NOT modern
- Include authentic imperfections based on weathering level
- Natural lighting as in 1800s photography studios
- Maximum resolution and detail for 4K quality`;

    console.log('Generating portrait with AI for:', fullName);

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
        size: '1920x1920'
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

    console.log('Image generated, uploading to storage...');

    // Convert base64 to binary
    const base64Data = imageBase64.replace(/^data:image\/\w+;base64,/, '');
    const binaryData = Uint8Array.from(atob(base64Data), c => c.charCodeAt(0));

    // Upload to Supabase Storage
    const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);
    const fileName = `${actorId}-${Date.now()}.png`;
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

    // Save current portrait to history before updating
    const { data: currentActor } = await supabase
      .from('actors')
      .select('image_url')
      .eq('id', actorId)
      .single();

    if (currentActor?.image_url) {
      // Mark all previous portraits as not current
      await supabase
        .from('actor_portrait_history')
        .update({ is_current: false })
        .eq('actor_id', actorId);

      // Save old portrait to history
      await supabase
        .from('actor_portrait_history')
        .insert({
          actor_id: actorId,
          image_url: currentActor.image_url,
          color_mode: 'bw', // Assume previous was B&W
          generation_params: {},
          is_current: false,
        });
    }

    // Update actor record with new image URL
    const { error: updateError } = await supabase
      .from('actors')
      .update({ image_url: publicUrl })
      .eq('id', actorId);

    if (updateError) {
      console.error('Database update error:', updateError);
      throw new Error(`Failed to update actor: ${updateError.message}`);
    }

    // Save new portrait to history as current
    await supabase
      .from('actor_portrait_history')
      .insert({
        actor_id: actorId,
        image_url: publicUrl,
        color_mode: colorMode,
        generation_params: { age, weathering, detailLevel, clothingStyle },
        is_current: true,
      });

    console.log('Portrait generated and uploaded successfully');

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
    console.error('Error generating portrait:', error);
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