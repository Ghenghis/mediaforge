/**
 * AI Provider Service
 * Manages switching between cloud (Supabase Edge Functions) and local (LM Studio) AI
 */

// AI Provider types
export type AIProvider = 'cloud' | 'local';

export interface AIProviderConfig {
  provider: AIProvider;
  localUrl: string;
  visionModel: string;
  textModel: string;
  imageModel: string;
}

// Default configuration - Using 'local' to leverage Docker functions server with sexy model outfits
const DEFAULT_CONFIG: AIProviderConfig = {
  provider: 'local',
  localUrl: import.meta.env.VITE_LOCAL_FUNCTIONS_URL || 'http://localhost:3001',
  visionModel: 'default',
  textModel: 'default',
  imageModel: 'default',
};

// Storage key for persistence
const STORAGE_KEY = 'frontier-stories-ai-config';

/**
 * Get current AI provider configuration
 */
export function getAIConfig(): AIProviderConfig {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      return { ...DEFAULT_CONFIG, ...JSON.parse(stored) };
    }
  } catch (e) {
    console.warn('Failed to load AI config from storage:', e);
  }
  return DEFAULT_CONFIG;
}

/**
 * Save AI provider configuration
 */
export function saveAIConfig(config: Partial<AIProviderConfig>): AIProviderConfig {
  const current = getAIConfig();
  const updated = { ...current, ...config };
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  } catch (e) {
    console.warn('Failed to save AI config to storage:', e);
  }
  return updated;
}

/**
 * Get the current provider
 */
export function getCurrentProvider(): AIProvider {
  return getAIConfig().provider;
}

/**
 * Set the current provider
 */
export function setProvider(provider: AIProvider): void {
  saveAIConfig({ provider });
}

/**
 * Check if local LM Studio is available
 */
export async function checkLocalAvailability(): Promise<{
  available: boolean;
  models?: string[];
  error?: string;
}> {
  const config = getAIConfig();
  try {
    const response = await fetch(`${config.localUrl}/health`, {
      method: 'GET',
      signal: AbortSignal.timeout(5000),
    });
    
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }
    
    const data = await response.json();
    
    // Also try to get models
    const modelsResponse = await fetch(`${config.localUrl}/models`, {
      method: 'GET',
      signal: AbortSignal.timeout(5000),
    });
    
    let models: string[] = [];
    if (modelsResponse.ok) {
      const modelsData = await modelsResponse.json();
      models = modelsData.data?.map((m: { id: string }) => m.id) || [];
    }
    
    return {
      available: true,
      models,
    };
  } catch (error) {
    return {
      available: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Check if LM Studio is running and has models loaded
 */
export async function checkLMStudioStatus(): Promise<{
  connected: boolean;
  modelsLoaded: boolean;
  loadedModels: string[];
  error?: string;
}> {
  const config = getAIConfig();
  try {
    const response = await fetch(`${config.localUrl}/models`, {
      method: 'GET',
      signal: AbortSignal.timeout(5000),
    });
    
    if (!response.ok) {
      throw new Error(`LM Studio not available: ${response.status}`);
    }
    
    const data = await response.json();
    const models = data.data || [];
    
    return {
      connected: true,
      modelsLoaded: models.length > 0,
      loadedModels: models.map((m: { id: string }) => m.id),
    };
  } catch (error) {
    return {
      connected: false,
      modelsLoaded: false,
      loadedModels: [],
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}
