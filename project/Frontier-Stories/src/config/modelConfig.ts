/**
 * Frontier-Stories Model Configuration
 * Automatic model switching based on task type
 * 
 * Priority: Uncensored models first for 18+ adult content generation
 */

export interface ModelDefinition {
  id: string;
  name: string;
  path: string;
  size: string;
  type: 'text' | 'vision' | 'image_gen' | 'video_gen' | 'tts' | 'ocr';
  uncensored: boolean;
  quality: 'low' | 'medium' | 'high' | 'ultra';
  speed: 'fast' | 'medium' | 'slow';
  vram: number; // GB required
  description: string;
  useCases: string[];
}

export interface TaskModelMapping {
  task: string;
  primaryModel: string;
  fallbackModels: string[];
  description: string;
}

// ============================================================================
// UNCENSORED TEXT MODELS - Priority 1 (Adult Story Generation)
// ============================================================================
export const UNCENSORED_TEXT_MODELS: ModelDefinition[] = [
  {
    id: 'wizardlm-uncensored-supercot-storytelling-30b',
    name: 'WizardLM Uncensored SuperCOT Storytelling 30B',
    path: 'TheBloke/wizardlm-uncensored-supercot-storytelling-30b/WizardLM-Uncensored-SuperCOT-Storytelling.Q4_K_S.gguf',
    size: '18.44 GB',
    type: 'text',
    uncensored: true,
    quality: 'ultra',
    speed: 'slow',
    vram: 20,
    description: 'Best quality uncensored storytelling model. Excellent for long-form adult narratives.',
    useCases: ['adult_stories', 'long_narratives', 'creative_writing', 'roleplay']
  },
  {
    id: 'openai-gpt-oss-20b-abliterated-uncensored',
    name: 'OpenAI GPT-OSS 20B Abliterated Uncensored',
    path: 'DavidAU/openai-gpt-oss-20b-abliterated-uncensored-neo-imatrix/OpenAI-20B-NEO-CODEPlus-Uncensored-IQ4_NL.gguf',
    size: '11.82 GB',
    type: 'text',
    uncensored: true,
    quality: 'high',
    speed: 'medium',
    vram: 14,
    description: 'Abliterated GPT model with no content restrictions.',
    useCases: ['adult_stories', 'dialogue', 'creative_writing']
  },
  {
    id: 'l3-dark-champion-18b-uncensored',
    name: 'L3.2 8X3B MOE Dark Champion 18.4B Uncensored',
    path: 'DavidAU/llama-3.2-8x3b-moe-dark-champion-instruct-uncensored-abliterated-18.4b/L3.2-8X3B-MOE-Dark-Champion-Inst-18.4B-uncen-ablit_D_AU-Q6_k.gguf',
    size: '15.15 GB',
    type: 'text',
    uncensored: true,
    quality: 'high',
    speed: 'medium',
    vram: 16,
    description: 'Dark-themed uncensored model for edgy content.',
    useCases: ['adult_stories', 'dark_themes', 'roleplay']
  },
  {
    id: 'qwen2.5-14b-instruct-uncensored',
    name: 'Qwen2.5 14B Instruct Uncensored',
    path: 'Orion-zhen/qwen2.5-14b-instruct-uncensored/qwen2.5-14b-instruct-uncensored-q5_k_m.gguf',
    size: '10.51 GB',
    type: 'text',
    uncensored: true,
    quality: 'high',
    speed: 'medium',
    vram: 12,
    description: 'High quality Qwen model without content filters.',
    useCases: ['adult_stories', 'dialogue', 'instructions']
  },
  {
    id: 'gemma-restless-quill-10b-uncensored',
    name: 'Gemma The Writer N Restless Quill 10B Uncensored',
    path: 'DavidAU/gemma-the-writer-n-restless-quill-10b-uncensored/Gemma-The-Writer-N-Restless-Quill-10B-max-cpu-D_AU-Q8_0.gguf',
    size: '11.53 GB',
    type: 'text',
    uncensored: true,
    quality: 'high',
    speed: 'medium',
    vram: 12,
    description: 'Uncensored writer model optimized for creative fiction.',
    useCases: ['adult_stories', 'creative_writing', 'fiction']
  },
  {
    id: 'dirty-shirley-writer-v2-9b-uncensored',
    name: 'Dirty Shirley Writer v2 9B Uncensored',
    path: 'mradermacher/dirty-shirley-writer-v2-9b-uncensored/Dirty-Shirley-Writer-v2-9B-Uncensored.Q6_K.gguf',
    size: '7.59 GB',
    type: 'text',
    uncensored: true,
    quality: 'high',
    speed: 'fast',
    vram: 10,
    description: 'Explicitly designed for adult creative writing.',
    useCases: ['adult_stories', 'erotic_fiction', 'roleplay']
  },
  {
    id: 'wizardlm-13b-uncensored',
    name: 'WizardLM 13B Uncensored',
    path: 'mradermacher/wizardlm-13b-uncensored/WizardLM-13B-Uncensored.Q6_K.gguf',
    size: '10.68 GB',
    type: 'text',
    uncensored: true,
    quality: 'high',
    speed: 'medium',
    vram: 12,
    description: 'Classic uncensored WizardLM for general adult content.',
    useCases: ['adult_stories', 'dialogue', 'general']
  },
  {
    id: 'qwen3-8b-jailbroken',
    name: 'Qwen3 8B Jailbroken',
    path: 'mradermacher/qwen3-8b-jailbroken-i1/Qwen3-8B-Jailbroken.i1-Q6_K.gguf',
    size: '6.73 GB',
    type: 'text',
    uncensored: true,
    quality: 'medium',
    speed: 'fast',
    vram: 8,
    description: 'Jailbroken Qwen3 with removed safety filters.',
    useCases: ['adult_stories', 'dialogue', 'quick_generation']
  },
  {
    id: 'deepseek-r1-nsfw-rp',
    name: 'DeepSeek R1 Distill NSFW RP vRedux',
    path: 'mradermacher/deepseek-r1-distill-nsfw-rp-vredux-proper/Deepseek-R1-Distill-NSFW-RP-vRedux-Proper.Q4_K_S.gguf',
    size: '4.69 GB',
    type: 'text',
    uncensored: true,
    quality: 'medium',
    speed: 'fast',
    vram: 6,
    description: 'Specialized for NSFW roleplay scenarios.',
    useCases: ['roleplay', 'adult_stories', 'dialogue']
  },
  {
    id: 'deepseek-r1-qwen-7b-uncensored',
    name: 'DeepSeek R1 Distill Qwen 7B Uncensored',
    path: 'mradermacher/deepseek-r1-distill-qwen-7b-uncensored/DeepSeek-R1-Distill-Qwen-7B-Uncensored.Q4_K_S.gguf',
    size: '4.46 GB',
    type: 'text',
    uncensored: true,
    quality: 'medium',
    speed: 'fast',
    vram: 6,
    description: 'Fast uncensored reasoning model.',
    useCases: ['adult_stories', 'quick_generation', 'dialogue']
  },
  {
    id: 'wizard-vicuna-7b-uncensored',
    name: 'Wizard Vicuna 7B Uncensored',
    path: 'mradermacher/wizard-vicuna-7b-uncensored/Wizard-Vicuna-7B-Uncensored.Q6_K.gguf',
    size: '5.53 GB',
    type: 'text',
    uncensored: true,
    quality: 'medium',
    speed: 'fast',
    vram: 8,
    description: 'Classic uncensored assistant model.',
    useCases: ['adult_stories', 'dialogue', 'general']
  },
  {
    id: 'llama-3.2-3b-fluxed-uncensored',
    name: 'Llama 3.2 3B Fluxed Uncensored',
    path: 'mradermacher/llama-3.2-3b-fluxed-uncensored/Llama-3.2-3B-Fluxed-uncensored.Q8_0.gguf',
    size: '3.42 GB',
    type: 'text',
    uncensored: true,
    quality: 'medium',
    speed: 'fast',
    vram: 4,
    description: 'Small fast uncensored model for quick iterations.',
    useCases: ['quick_generation', 'dialogue', 'drafts']
  },
  {
    id: 'deepseek-r1-qwen-1.5b-fully-uncensored',
    name: 'DeepSeek R1 Distill Qwen 1.5B Fully Uncensored',
    path: 'mradermacher/deepseek-r1-distill-qwen-1.5b-fully-uncensored-i1/DeepSeek-R1-Distill-Qwen-1.5B-Fully-Uncensored.i1-Q4_0.gguf',
    size: '1068.23 MB',
    type: 'text',
    uncensored: true,
    quality: 'low',
    speed: 'fast',
    vram: 2,
    description: 'Ultra-fast tiny uncensored model for testing.',
    useCases: ['quick_generation', 'testing', 'prototyping']
  }
];

