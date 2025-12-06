import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { genre, theme, characterCount = 3, era = '1870s' } = await req.json();

    if (!genre || !theme) {
      throw new Error('Genre and theme are required');
    }

    const LOVABLE_API_KEY = Deno.env.get('LOVABLE_API_KEY');
    if (!LOVABLE_API_KEY) {
      throw new Error('LOVABLE_API_KEY not configured');
    }

    const systemPrompt = `You are a creative writer specializing in Old West and Native American historical fiction. 
Generate story templates with authentic dialogue and character interactions. 
Focus on respectful, historically-informed narratives that honor Native American cultures and frontier history.`;

    const userPrompt = `Create a story template for:
Genre: ${genre}
Theme: ${theme}
Era: ${era}
Number of Characters: ${characterCount}

Requirements:
1. Create a compelling title (max 60 characters)
2. Write a brief description (max 150 characters)
3. Generate ${characterCount} unique characters with appropriate roles, first names, and last names
4. Create 5-8 dialogue lines that tell a complete micro-story
5. Each character should speak at least once
6. Use authentic Old West and Native American naming conventions
7. Ensure dialogue is period-appropriate and culturally respectful

Return ONLY a JSON object with this structure (no markdown, no code blocks):
{
  "title": "string",
  "description": "string",
  "genre": "string",
  "era": "string",
  "icon_name": "Heart|Mountain|Users|BookOpen",
  "lines": [
    {
      "actor_role": "string",
      "actor_first_name": "string", 
      "actor_last_name": "string",
      "text": "string"
    }
  ]
}`;

    console.log('Generating template with AI...');

    const response = await fetch('https://ai.gateway.lovable.dev/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${LOVABLE_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'google/gemini-2.5-flash',
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: userPrompt }
        ],
        temperature: 0.8,
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
    const content = data.choices[0].message.content;

    console.log('AI Response:', content);

    // Parse the JSON response
    let template;
    try {
      // Remove markdown code blocks if present
      const cleanContent = content.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
      template = JSON.parse(cleanContent);
    } catch (parseError) {
      console.error('JSON parse error:', parseError, 'Content:', content);
      throw new Error('Failed to parse AI response as JSON');
    }

    // Validate template structure
    if (!template.title || !template.lines || !Array.isArray(template.lines)) {
      throw new Error('Invalid template structure from AI');
    }

    // Add line numbers
    template.lines = template.lines.map((line: any, index: number) => ({
      ...line,
      line_number: index + 1
    }));

    return new Response(
      JSON.stringify({ template }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );
  } catch (error) {
    console.error('Error generating template:', error);
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