/**
 * Frontier-Stories Local Functions Server
 * Handles AI functions with LM Studio integration for uncensored image/text generation
 */

import express from 'express';
import cors from 'cors';
import fetch from 'node-fetch';
import { createClient } from '@supabase/supabase-js';
import pg from 'pg';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
const { Pool } = pg;

// ES Module dirname equivalent
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 54321;

// LM Studio configuration (for text generation)
const LM_STUDIO_URL = process.env.LM_STUDIO_URL || 'http://host.docker.internal:1234';
const LM_STUDIO_VISION_MODEL = process.env.LM_STUDIO_VISION_MODEL || 'default';
const LM_STUDIO_TEXT_MODEL = process.env.LM_STUDIO_TEXT_MODEL || 'default';

// Automatic1111/ComfyUI configuration (for image generation)
const A1111_URL = process.env.A1111_URL || 'http://host.docker.internal:7861';
const COMFYUI_URL = process.env.COMFYUI_URL || 'http://host.docker.internal:8188';
const IMAGE_GEN_BACKEND = process.env.IMAGE_GEN_BACKEND || 'a1111'; // 'a1111' or 'comfyui'

// Image storage path
const IMAGE_STORAGE_PATH = process.env.IMAGE_STORAGE_PATH || path.join(__dirname, 'storage', 'images');

// Ensure storage directory exists
if (!fs.existsSync(IMAGE_STORAGE_PATH)) {
  fs.mkdirSync(IMAGE_STORAGE_PATH, { recursive: true });
  console.log(`Created image storage directory: ${IMAGE_STORAGE_PATH}`);
}

// Database configuration
const DATABASE_URL = process.env.DATABASE_URL;
const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY;

// Middleware
app.use(cors());
app.use(express.json({ limit: '50mb' }));

// Serve stored images statically
app.use('/images', express.static(IMAGE_STORAGE_PATH));

/**
 * Save image to local storage and return URL
 * @param {Buffer|string} imageData - Base64 image data or buffer
 * @param {string} filename - Filename without extension
 * @returns {Promise<{filePath: string, url: string}>}
 */
async function saveImageToStorage(imageData, filename) {
  const timestamp = Date.now();
  const safeFilename = `${filename.replace(/[^a-zA-Z0-9-_]/g, '_')}-${timestamp}.png`;
  const filePath = path.join(IMAGE_STORAGE_PATH, safeFilename);
  
  let buffer;
  if (typeof imageData === 'string') {
    // Remove data URL prefix if present
    const base64Data = imageData.replace(/^data:image\/\w+;base64,/, '');
    buffer = Buffer.from(base64Data, 'base64');
  } else {
    buffer = imageData;
  }
  
  await fs.promises.writeFile(filePath, buffer);
  
  // Return relative URL for serving
  const url = `/images/${safeFilename}`;
  console.log(`Saved image: ${filePath}`);
  
  return { filePath, url, filename: safeFilename };
}

// Health check endpoint
app.get('/health', async (req, res) => {
  let lmStudioStatus = 'unknown';
  let modelsLoaded = [];
  
  try {
    const lmResponse = await fetch(`${LM_STUDIO_URL}/v1/models`, {
      signal: AbortSignal.timeout(3000)
    });
    if (lmResponse.ok) {
      const data = await lmResponse.json();
      modelsLoaded = data.data?.map(m => m.id) || [];
      lmStudioStatus = modelsLoaded.length > 0 ? 'ready' : 'no_models_loaded';
    } else {
      lmStudioStatus = 'error';
    }
  } catch (e) {
    lmStudioStatus = 'disconnected';
  }
  
  res.json({ 
    status: 'healthy', 
    timestamp: new Date().toISOString(),
    lmStudioUrl: LM_STUDIO_URL,
    lmStudioStatus,
    modelsLoaded,
    visionModel: modelConfig.visionModel,
    textModel: modelConfig.textModel,
    imageStoragePath: IMAGE_STORAGE_PATH
  });
});

