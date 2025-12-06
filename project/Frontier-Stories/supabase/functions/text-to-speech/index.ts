import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { text, voiceId, voiceSettings } = await req.json();

    if (!text) {
      throw new Error('Text is required');
    }

    const ELEVENLABS_API_KEY = Deno.env.get('ELEVENLABS_API_KEY');
    if (!ELEVENLABS_API_KEY) {
      throw new Error('ElevenLabs API key not configured');
    }

    // Map legacy sample IDs from seed data to real ElevenLabs voices
    const voiceIdMap: Record<string, string> = {
      'sample-voice-blackhawk': 'bIHbv24MWmeRgasZH58o', // Will
      'sample-voice-sarahmccoy': 'EXAVITQu4vr4xnSDxMaL', // Sarah
      'sample-voice-jakemorrison': 'TX3LPaxmHKxFdv7VOQHJ', // Liam
      'sample-voice-runningbear': 'JBFqnCBsd6RMkjVDRZzb', // George
    };

    const normalizedVoiceId = voiceId && voiceIdMap[voiceId] ? voiceIdMap[voiceId] : voiceId;

    // Use default voice if not provided
    const selectedVoiceId = normalizedVoiceId || '9BWtsMINqrJLrRacOk9x'; // Aria by default
    
    // Default voice settings optimized for storytelling
    const settings = voiceSettings || {
      stability: 0.5,
      similarity_boost: 0.75,
      style: 0.5,
      use_speaker_boost: true
    };

    console.log(`Generating speech with voice ID: ${selectedVoiceId}`);

    // Generate speech using ElevenLabs API
    const response = await fetch(
      `https://api.elevenlabs.io/v1/text-to-speech/${selectedVoiceId}`,
      {
        method: 'POST',
        headers: {
          'Accept': 'audio/mpeg',
          'Content-Type': 'application/json',
          'xi-api-key': ELEVENLABS_API_KEY,
        },
        body: JSON.stringify({
          text: text,
          model_id: 'eleven_multilingual_v2',
          voice_settings: settings,
        }),
      }
    );

    if (!response.ok) {
      const error = await response.text();
      console.error('ElevenLabs API error:', error);
      throw new Error(`ElevenLabs API error: ${response.status} - ${error}`);
    }

    // Get the audio data
    const audioData = await response.arrayBuffer();
    
    console.log(`Successfully generated ${audioData.byteLength} bytes of audio`);

    // Return the audio data
    return new Response(audioData, {
      headers: {
        ...corsHeaders,
        'Content-Type': 'audio/mpeg',
      },
    });
  } catch (error) {
    console.error('Error in text-to-speech function:', error);
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
