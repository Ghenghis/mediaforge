/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_SUPABASE_URL: string;
  readonly VITE_SUPABASE_PUBLISHABLE_KEY: string;
  readonly VITE_SUPABASE_PROJECT_ID: string;
  readonly VITE_LM_STUDIO_URL: string;
  readonly VITE_LOCAL_FUNCTIONS_URL: string;
  readonly VITE_FUNCTIONS_URL: string;
  readonly VITE_LM_STUDIO_MODELS_PATH: string;
  readonly VITE_ADULT_CONTENT_ENABLED: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