// Detailed LM Studio status check
app.get('/lm-studio/status', async (req, res) => {
  try {
    const modelsResponse = await fetch(`${LM_STUDIO_URL}/v1/models`, {
      signal: AbortSignal.timeout(5000)
    });
    
    if (!modelsResponse.ok) {
      throw new Error(`LM Studio returned ${modelsResponse.status}`);
    }
    
    const modelsData = await modelsResponse.json();
    const models = modelsData.data || [];
    
    // Categorize models by type
    const categorizedModels = {
      text: [],
      vision: [],
      image: [],
      unknown: []
    };
    
    for (const model of models) {
      const id = model.id.toLowerCase();
      if (id.includes('flux') || id.includes('stable-diffusion') || id.includes('sd') || id.includes('sdxl') || id.includes('chroma')) {
        categorizedModels.image.push(model.id);
      } else if (id.includes('vision') || id.includes('llava') || id.includes('gemma') && id.includes('vision')) {
        categorizedModels.vision.push(model.id);
      } else if (id.includes('llama') || id.includes('mistral') || id.includes('wizard') || id.includes('qwen') || id.includes('phi')) {
        categorizedModels.text.push(model.id);
      } else {
        categorizedModels.unknown.push(model.id);
      }
    }
    
    res.json({
      connected: true,
      url: LM_STUDIO_URL,
      totalModels: models.length,
      models: categorizedModels,
      allModels: models.map(m => ({ id: m.id, object: m.object })),
      currentConfig: modelConfig
    });
  } catch (error) {
    res.status(503).json({
      connected: false,
      url: LM_STUDIO_URL,
      error: error.message,
      hint: 'Ensure LM Studio is running and has the local server enabled on port 1234'
    });
  }
});

// Get available LM Studio models
app.get('/models', async (req, res) => {
  try {
    const response = await fetch(`${LM_STUDIO_URL}/v1/models`);
    if (!response.ok) {
      throw new Error(`LM Studio not available: ${response.status}`);
    }
    const data = await response.json();
    res.json(data);
  } catch (error) {
    console.error('Error fetching models:', error);
    res.status(500).json({ 
      error: 'Failed to fetch models from LM Studio',
      details: error.message,
      hint: 'Make sure LM Studio is running on port 1234'
    });
  }
});