// ============================================================================
// UNCENSORED VISION MODELS - Priority 1 (Image Understanding for Adult Content)
// ============================================================================
export const UNCENSORED_VISION_MODELS: ModelDefinition[] = [
  {
    id: 'amoral-gemma3-12b-vision',
    name: 'Amoral Gemma3 12B Vision',
    path: 'mradermacher/amoral-gemma3-12b-vision-i1/amoral-gemma3-12B-vision.i1-Q6_K.gguf',
    size: '9.66 GB',
    type: 'vision',
    uncensored: true,
    quality: 'high',
    speed: 'medium',
    vram: 12,
    description: 'BEST uncensored vision model. No content restrictions for image analysis.',
    useCases: ['image_analysis', 'adult_images', 'scene_description', 'portrait_analysis']
  },
  {
    id: 'llama-3.2-11b-vision-abliterated',
    name: 'Llama 3.2 11B Vision Instruct Abliterated',
    path: 'case01/llama-3.2-11b-vision-instruct-abliterated/llama-3.2-11B-vision_f16_projector.gguf',
    size: '1.94 GB',
    type: 'vision',
    uncensored: true,
    quality: 'high',
    speed: 'medium',
    vram: 12,
    description: 'Abliterated Llama vision model without content filters.',
    useCases: ['image_analysis', 'adult_images', 'scene_description']
  },
  {
    id: 'qwen3-vl-30b-a3b',
    name: 'Qwen3 VL 30B A3B Instruct',
    path: 'yairpatch/qwen3-vl-30b-a3b-instruct/Qwen3-VL-30B-A3B-Instruct-Q5_K_M.gguf',
    size: '21.73 GB',
    type: 'vision',
    uncensored: false,
    quality: 'ultra',
    speed: 'slow',
    vram: 24,
    description: 'Largest vision model for highest quality image understanding.',
    useCases: ['detailed_analysis', 'complex_scenes', 'high_quality']
  },
  {
    id: 'qwen3-vl-8b',
    name: 'Qwen3 VL 8B',
    path: 'qwen/qwen3-vl-8b',
    size: '9.87 GB',
    type: 'vision',
    uncensored: false,
    quality: 'high',
    speed: 'medium',
    vram: 10,
    description: 'Good balance of quality and speed for vision tasks.',
    useCases: ['image_analysis', 'scene_description', 'general_vision']
  },
  {
    id: 'llama-3.2-11b-vision',
    name: 'Llama 3.2 11B Vision Instruct',
    path: 'leafspark/llama-3.2-11b-vision-instruct@q4_k_m/Llama-3.2-11B-Vision-Instruct.Q4_K_M.gguf',
    size: '5.96 GB',
    type: 'vision',
    uncensored: false,
    quality: 'high',
    speed: 'medium',
    vram: 8,
    description: 'Standard Llama vision model for general use.',
    useCases: ['image_analysis', 'scene_description', 'general_vision']
  }
];

