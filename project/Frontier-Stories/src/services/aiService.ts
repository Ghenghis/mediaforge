/**
 * Unified AI Service
 * Routes AI requests to either cloud (Supabase) or local (LM Studio) based on provider setting
 */

import { supabase } from "@/integrations/supabase/client";
import { getAIConfig } from "./aiProvider";
import * as localAI from "./localAIClient";

export interface GeneratePortraitRequest {
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
}

export interface GenerateStoryRequest {
  prompt: string;
  actors?: Array<{ name: string; role: string }>;
  setting?: string;
  genre?: string;
  rating?: string;
}

export interface GenerateTemplateRequest {
  genre: string;
  theme: string;
  characterCount?: number;
  era?: string;
}

export interface AIResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  provider: 'cloud' | 'local';
}

/**
 * Generate actor portrait using the configured AI provider
 */
export async function generatePortrait(
  request: GeneratePortraitRequest
): Promise<AIResponse<{ imageUrl?: string; textResponse?: string }>> {
  const config = getAIConfig();

  if (config.provider === 'local') {
    // Use local LM Studio
    const result = await localAI.generatePortrait({
      ...request,
      model: config.visionModel !== 'default' ? config.visionModel : undefined,
    });

    if (result.success && result.data) {
      return {
        success: true,
        data: {
          imageUrl: result.data.imageUrl || undefined,
          textResponse: result.data.textResponse,
        },
        provider: 'local',
      };
    }

    return {
      success: false,
      error: result.error || 'Failed to generate portrait locally',
      provider: 'local',
    };
  }

  // Use cloud (Supabase Edge Function)
  try {
    const { data, error } = await supabase.functions.invoke('generate-actor-portrait', {
      body: request,
    });

    if (error) {
      throw error;
    }

    return {
      success: true,
      data: {
        imageUrl: data.imageUrl,
      },
      provider: 'cloud',
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to generate portrait',
      provider: 'cloud',
    };
  }
}

/**
 * Generate story using the configured AI provider
 */
export async function generateStory(
  request: GenerateStoryRequest
): Promise<AIResponse<{ story: string }>> {
  const config = getAIConfig();

  if (config.provider === 'local') {
    const result = await localAI.generateStory({
      ...request,
      model: config.textModel !== 'default' ? config.textModel : undefined,
    });

    if (result.success && result.data) {
      return {
        success: true,
        data: { story: result.data.story },
        provider: 'local',
      };
    }

    return {
      success: false,
      error: result.error || 'Failed to generate story locally',
      provider: 'local',
    };
  }

  // Use cloud - note: would need to implement this in Supabase Edge Functions
  try {
    // For now, we'll try local as fallback since story generation may not be in cloud
    const result = await localAI.generateStory(request);
    
    if (result.success && result.data) {
      return {
        success: true,
        data: { story: result.data.story },
        provider: 'local', // Fallback to local
      };
    }

    return {
      success: false,
      error: 'Story generation not available in cloud mode. Please use local LM Studio.',
      provider: 'cloud',
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to generate story',
      provider: 'cloud',
    };
  }
}

/**
 * Generate story template using the configured AI provider
 */
export async function generateTemplate(
  request: GenerateTemplateRequest
): Promise<AIResponse<{ template: unknown }>> {
  const config = getAIConfig();

  // Templates are always via cloud (Supabase Edge Function)
  try {
    const { data, error } = await supabase.functions.invoke('generate-template', {
      body: request,
    });

    if (error) {
      throw error;
    }

    return {
      success: true,
      data: { template: data.template },
      provider: 'cloud',
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to generate template',
      provider: 'cloud',
    };
  }
}

/**
 * Analyze story scenes using the configured AI provider
 */
export async function analyzeScenes(
  storyText: string
): Promise<AIResponse<{ analysis: string }>> {
  const config = getAIConfig();

  if (config.provider === 'local') {
    const result = await localAI.analyzeScenes({
      storyText,
      model: config.textModel !== 'default' ? config.textModel : undefined,
    });

    if (result.success && result.data) {
      return {
        success: true,
        data: { analysis: result.data.analysis },
        provider: 'local',
      };
    }

    return {
      success: false,
      error: result.error || 'Failed to analyze scenes locally',
      provider: 'local',
    };
  }

  // Use cloud
  try {
    const { data, error } = await supabase.functions.invoke('analyze-story-scenes', {
      body: { storyText },
    });

    if (error) {
      throw error;
    }

    return {
      success: true,
      data: { analysis: data.analysis },
      provider: 'cloud',
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to analyze scenes',
      provider: 'cloud',
    };
  }
}

/**
 * Get current AI provider status
 */
export async function getProviderStatus(): Promise<{
  provider: 'cloud' | 'local';
  available: boolean;
  details?: unknown;
}> {
  const config = getAIConfig();

  if (config.provider === 'local') {
    const health = await localAI.checkHealth();
    return {
      provider: 'local',
      available: health.success,
      details: health.data,
    };
  }

  // Cloud is always available (assuming internet connection)
  return {
    provider: 'cloud',
    available: true,
    details: { url: 'Lovable Cloud AI Gateway' },
  };
}