// Generate actor portrait using Automatic1111 or ComfyUI for ACTUAL image generation
app.post('/generate-actor-portrait', async (req, res) => {
  try {
    const { 
      actorId, 
      fullName, 
      role, 
      era, 
      ethnicity, 
      colorMode = 'color',
      customization = {},
      model // Optional: override default model
    } = req.body;

    if (!actorId || !fullName || !role) {
      return res.status(400).json({ error: 'Actor ID, full name, and role are required' });
    }
    
    // Fetch actor metadata from database to get outfit/pose/expression details
    let actorMetadata = {};
    try {
      const { rows } = await query('SELECT metadata FROM public.actors WHERE id = $1', [actorId]);
      if (rows.length > 0 && rows[0].metadata) {
        actorMetadata = rows[0].metadata;
        console.log(`Loaded metadata for ${fullName}:`, JSON.stringify(actorMetadata).substring(0, 200));
      }
    } catch (dbError) {
      console.warn('Could not fetch actor metadata:', dbError.message);
    }
    
    // Extract styling from actor metadata (these are our sexy model outfits!)
    const outfit = actorMetadata.outfit || 'elegant traditional Native American attire';
    const poseStyle = actorMetadata.pose_style || 'confident natural pose';
    const expressionStyle = actorMetadata.expression_style || 'alluring gaze';
    const lightingStyle = actorMetadata.lighting_style || 'golden hour soft lighting';
    const backgroundStyle = actorMetadata.background_style || 'natural outdoor backdrop';
    const framing = actorMetadata.framing || 'portrait waist-up';
    
    // Build detailed prompt for uncensored image generation
    const age = actorMetadata.age || customization.age || 25;
    const tribe = actorMetadata.tribe || '';
    const hair = actorMetadata.hair || 'long dark hair';
    const beauty = actorMetadata.beauty || 'stunning';

    const ethnicityGuide = tribe ? `${tribe} Native American` : (ethnicity || 'Native American');
    const ageDesc = age < 22 ? 'young' : age < 30 ? 'young adult' : age < 45 ? 'mature' : 'distinguished';

    // Build the Stable Diffusion optimized prompt
    const prompt = `masterpiece, best quality, highly detailed, professional fashion photography, 
${beauty} ${ageDesc} ${ethnicityGuide} woman, ${role}, 
${hair}, beautiful face, perfect features, flawless skin,
wearing ${outfit},
${poseStyle}, ${expressionStyle},
${lightingStyle}, ${backgroundStyle}, ${framing},
8k uhd, dslr, high quality, film grain, Fujifilm XT3, sharp focus, 
sensual editorial fashion photography, glamorous, alluring`;

    // Negative prompt to avoid bad outputs
    const negativePrompt = `lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, artist name, deformed, ugly, duplicate, morbid, mutilated, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, mutation, disfigured, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, long neck, censored`;

    console.log(`🎨 Generating portrait for ${fullName} using A1111`);
    console.log(`📝 Prompt: ${prompt.substring(0, 200)}...`);

    // Call Automatic1111 API for actual image generation
    const a1111Response = await fetch(`${A1111_URL}/sdapi/v1/txt2img`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt: prompt,
        negative_prompt: negativePrompt,
        steps: 30,
        cfg_scale: 7,
        width: 768,
        height: 1024,
        sampler_name: 'DPM++ 2M Karras',
        seed: -1, // Random seed
        batch_size: 1,
        n_iter: 1,
        restore_faces: true,
        enable_hr: false, // Set to true for high-res fix
        // hr_scale: 1.5,
        // hr_upscaler: "Latent",
        // denoising_strength: 0.5,
      })
    });

    if (!a1111Response.ok) {
      const errorText = await a1111Response.text();
      console.error('A1111 error:', a1111Response.status, errorText);
      throw new Error(`Automatic1111 error: ${a1111Response.status} - ${errorText}`);
    }

    const a1111Data = await a1111Response.json();
    
    // A1111 returns images as base64 in the 'images' array
    const base64Image = a1111Data.images?.[0];
    
    let savedImage = null;
    let imageUrl = null;
    
    if (base64Image) {
      try {
        // Convert to data URL format and save
        const imageDataUrl = `data:image/png;base64,${base64Image}`;
        savedImage = await saveImageToStorage(imageDataUrl, `portrait-${actorId}`);
        imageUrl = savedImage.url;
        console.log(`✅ Saved portrait image: ${savedImage.filename}`);
        
        // Update actor record in database with new image URL
        if (pool) {
          const fullImageUrl = `http://localhost:${PORT}${imageUrl}`;
          await query(
            'UPDATE public.actors SET image_url = $1, updated_at = NOW() WHERE id = $2',
            [fullImageUrl, actorId]
          );
          console.log(`📝 Updated database for actor ${actorId}`);
        }
      } catch (saveError) {
        console.error('Error saving image:', saveError);
      }
    } else {
      console.error('❌ No image returned from A1111');
    }
    
    res.json({ 
      success: !!imageUrl,
      actorId,
      fullName,
      prompt: prompt.substring(0, 500),
      imageUrl: imageUrl ? `http://localhost:${PORT}${imageUrl}` : null,
      backend: 'automatic1111',
      note: imageUrl ? '🎨 Image generated and saved!' : '❌ No image generated - check A1111 is running'
    });

  } catch (error) {
    console.error('Error generating portrait:', error);
    res.status(500).json({ 
      success: false, 
      error: error.message,
      hint: 'Make sure Automatic1111 is running on port 7860 with --api flag'
    });
  }
});

// Upload and save an externally generated image for an actor
app.post('/upload-portrait', async (req, res) => {
  try {
    const { actorId, imageData, filename } = req.body;
    
    if (!actorId || !imageData) {
      return res.status(400).json({ error: 'Actor ID and image data are required' });
    }
    
    const savedImage = await saveImageToStorage(imageData, filename || `portrait-${actorId}`);
    const fullUrl = `http://localhost:${PORT}${savedImage.url}`;
    
    // Update actor record
    if (pool) {
      await query(
        'UPDATE public.actors SET image_url = $1, updated_at = NOW() WHERE id = $2',
        [fullUrl, actorId]
      );
    }
    
    res.json({
      success: true,
      actorId,
      imageUrl: fullUrl,
      filename: savedImage.filename
    });
  } catch (error) {
    console.error('Error uploading portrait:', error);
    res.status(500).json({ error: error.message });
  }
});