// ============================================================================
// WRITER MODELS - Priority 2 (High Quality Story Generation)
// ============================================================================
export const WRITER_MODELS: ModelDefinition[] = [
  {
    id: 'rombos-qwen2.5-writer-32b',
    name: 'Rombos Qwen2.5 Writer 32B',
    path: 'bartowski/rombos-qwen2.5-writer-32b/Rombos-Qwen2.5-Writer-32b-Q4_1.gguf',
    size: '20.64 GB',
    type: 'text',
    uncensored: false,
    quality: 'ultra',
    speed: 'slow',
    vram: 22,
    description: 'Highest quality writer model for professional fiction.',
    useCases: ['long_narratives', 'professional_writing', 'novels']
  },
  {
    id: 'mistral-small-24b-writer',
    name: 'Mistral Small 24B Instruct Writer',
    path: 'bartowski/lars1234_mistral-small-24b-instruct-2501-writer/lars1234_Mistral-Small-24B-Instruct-2501-writer-Q6_K_L.gguf',
    size: '19.67 GB',
    type: 'text',
    uncensored: false,
    quality: 'ultra',
    speed: 'slow',
    vram: 20,
    description: 'Mistral-based writer for sophisticated narratives.',
    useCases: ['long_narratives', 'dialogue', 'creative_writing']
  },
  {
    id: 'l3-grand-story-16.5b',
    name: 'L3 SMB Grand Story Ultra Quality 16.5B',
    path: 'DavidAU/l3-smb-grand-story-ultra-quality-16.5b-neo-v2-imatrix/L3-SMB-Grand-STORY-F32-Ultra-Quality-16_5B-NEO-V2-D_AU-Q4_K_S-imat13.gguf',
    size: '9.51 GB',
    type: 'text',
    uncensored: false,
    quality: 'high',
    speed: 'medium',
    vram: 12,
    description: 'Optimized for grand storytelling narratives.',
    useCases: ['epic_stories', 'world_building', 'adventure']
  },
  {
    id: 'praxis-bookwriter-14b',
    name: 'Praxis Bookwriter Qwen2.5 14B',
    path: 'mradermacher/praxis-bookwriter-qwen2.5-14b-sft-i1/praxis-bookwriter-qwen2.5-14b-sft.i1-Q4_K_S.gguf',
    size: '8.57 GB',
    type: 'text',
    uncensored: false,
    quality: 'high',
    speed: 'medium',
    vram: 10,
    description: 'Specialized for book-length fiction writing.',
    useCases: ['novels', 'chapters', 'long_form']
  },
  {
    id: 'gemma-the-writer-9b-abliterated',
    name: 'Gemma The Writer 9B Abliterated',
    path: 'mradermacher/gemma-the-writer-9b-abliterated/Gemma-The-Writer-9B-abliterated.Q6_K.gguf',
    size: '7.59 GB',
    type: 'text',
    uncensored: true,
    quality: 'high',
    speed: 'fast',
    vram: 10,
    description: 'Abliterated Gemma writer model.',
    useCases: ['creative_writing', 'fiction', 'dialogue']
  },
  {
    id: 'gemma-gutenberg-10b',
    name: 'Gemma The Writer J.Gutenberg 10B',
    path: 'DavidAU/gemma-the-writer-j.gutenberg-10b/Gemma-The-Writer-J.GutenBerg-10B-D_AU-Q6_k.gguf',
    size: '8.24 GB',
    type: 'text',
    uncensored: false,
    quality: 'high',
    speed: 'medium',
    vram: 10,
    description: 'Classic literature style writing.',
    useCases: ['period_fiction', 'classic_style', 'formal_writing']
  },
  {
    id: 'llama-3.1-8b-bookadventures',
    name: 'Llama 3.1 8B BookAdventures',
    path: 'KoboldAI/llama-3.1-8b-bookadventures/Llama-3.1-8B-BookAdventures.Q4_K_S.gguf',
    size: '4.69 GB',
    type: 'text',
    uncensored: false,
    quality: 'medium',
    speed: 'fast',
    vram: 6,
    description: 'Adventure-focused story model.',
    useCases: ['adventure', 'action', 'quick_stories']
  }
];

