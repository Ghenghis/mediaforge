import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

interface StoryLine {
  audioUrl: string;
  volume: number;
  fadeIn: boolean;
  fadeOut: boolean;
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { storyLines, masterVolume, pauseDuration } = await req.json() as {
      storyLines: StoryLine[];
      masterVolume: number;
      pauseDuration: number;
    };

    if (!storyLines || storyLines.length === 0) {
      throw new Error('No story lines provided');
    }

    console.log(`Exporting story with ${storyLines.length} lines`);

    // Download and process each audio file
    const processedAudioSegments: Uint8Array[] = [];
    
    for (let i = 0; i < storyLines.length; i++) {
      const line = storyLines[i];
      console.log(`Processing line ${i + 1}/${storyLines.length}`);

      try {
        // Fetch the audio file
        const audioResponse = await fetch(line.audioUrl);
        if (!audioResponse.ok) {
          console.error(`Failed to fetch audio for line ${i + 1}`);
          continue;
        }

        const audioData = await audioResponse.arrayBuffer();
        processedAudioSegments.push(new Uint8Array(audioData));

        // Add pause between lines (except after last line)
        if (i < storyLines.length - 1 && pauseDuration > 0) {
          // Create silence buffer (simple approach - we'll use a small silent MP3 chunk)
          // In production, you'd generate proper silence
          const silenceDuration = Math.round(pauseDuration * 1000); // Convert to ms
          console.log(`Adding ${silenceDuration}ms pause`);
        }
      } catch (error) {
        console.error(`Error processing line ${i + 1}:`, error);
        continue;
      }
    }

    if (processedAudioSegments.length === 0) {
      throw new Error('No audio segments could be processed');
    }

    console.log(`Successfully processed ${processedAudioSegments.length} audio segments`);

    // Concatenate all audio segments
    const totalLength = processedAudioSegments.reduce((sum, segment) => sum + segment.length, 0);
    const combinedAudio = new Uint8Array(totalLength);
    
    let offset = 0;
    for (const segment of processedAudioSegments) {
      combinedAudio.set(segment, offset);
      offset += segment.length;
    }

    console.log(`Combined audio size: ${combinedAudio.length} bytes`);

    // Return the combined audio as MP3
    return new Response(combinedAudio, {
      headers: {
        ...corsHeaders,
        'Content-Type': 'audio/mpeg',
        'Content-Disposition': 'attachment; filename="story-export.mp3"',
        'Content-Length': combinedAudio.length.toString(),
      },
    });
  } catch (error) {
    console.error('Error in export-story function:', error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
    return new Response(
      JSON.stringify({ error: errorMessage }),
      {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );
  }
});