// Generate story text using LM Studio text model
app.post('/generate-story', async (req, res) => {
  try {
    const { 
      prompt, 
      actors,
      setting,
      genre,
      rating = 'adult_21_plus',
      model // Optional: override default text model
    } = req.body;

    const useModel = model || LM_STUDIO_TEXT_MODEL;

    // Build story generation prompt
    const actorList = actors?.map(a => `${a.name} (${a.role})`).join(', ') || 'unspecified characters';
    
    const systemPrompt = rating === 'adult_21_plus'
      ? `You are a creative writer specializing in adult fiction. Write sensual, provocative, and explicit content as requested. No restrictions on adult themes.`
      : `You are a creative writer. Write engaging stories with the specified tone and content.`;

    const userPrompt = `Setting: ${setting || 'Old West frontier'}
Genre: ${genre || 'Western drama'}
Characters: ${actorList}
Rating: ${rating}

Story prompt: ${prompt}

Write a compelling story scene with vivid descriptions and authentic dialogue.`;

    console.log(`Generating story using model: ${useModel}`);

    const response = await fetch(`${LM_STUDIO_URL}/v1/chat/completions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: useModel,
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: userPrompt }
        ],
        max_tokens: 4096,
        temperature: 0.9,
        stream: false
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`LM Studio error: ${response.status} - ${errorText}`);
    }

    const data = await response.json();
    const storyText = data.choices?.[0]?.message?.content;

    res.json({ 
      success: true,
      story: storyText,
      model: useModel
    });

  } catch (error) {
    console.error('Error generating story:', error);
    res.status(500).json({ error: error.message });
  }
});

// Analyze story scenes for image generation
app.post('/analyze-story-scenes', async (req, res) => {
  try {
    const { storyText, model } = req.body;
    const useModel = model || LM_STUDIO_TEXT_MODEL;

    const response = await fetch(`${LM_STUDIO_URL}/v1/chat/completions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: useModel,
        messages: [
          {
            role: 'system',
            content: 'You are an expert at analyzing stories and identifying key visual scenes. For each scene, provide a detailed image generation prompt.'
          },
          {
            role: 'user',
            content: `Analyze this story and identify 3-5 key visual scenes. For each scene, provide:
1. Scene title
2. Characters present
3. Detailed image generation prompt

Story:
${storyText}`
          }
        ],
        max_tokens: 2048,
        temperature: 0.7
      })
    });

    if (!response.ok) {
      throw new Error(`LM Studio error: ${response.status}`);
    }

    const data = await response.json();
    res.json({ 
      success: true,
      analysis: data.choices?.[0]?.message?.content,
      model: useModel
    });

  } catch (error) {
    console.error('Error analyzing scenes:', error);
    res.status(500).json({ error: error.message });
  }
});