// ============================================================================
// IMAGE GENERATION MODELS (Flux, etc.)
// ============================================================================
export const IMAGE_GEN_MODELS: ModelDefinition[] = [
  {
    id: 'chroma-unlocked-v29',
    name: 'Chroma Unlocked v29 (Flux)',
    path: 'silveroxides/chroma/chroma-unlocked-v29-Q8_0.gguf',
    size: '10.29 GB',
    type: 'image_gen',
    uncensored: true,
    quality: 'high',
    speed: 'medium',
    vram: 12,
    description: 'Unlocked Flux model for unrestricted image generation.',
    useCases: ['portraits', 'scenes', 'adult_images']
  },
  {
    id: 'flux1-kontext-dev',
    name: 'Flux1 Kontext Dev',
    path: 'QuantStack/flux.1-kontext-dev/flux1-kontext-dev-Q6_K.gguf',
    size: '9.85 GB',
    type: 'image_gen',
    uncensored: false,
    quality: 'high',
    speed: 'medium',
    vram: 12,
    description: 'Context-aware Flux model for consistent image generation.',
    useCases: ['portraits', 'scenes', 'consistent_style']
  }
];

// ============================================================================
// VIDEO GENERATION MODELS
// ============================================================================
export const VIDEO_GEN_MODELS: ModelDefinition[] = [
  {
    id: 'wan2.2-i2v-14b',
    name: 'Wan2.2 Image-to-Video 14B',
    path: 'bullerwins/wan2.2-i2v-a14b/wan2.2_i2v_low_noise_14B_Q6_K.gguf',
    size: '12.00 GB',
    type: 'video_gen',
    uncensored: false,
    quality: 'high',
    speed: 'slow',
    vram: 14,
    description: 'Convert images to video animations.',
    useCases: ['image_animation', 'scene_motion', 'video_creation']
  },
  {
    id: 'wan2.2-t2v-14b',
    name: 'Wan2.2 Text-to-Video 14B',
    path: 'QuantStack/wan2.2-t2v-a14b/Wan2.2-T2V-A14B-LowNoise-Q6_K.gguf',
    size: '12.00 GB',
    type: 'video_gen',
    uncensored: false,
    quality: 'high',
    speed: 'slow',
    vram: 14,
    description: 'Generate video from text descriptions.',
    useCases: ['text_to_video', 'scene_generation', 'animation']
  },
  {
    id: 'hunyuan-video-i2v',
    name: 'HunyuanVideo Image-to-Video 720p',
    path: 'city96/hunyuanvideo-i2v/hunyuan-video-i2v-720p-Q6_K.gguf',
    size: '10.95 GB',
    type: 'video_gen',
    uncensored: false,
    quality: 'high',
    speed: 'slow',
    vram: 12,
    description: 'High quality 720p video generation from images.',
    useCases: ['hd_video', 'image_animation', 'cinematic']
  }
];

