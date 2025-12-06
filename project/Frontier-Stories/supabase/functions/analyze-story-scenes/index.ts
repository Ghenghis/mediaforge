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
    const { storyId } = await req.json();
    
    console.log(`Analyzing story scenes for story: ${storyId}`);

    const LOVABLE_API_KEY = Deno.env.get('LOVABLE_API_KEY');
    if (!LOVABLE_API_KEY) {
      throw new Error('LOVABLE_API_KEY not configured');
    }

    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    // Fetch story and lines
    const { data: story, error: storyError } = await supabase
      .from('stories')
      .select('*, story_lines(*)')
      .eq('id', storyId)
      .order('line_number', { foreignTable: 'story_lines', ascending: true })
      .single();

    if (storyError || !story) {
      throw new Error('Story not found');
    }

    // Build full story text
    const storyText = story.story_lines
      .map((line: any) => `[Line ${line.line_number}] ${line.text}`)
      .join('\n');

    console.log('Analyzing story with AI to extract scenes...');

    // Use Lovable AI to analyze and extract scenes
    const aiResponse = await fetch("https://ai.gateway.lovable.dev/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${LOVABLE_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "google/gemini-2.5-flash",
        messages: [
          {
            role: "system",
            content: `You are a professional storyboard artist analyzing story scripts to identify distinct visual scenes. 
For each scene, identify:
- The line number range (start and end)
- A detailed visual description of the setting/location
- The setting type (town, desert, canyon, river, cabin, etc.)
- Time of day (dawn, morning, noon, afternoon, dusk, night)
- Weather conditions (clear, cloudy, rainy, stormy, snowy, foggy)
- The mood/atmosphere (tense, peaceful, dramatic, mysterious, joyful, etc.)

Return a JSON array of scenes. Each scene should cover 1-5 dialogue lines typically, representing a distinct visual moment.`
          },
          {
            role: "user",
            content: `Analyze this ${story.era} Old West story and break it down into visual scenes for storyboarding. The story era is "${story.era}".\n\n${storyText}`
          }
        ],
        tools: [
          {
            type: "function",
            function: {
              name: "extract_scenes",
              description: "Extract visual scenes from the story for storyboarding",
              parameters: {
                type: "object",
                properties: {
                  scenes: {
                    type: "array",
                    items: {
                      type: "object",
                      properties: {
                        scene_number: { type: "number" },
                        line_range_start: { type: "number" },
                        line_range_end: { type: "number" },
                        scene_description: { type: "string" },
                        setting: { type: "string" },
                        time_of_day: { type: "string" },
                        weather: { type: "string" },
                        mood: { type: "string" }
                      },
                      required: ["scene_number", "line_range_start", "line_range_end", "scene_description", "setting", "time_of_day", "weather", "mood"],
                      additionalProperties: false
                    }
                  }
                },
                required: ["scenes"],
                additionalProperties: false
              }
            }
          }
        ],
        tool_choice: { type: "function", function: { name: "extract_scenes" } }
      })
    });

    if (!aiResponse.ok) {
      const errorText = await aiResponse.text();
      console.error('AI API error:', aiResponse.status, errorText);
      throw new Error(`AI API error: ${aiResponse.status}`);
    }

    const aiData = await aiResponse.json();
    const toolCall = aiData.choices?.[0]?.message?.tool_calls?.[0];
    
    if (!toolCall) {
      throw new Error('No scenes extracted from AI');
    }

    const scenes = JSON.parse(toolCall.function.arguments).scenes;
    console.log(`Extracted ${scenes.length} scenes`);

    // Save scenes to database
    const sceneInserts = scenes.map((scene: any) => ({
      story_id: storyId,
      scene_number: scene.scene_number,
      line_range_start: scene.line_range_start,
      line_range_end: scene.line_range_end,
      scene_description: scene.scene_description,
      era: story.era,
      setting: scene.setting,
      time_of_day: scene.time_of_day,
      weather: scene.weather,
      mood: scene.mood,
    }));

    const { error: insertError } = await supabase
      .from('storyboard_scenes')
      .upsert(sceneInserts, { 
        onConflict: 'story_id,scene_number',
        ignoreDuplicates: false 
      });

    if (insertError) {
      console.error('Insert error:', insertError);
      throw insertError;
    }

    console.log('Scenes saved successfully');

    return new Response(
      JSON.stringify({ 
        success: true, 
        scenes: scenes.length 
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error: any) {
    console.error('Error in analyze-story-scenes function:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to analyze scenes' }),
      { 
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    );
  }
});