// Generate scene imagery
app.post('/generate-scene-imagery', async (req, res) => {
  try {
    const { scenePrompt, style, model } = req.body;
    const useModel = model || LM_STUDIO_VISION_MODEL;

    const fullPrompt = `${scenePrompt}
Style: ${style || 'Cinematic Old West, dramatic lighting'}
Quality: Ultra high resolution, photorealistic`;

    const response = await fetch(`${LM_STUDIO_URL}/v1/chat/completions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: useModel,
        messages: [{ role: 'user', content: fullPrompt }],
        max_tokens: 4096,
        temperature: 0.8
      })
    });

    if (!response.ok) {
      throw new Error(`LM Studio error: ${response.status}`);
    }

    const data = await response.json();
    res.json({ 
      success: true,
      imageData: data.choices?.[0]?.message?.content,
      model: useModel
    });

  } catch (error) {
    console.error('Error generating scene:', error);
    res.status(500).json({ error: error.message });
  }
});

// Text-to-speech placeholder (requires separate TTS model or service)
app.post('/text-to-speech', async (req, res) => {
  try {
    const { text, voiceId } = req.body;
    
    // For local TTS, you might use:
    // - Coqui TTS
    // - Piper TTS
    // - XTTS
    // This is a placeholder that returns info about TTS configuration needed
    
    res.json({
      success: false,
      message: 'Local TTS not yet configured',
      hint: 'Configure a local TTS service like Coqui TTS or Piper in the settings',
      text,
      voiceId
    });

  } catch (error) {
    console.error('Error in TTS:', error);
    res.status(500).json({ error: error.message });
  }
});

// Configuration endpoint - get/set model preferences
let modelConfig = {
  visionModel: LM_STUDIO_VISION_MODEL,
  textModel: LM_STUDIO_TEXT_MODEL,
  ttsEnabled: false,
  ttsService: null
};

app.get('/config', (req, res) => {
  res.json(modelConfig);
});

app.post('/config', (req, res) => {
  const { visionModel, textModel, ttsEnabled, ttsService } = req.body;
  
  if (visionModel) modelConfig.visionModel = visionModel;
  if (textModel) modelConfig.textModel = textModel;
  if (typeof ttsEnabled === 'boolean') modelConfig.ttsEnabled = ttsEnabled;
  if (ttsService) modelConfig.ttsService = ttsService;
  
  console.log('Updated model config:', modelConfig);
  res.json({ success: true, config: modelConfig });
});

// Database client setup
const pool = new Pool({
  connectionString: DATABASE_URL,
});

// Helper function to query database
async function query(text, params) {
  const start = Date.now();
  try {
    const res = await pool.query(text, params);
    const duration = Date.now() - start;
    console.log('Executed query', { text, duration, rows: res.rowCount });
    return res;
  } catch (error) {
    console.error('Database query error:', error);
    throw error;
  }
}

// Get all actors
app.get('/actors', async (req, res) => {
  try {
    const { rows } = await query('SELECT * FROM public.actors ORDER BY created_at DESC');
    res.json({ data: rows, error: null });
  } catch (error) {
    console.error('Error fetching actors:', error);
    res.status(500).json({ data: null, error: error.message });
  }
});

// Get actor by ID
app.get('/actors/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { rows } = await query('SELECT * FROM public.actors WHERE id = $1', [id]);
    
    if (rows.length === 0) {
      return res.status(404).json({ data: null, error: 'Actor not found' });
    }
    
    res.json({ data: rows[0], error: null });
  } catch (error) {
    console.error('Error fetching actor:', error);
    res.status(500).json({ data: null, error: error.message });
  }
});

// Create new actor
app.post('/actors', async (req, res) => {
  try {
    const { first_name, last_name, role, era = '1870s', ethnicity, bio, voice_id, voice_name, image_url } = req.body;
    
    if (!first_name || !last_name || !role) {
      return res.status(400).json({ data: null, error: 'First name, last name, and role are required' });
    }
    
    const { rows } = await query(
      `INSERT INTO public.actors (first_name, last_name, role, era, ethnicity, bio, voice_id, voice_name, image_url)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
       RETURNING *`,
      [first_name, last_name, role, era, ethnicity, bio, voice_id, voice_name, image_url]
    );
    
    res.json({ data: rows[0], error: null });
  } catch (error) {
    console.error('Error creating actor:', error);
    res.status(500).json({ data: null, error: error.message });
  }
});

// Update actor
app.put('/actors/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { first_name, last_name, role, era, ethnicity, bio, voice_id, voice_name, image_url, is_active } = req.body;
    
    const { rows } = await query(
      `UPDATE public.actors 
       SET first_name = $1, last_name = $2, role = $3, era = $4, ethnicity = $5, bio = $6, 
           voice_id = $7, voice_name = $8, image_url = $9, is_active = $10, updated_at = NOW()
       WHERE id = $11
       RETURNING *`,
      [first_name, last_name, role, era, ethnicity, bio, voice_id, voice_name, image_url, is_active, id]
    );
    
    if (rows.length === 0) {
      return res.status(404).json({ data: null, error: 'Actor not found' });
    }
    
    res.json({ data: rows[0], error: null });
  } catch (error) {
    console.error('Error updating actor:', error);
    res.status(500).json({ data: null, error: error.message });
  }
});

// Delete actor
app.delete('/actors/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { rows } = await query('DELETE FROM public.actors WHERE id = $1 RETURNING *', [id]);
    
    if (rows.length === 0) {
      return res.status(404).json({ data: null, error: 'Actor not found' });
    }
    
    res.json({ data: rows[0], error: null });
  } catch (error) {
    console.error('Error deleting actor:', error);
    res.status(500).json({ data: null, error: error.message });
  }
});

// ============================================================
// ADDITIONAL ENDPOINTS - Placeholders for cloud functions
// ============================================================

// Generate template (story template generation)
app.post('/generate-template', async (req, res) => {
  console.log('📝 Generate template requested:', req.body);
  try {
    const { genre, theme, era, style } = req.body;
    const useModel = modelConfig.textModel || LM_STUDIO_TEXT_MODEL;
    
    const prompt = `Generate a creative story template for the Old West era.
Genre: ${genre || 'Western Drama'}
Theme: ${theme || 'Adventure'}
Era: ${era || '1870s'}
Style: ${style || 'Classic Western'}

Provide a detailed story template with:
1. Title
2. Setting description
3. Main character archetype
4. Plot outline (3-5 key beats)
5. Tone and mood`;

    const response = await fetch(`${LM_STUDIO_URL}/v1/chat/completions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: useModel,
        messages: [{ role: 'user', content: prompt }],
        temperature: 0.8,
        max_tokens: 1000
      })
    });

    if (!response.ok) {
      throw new Error(`LM Studio error: ${response.status}`);
    }

    const result = await response.json();
    res.json({ 
      success: true, 
      template: result.choices?.[0]?.message?.content || 'Template generated',
      provider: 'local'
    });
  } catch (error) {
    console.error('Template generation error:', error);
    res.json({ success: false, error: error.message });
  }
});