// ============================================================================
// OCR MODELS
// ============================================================================
export const OCR_MODELS: ModelDefinition[] = [
  {
    id: 'qwen2-vl-7b-ocr',
    name: 'Qwen2 VL 7B OCR',
    path: 'mradermacher/qwen-2-vl-7b-ocr/Qwen-2-VL-7B-OCR.Q6_K.gguf',
    size: '7.61 GB',
    type: 'ocr',
    uncensored: false,
    quality: 'high',
    speed: 'medium',
    vram: 10,
    description: 'Best OCR model for text extraction from images.',
    useCases: ['text_extraction', 'document_scanning', 'ocr']
  },
  {
    id: 'nanonets-ocr2-3b',
    name: 'Nanonets OCR2 3B',
    path: 'mradermacher/nanonets-ocr2-3b/Nanonets-OCR2-3B.Q6_K.gguf',
    size: '3.88 GB',
    type: 'ocr',
    uncensored: false,
    quality: 'medium',
    speed: 'fast',
    vram: 5,
    description: 'Fast OCR for quick text extraction.',
    useCases: ['quick_ocr', 'text_extraction']
  }
];

// ============================================================================
// TASK-BASED MODEL MAPPING (Automatic Selection)
// ============================================================================
export const TASK_MODEL_MAPPING: TaskModelMapping[] = [
  {
    task: 'adult_story_generation',
    primaryModel: 'wizardlm-uncensored-supercot-storytelling-30b',
    fallbackModels: ['dirty-shirley-writer-v2-9b-uncensored', 'qwen2.5-14b-instruct-uncensored', 'deepseek-r1-nsfw-rp'],
    description: 'Generate adult/erotic story content'
  },
  {
    task: 'quick_adult_dialogue',
    primaryModel: 'dirty-shirley-writer-v2-9b-uncensored',
    fallbackModels: ['qwen3-8b-jailbroken', 'deepseek-r1-qwen-7b-uncensored'],
    description: 'Fast adult dialogue generation'
  },
  {
    task: 'adult_image_analysis',
    primaryModel: 'amoral-gemma3-12b-vision',
    fallbackModels: ['llama-3.2-11b-vision-abliterated', 'qwen3-vl-8b'],
    description: 'Analyze adult/NSFW images without restrictions'
  },
  {
    task: 'portrait_generation',
    primaryModel: 'chroma-unlocked-v29',
    fallbackModels: ['flux1-kontext-dev'],
    description: 'Generate character portraits'
  },
  {
    task: 'scene_description',
    primaryModel: 'amoral-gemma3-12b-vision',
    fallbackModels: ['qwen3-vl-8b', 'llama-3.2-11b-vision'],
    description: 'Describe scenes from images'
  },
  {
    task: 'long_narrative',
    primaryModel: 'rombos-qwen2.5-writer-32b',
    fallbackModels: ['mistral-small-24b-writer', 'wizardlm-uncensored-supercot-storytelling-30b'],
    description: 'Generate long-form narrative content'
  },
  {
    task: 'quick_draft',
    primaryModel: 'llama-3.2-3b-fluxed-uncensored',
    fallbackModels: ['deepseek-r1-qwen-1.5b-fully-uncensored'],
    description: 'Quick story drafts and testing'
  },
  {
    task: 'video_animation',
    primaryModel: 'wan2.2-i2v-14b',
    fallbackModels: ['hunyuan-video-i2v'],
    description: 'Animate images into video'
  },
  {
    task: 'text_extraction',
    primaryModel: 'qwen2-vl-7b-ocr',
    fallbackModels: ['nanonets-ocr2-3b'],
    description: 'Extract text from images'
  }
];

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Get the best model for a specific task based on available VRAM
 */
