/**
 * Local AI Client
 * Calls the local functions server for LM Studio AI operations
 */

import { getAIConfig } from './aiProvider';

export interface GeneratePortraitParams {
  actorId: string;
  fullName: string;
  role: string;
  era: string;
  ethnicity?: string;
  colorMode?: 'bw' | 'color';
  customization?: {
    age?: number;
    weathering?: number;
    detailLevel?: number;
    clothingStyle?: number;
    coverage?: number;
    fit?: string;
    styleProfile?: string;
    accentFocus?: string;
    textureDetail?: number;
    contrast?: number;
    rating?: string;
  };
  model?: string;
}

export interface GenerateStoryParams {
  prompt: string;
  actors?: Array<{ name: string; role: string }>;
  setting?: string;
  genre?: string;
  rating?: string;
  model?: string;
}

export interface AnalyzeScenesParams {
  storyText: string;
  model?: string;
}

export interface GenerateSceneImageryParams {
  scenePrompt: string;
  style?: string;
  model?: string;
}

export interface LocalAIResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
}

/**
 * Base fetch function for local AI server
 */
async function fetchLocal<T>(
  endpoint: string,
  method: 'GET' | 'POST' = 'GET',
  body?: unknown
): Promise<LocalAIResponse<T>> {
  const config = getAIConfig();
  const url = `${config.localUrl}${endpoint}`;

  try {
    const options: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
    };

    if (body && method === 'POST') {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(url, options);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `Request failed: ${response.status}`);
    }

    const data = await response.json();
    return { success: true, data };
  } catch (error) {
    console.error(`Local AI request failed (${endpoint}):`, error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Check server health
 */
export async function checkHealth(): Promise<LocalAIResponse<{
  status: string;
  lmStudioUrl: string;
  visionModel: string;
  textModel: string;
}>> {
  return fetchLocal('/health');
}

/**
 * Get available models from LM Studio
 */
export async function getModels(): Promise<LocalAIResponse<{
  data: Array<{ id: string; object: string; owned_by: string }>;
}>> {
  return fetchLocal('/models');
}

/**
 * Get/set server configuration
 */
export async function getConfig(): Promise<LocalAIResponse<{
  visionModel: string;
  textModel: string;
  ttsEnabled: boolean;
  ttsService: string | null;
}>> {
  return fetchLocal('/config');
}

export async function setConfig(config: {
  visionModel?: string;
  textModel?: string;
  ttsEnabled?: boolean;
  ttsService?: string;
}): Promise<LocalAIResponse<{ success: boolean; config: unknown }>> {
  return fetchLocal('/config', 'POST', config);
}

/**
 * Generate actor portrait using local LM Studio
 */
export async function generatePortrait(
  params: GeneratePortraitParams
): Promise<LocalAIResponse<{
  actorId: string;
  prompt: string;
  imageUrl: string | null;
  textResponse: string;
  model: string;
  note: string;
}>> {
  return fetchLocal('/generate-actor-portrait', 'POST', params);
}

/**
 * Generate story text using local LM Studio
 */
export async function generateStory(
  params: GenerateStoryParams
): Promise<LocalAIResponse<{
  story: string;
  model: string;
}>> {
  return fetchLocal('/generate-story', 'POST', params);
}

/**
 * Analyze story for scene extraction
 */
export async function analyzeScenes(
  params: AnalyzeScenesParams
): Promise<LocalAIResponse<{
  analysis: string;
  model: string;
}>> {
  return fetchLocal('/analyze-story-scenes', 'POST', params);
}

/**
 * Generate scene imagery
 */
export async function generateSceneImagery(
  params: GenerateSceneImageryParams
): Promise<LocalAIResponse<{
  imageData: string;
  model: string;
}>> {
  return fetchLocal('/generate-scene-imagery', 'POST', params);
}

/**
 * Text-to-speech (if configured)
 */
export async function textToSpeech(
  text: string,
  voiceId?: string
): Promise<LocalAIResponse<{
  success: boolean;
  message?: string;
  audioUrl?: string;
}>> {
  return fetchLocal('/text-to-speech', 'POST', { text, voiceId });
}

/**
 * Get actors from local database
 */
export async function getActors(): Promise<LocalAIResponse<{
  data: unknown[];
  error: string | null;
}>> {
  return fetchLocal('/actors');
}

/**
 * Get actor by ID from local database
 */
export async function getActor(id: string): Promise<LocalAIResponse<{
  data: unknown;
  error: string | null;
}>> {
  return fetchLocal(`/actors/${id}`);
}