// Colorize portrait (AI colorization)
app.post('/colorize-portrait', async (req, res) => {
  console.log('🎨 Colorize portrait requested:', req.body);
  const { actorId, imageUrl, era, fullName, role } = req.body;
  
  // For now, return success - actual colorization would need an image model
  res.json({ 
    success: true, 
    message: `Colorization queued for ${fullName || actorId}. This feature requires an image-to-image model.`,
    colorizedUrl: imageUrl, // Return original for now
    provider: 'local'
  });
});

// Style transfer
app.post('/style-transfer', async (req, res) => {
  console.log('🎭 Style transfer requested:', req.body);
  const { actorId, imageUrl, style } = req.body;
  
  res.json({ 
    success: true, 
    message: `Style transfer (${style || 'default'}) queued. This feature requires a style transfer model.`,
    styledUrl: imageUrl,
    provider: 'local'
  });
});

// Voice design (AI voice generation)
app.post('/voice-design', async (req, res) => {
  console.log('🎤 Voice design requested:', req.body);
  const { description, characterBio } = req.body;
  
  res.json({ 
    success: true, 
    message: 'Voice design requires an external TTS service like ElevenLabs.',
    voiceId: 'placeholder-voice-id',
    provider: 'local'
  });
});

// Voice clone
app.post('/voice-clone', async (req, res) => {
  console.log('🎙️ Voice clone requested');
  
  res.json({ 
    success: true, 
    message: 'Voice cloning requires an external service like ElevenLabs.',
    voiceId: 'placeholder-cloned-voice',
    provider: 'local'
  });
});

// Generate scenery
app.post('/generate-scenery', async (req, res) => {
  console.log('🏜️ Generate scenery requested:', req.body);
  const { storyId, era, location, mood } = req.body;
  
  try {
    const useModel = modelConfig.visionModel || LM_STUDIO_VISION_MODEL;
    const prompt = `Create a dramatic ${era || '1870s'} Old West landscape scene.
Location: ${location || 'Western frontier'}
Mood: ${mood || 'Epic and cinematic'}
Style: Photorealistic western scenery, golden hour lighting, vast landscapes.`;

    // This would call an image generation model if available
    res.json({ 
      success: true, 
      message: 'Scenery generation queued',
      prompt: prompt,
      provider: 'local'
    });
  } catch (error) {
    res.json({ success: false, error: error.message });
  }
});

// Export story (audio/video export)
app.post('/export-story', async (req, res) => {
  console.log('📦 Export story requested:', req.body);
  const { storyLines, format } = req.body;
  
  res.json({ 
    success: true, 
    message: `Story export (${format || 'audio'}) queued. ${storyLines?.length || 0} lines to process.`,
    exportUrl: null,
    provider: 'local'
  });
});