export function getModelForTask(task: string, availableVram: number = 12): ModelDefinition | null {
  const mapping = TASK_MODEL_MAPPING.find(m => m.task === task);
  if (!mapping) return null;
  
  const allModels = [
    ...UNCENSORED_TEXT_MODELS,
    ...UNCENSORED_VISION_MODELS,
    ...WRITER_MODELS,
    ...IMAGE_GEN_MODELS,
    ...VIDEO_GEN_MODELS,
    ...OCR_MODELS
  ];
  
  // Try primary model first
  const primary = allModels.find(m => m.id === mapping.primaryModel);
  if (primary && primary.vram <= availableVram) return primary;
  
  // Try fallbacks
  for (const fallbackId of mapping.fallbackModels) {
    const fallback = allModels.find(m => m.id === fallbackId);
    if (fallback && fallback.vram <= availableVram) return fallback;
  }
  
  return null;
}

/**
 * Get all uncensored models sorted by quality
 */
export function getUncensoredModels(): ModelDefinition[] {
  const allModels = [
    ...UNCENSORED_TEXT_MODELS,
    ...UNCENSORED_VISION_MODELS,
    ...WRITER_MODELS.filter(m => m.uncensored),
    ...IMAGE_GEN_MODELS.filter(m => m.uncensored)
  ];
  
  const qualityOrder = { ultra: 0, high: 1, medium: 2, low: 3 };
  return allModels.sort((a, b) => qualityOrder[a.quality] - qualityOrder[b.quality]);
}

/**
 * Get models that fit within VRAM limit
 */
export function getModelsForVram(maxVram: number): ModelDefinition[] {
  const allModels = [
    ...UNCENSORED_TEXT_MODELS,
    ...UNCENSORED_VISION_MODELS,
    ...WRITER_MODELS,
    ...IMAGE_GEN_MODELS,
    ...VIDEO_GEN_MODELS,
    ...OCR_MODELS
  ];
  
  return allModels.filter(m => m.vram <= maxVram);
}

/**
 * Default model configuration for Frontier-Stories
 */
export const DEFAULT_MODEL_CONFIG = {
  storyGeneration: 'dirty-shirley-writer-v2-9b-uncensored',
  imageAnalysis: 'amoral-gemma3-12b-vision',
  portraitGeneration: 'chroma-unlocked-v29',
  quickDraft: 'llama-3.2-3b-fluxed-uncensored',
  sceneAnalysis: 'amoral-gemma3-12b-vision'
};