// ============================================================
// IMAGE GENERATION BACKEND API - A1111/ComfyUI Integration
// ============================================================

// Get available SD models from A1111
app.get('/image-gen/models', async (req, res) => {
  try {
    const response = await fetch(`${A1111_URL}/sdapi/v1/sd-models`);
    if (response.ok) {
      const models = await response.json();
      res.json({ 
        backend: 'a1111',
        models: models.map(m => m.model_name || m.title),
        status: 'connected'
      });
    } else {
      res.json({ backend: 'a1111', models: ['default'], status: 'error' });
    }
  } catch (error) {
    res.json({ backend: 'a1111', models: ['default'], status: 'disconnected' });
  }
});

// Get available samplers from A1111
app.get('/image-gen/samplers', async (req, res) => {
  try {
    const response = await fetch(`${A1111_URL}/sdapi/v1/samplers`);
    if (response.ok) {
      const samplers = await response.json();
      res.json({ samplers: samplers.map(s => s.name) });
    } else {
      res.json({ samplers: ['DPM++ 2M Karras', 'Euler a', 'DDIM'] });
    }
  } catch {
    res.json({ samplers: ['DPM++ 2M Karras', 'Euler a', 'DDIM'] });
  }
});

// Get current A1111 options/settings
app.get('/image-gen/options', async (req, res) => {
  try {
    const response = await fetch(`${A1111_URL}/sdapi/v1/options`);
    if (response.ok) {
      const options = await response.json();
      res.json({ 
        currentModel: options.sd_model_checkpoint,
        status: 'connected'
      });
    } else {
      res.json({ status: 'error' });
    }
  } catch {
    res.json({ status: 'disconnected' });
  }
});

// Set A1111 model
app.post('/image-gen/set-model', async (req, res) => {
  try {
    const { model } = req.body;
    const response = await fetch(`${A1111_URL}/sdapi/v1/options`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sd_model_checkpoint: model })
    });
    if (response.ok) {
      res.json({ success: true, model });
    } else {
      res.json({ success: false, error: 'Failed to set model' });
    }
  } catch (error) {
    res.json({ success: false, error: error.message });
  }
});

// Check image generation backend status
app.get('/image-gen/status', async (req, res) => {
  const status = {
    a1111: { url: A1111_URL, status: 'unknown' },
    comfyui: { url: COMFYUI_URL, status: 'unknown' },
    activeBackend: IMAGE_GEN_BACKEND
  };

  // Check A1111
  try {
    const a1111Check = await fetch(`${A1111_URL}/sdapi/v1/options`, { 
      signal: AbortSignal.timeout(3000) 
    });
    status.a1111.status = a1111Check.ok ? 'connected' : 'error';
  } catch {
    status.a1111.status = 'disconnected';
  }

  // Check ComfyUI
  try {
    const comfyCheck = await fetch(`${COMFYUI_URL}/system_stats`, { 
      signal: AbortSignal.timeout(3000) 
    });
    status.comfyui.status = comfyCheck.ok ? 'connected' : 'error';
  } catch {
    status.comfyui.status = 'disconnected';
  }

  res.json(status);
});

// Get generation progress from A1111
app.get('/image-gen/progress', async (req, res) => {
  try {
    const response = await fetch(`${A1111_URL}/sdapi/v1/progress`);
    if (response.ok) {
      const progress = await response.json();
      res.json(progress);
    } else {
      res.json({ progress: 0, state: { job: '' } });
    }
  } catch {
    res.json({ progress: 0, state: { job: '' } });
  }
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`
╔═══════════════════════════════════════════════════════════╗
║        Frontier-Stories Functions Server                  ║
╠═══════════════════════════════════════════════════════════╣
║  Port: ${PORT}                                              ║
║  LM Studio: ${LM_STUDIO_URL.padEnd(38)}║
║  A1111: ${A1111_URL.padEnd(43)}║
║  ComfyUI: ${COMFYUI_URL.padEnd(41)}║
║  Image Backend: ${IMAGE_GEN_BACKEND.padEnd(35)}║
╚═══════════════════════════════════════════════════════════╝
  `);
});
