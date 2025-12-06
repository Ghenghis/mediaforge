/**
 * Image Generation Settings Component
 * Provides seamless A1111/ComfyUI integration controls
 */
import { useState, useEffect } from "react";
import { Settings, Sliders, Image, Sparkles, Cpu } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { useToast } from "@/hooks/use-toast";

// Default settings optimized for portrait generation
const DEFAULT_SETTINGS = {
  backend: 'a1111' as 'a1111' | 'comfyui',
  model: 'default',
  sampler: 'DPM++ 2M Karras',
  steps: 30,
  cfgScale: 7,
  width: 768,
  height: 1024,
  restoreFaces: true,
  hiresEnabled: false,
  hiresScale: 1.5,
  hiresDenoising: 0.5,
  negativePrompt: 'lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, deformed, ugly, duplicate, censored',
};

// Available samplers for A1111
const SAMPLERS = [
  'DPM++ 2M Karras',
  'DPM++ SDE Karras', 
  'DPM++ 2M SDE Karras',
  'Euler a',
  'Euler',
  'DDIM',
  'UniPC',
  'DPM2 a Karras',
];

// Storage key for persistence
const STORAGE_KEY = 'frontier-stories-image-gen-settings';

export interface ImageGenConfig {
  backend: 'a1111' | 'comfyui';
  model: string;
  sampler: string;
  steps: number;
  cfgScale: number;
  width: number;
  height: number;
  restoreFaces: boolean;
  hiresEnabled: boolean;
  hiresScale: number;
  hiresDenoising: number;
  negativePrompt: string;
}

// Get current config from localStorage or defaults
export function getImageGenConfig(): ImageGenConfig {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      return { ...DEFAULT_SETTINGS, ...JSON.parse(stored) };
    }
  } catch (e) {
    console.warn('Failed to load image gen config:', e);
  }
  return DEFAULT_SETTINGS;
}

// Save config to localStorage
export function saveImageGenConfig(config: Partial<ImageGenConfig>): void {
  try {
    const current = getImageGenConfig();
    const updated = { ...current, ...config };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  } catch (e) {
    console.warn('Failed to save image gen config:', e);
  }
}

interface ImageGenSettingsProps {
  onConfigChange?: (config: ImageGenConfig) => void;
  compact?: boolean;
}

const ImageGenSettings = ({ onConfigChange, compact = false }: ImageGenSettingsProps) => {
  const { toast } = useToast();
  const [config, setConfig] = useState<ImageGenConfig>(getImageGenConfig);
  const [isOpen, setIsOpen] = useState(!compact);
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [backendStatus, setBackendStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking');

  // Check backend connection on mount
  useEffect(() => {
    checkBackendConnection();
  }, [config.backend]);

  const checkBackendConnection = async () => {
    setBackendStatus('checking');
    try {
      const localFunctionsUrl = import.meta.env.VITE_LOCAL_FUNCTIONS_URL || 'http://localhost:3001';
      const response = await fetch(`${localFunctionsUrl}/health`);
      if (response.ok) {
        setBackendStatus('connected');
        // Try to fetch available models
        fetchAvailableModels();
      } else {
        setBackendStatus('disconnected');
      }
    } catch {
      setBackendStatus('disconnected');
    }
  };

  const fetchAvailableModels = async () => {
    try {
      const localFunctionsUrl = import.meta.env.VITE_LOCAL_FUNCTIONS_URL || 'http://localhost:3001';
      const response = await fetch(`${localFunctionsUrl}/image-gen/models`);
      if (response.ok) {
        const data = await response.json();
        setAvailableModels(data.models || []);
      }
    } catch {
      // Models fetch failed, use defaults
      setAvailableModels(['default']);
    }
  };

  const updateConfig = (key: keyof ImageGenConfig, value: any) => {
    const newConfig = { ...config, [key]: value };
    setConfig(newConfig);
    saveImageGenConfig(newConfig);
    onConfigChange?.(newConfig);
  };

  const resetToDefaults = () => {
    setConfig(DEFAULT_SETTINGS);
    saveImageGenConfig(DEFAULT_SETTINGS);
    onConfigChange?.(DEFAULT_SETTINGS);
    toast({
      title: "Settings Reset",
      description: "Image generation settings restored to defaults",
    });
  };

  const StatusBadge = () => (
    <Badge 
      variant={backendStatus === 'connected' ? 'default' : 'destructive'}
      className={backendStatus === 'connected' ? 'bg-green-500' : ''}
    >
      {backendStatus === 'checking' ? '...' : backendStatus === 'connected' ? 'Connected' : 'Offline'}
    </Badge>
  );

  if (compact) {
    return (
      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <CollapsibleTrigger asChild>
          <Button variant="ghost" size="sm" className="w-full justify-between">
            <span className="flex items-center gap-2">
              <Settings className="h-4 w-4" />
              Image Settings
            </span>
            <StatusBadge />
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent className="space-y-3 pt-3">
          <CompactSettings config={config} updateConfig={updateConfig} />
        </CollapsibleContent>
      </Collapsible>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            <Image className="h-5 w-5" />
            Image Generation Settings
          </span>
          <StatusBadge />
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Backend Selection */}
        <div className="space-y-2">
          <Label className="flex items-center gap-2">
            <Cpu className="h-4 w-4" />
            Backend
          </Label>
          <Select value={config.backend} onValueChange={(v) => updateConfig('backend', v)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="a1111">Automatic1111 / Forge</SelectItem>
              <SelectItem value="comfyui">ComfyUI</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Sampler */}
        <div className="space-y-2">
          <Label>Sampler</Label>
          <Select value={config.sampler} onValueChange={(v) => updateConfig('sampler', v)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {SAMPLERS.map(s => (
                <SelectItem key={s} value={s}>{s}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Steps */}
        <div className="space-y-2">
          <div className="flex justify-between">
            <Label>Steps</Label>
            <span className="text-sm text-muted-foreground">{config.steps}</span>
          </div>
          <Slider
            value={[config.steps]}
            onValueChange={([v]) => updateConfig('steps', v)}
            min={10}
            max={50}
            step={1}
          />
        </div>

        {/* CFG Scale */}
        <div className="space-y-2">
          <div className="flex justify-between">
            <Label>CFG Scale</Label>
            <span className="text-sm text-muted-foreground">{config.cfgScale}</span>
          </div>
          <Slider
            value={[config.cfgScale]}
            onValueChange={([v]) => updateConfig('cfgScale', v)}
            min={1}
            max={15}
            step={0.5}
          />
        </div>

        {/* Resolution */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>Width</Label>
            <Select value={config.width.toString()} onValueChange={(v) => updateConfig('width', parseInt(v))}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="512">512</SelectItem>
                <SelectItem value="640">640</SelectItem>
                <SelectItem value="768">768</SelectItem>
                <SelectItem value="832">832</SelectItem>
                <SelectItem value="1024">1024</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Height</Label>
            <Select value={config.height.toString()} onValueChange={(v) => updateConfig('height', parseInt(v))}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="512">512</SelectItem>
                <SelectItem value="768">768</SelectItem>
                <SelectItem value="896">896</SelectItem>
                <SelectItem value="1024">1024</SelectItem>
                <SelectItem value="1152">1152</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Restore Faces */}
        <div className="flex items-center justify-between">
          <Label>Restore Faces</Label>
          <Switch
            checked={config.restoreFaces}
            onCheckedChange={(v) => updateConfig('restoreFaces', v)}
          />
        </div>

        {/* Hi-Res Fix */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label className="flex items-center gap-2">
              <Sparkles className="h-4 w-4" />
              Hi-Res Upscale
            </Label>
            <Switch
              checked={config.hiresEnabled}
              onCheckedChange={(v) => updateConfig('hiresEnabled', v)}
            />
          </div>
          {config.hiresEnabled && (
            <div className="pl-4 space-y-3 border-l-2 border-muted">
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>Scale</Label>
                  <span className="text-sm text-muted-foreground">{config.hiresScale}x</span>
                </div>
                <Slider
                  value={[config.hiresScale]}
                  onValueChange={([v]) => updateConfig('hiresScale', v)}
                  min={1.25}
                  max={2}
                  step={0.25}
                />
              </div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>Denoising</Label>
                  <span className="text-sm text-muted-foreground">{config.hiresDenoising}</span>
                </div>
                <Slider
                  value={[config.hiresDenoising]}
                  onValueChange={([v]) => updateConfig('hiresDenoising', v)}
                  min={0.1}
                  max={0.8}
                  step={0.05}
                />
              </div>
            </div>
          )}
        </div>

        {/* Negative Prompt */}
        <div className="space-y-2">
          <Label>Negative Prompt</Label>
          <Textarea
            value={config.negativePrompt}
            onChange={(e) => updateConfig('negativePrompt', e.target.value)}
            placeholder="Things to avoid in generation..."
            className="h-20 text-xs"
          />
        </div>

        {/* Reset Button */}
        <Button variant="outline" onClick={resetToDefaults} className="w-full">
          Reset to Defaults
        </Button>
      </CardContent>
    </Card>
  );
};

// Compact version for inline use
const CompactSettings = ({ config, updateConfig }: { 
  config: ImageGenConfig; 
  updateConfig: (key: keyof ImageGenConfig, value: any) => void;
}) => (
  <div className="space-y-3 p-3 bg-muted rounded-lg">
    <div className="grid grid-cols-2 gap-3">
      <div className="space-y-1">
        <Label className="text-xs">Steps</Label>
        <Slider
          value={[config.steps]}
          onValueChange={([v]) => updateConfig('steps', v)}
          min={10}
          max={50}
          step={1}
        />
      </div>
      <div className="space-y-1">
        <Label className="text-xs">CFG</Label>
        <Slider
          value={[config.cfgScale]}
          onValueChange={([v]) => updateConfig('cfgScale', v)}
          min={1}
          max={15}
          step={0.5}
        />
      </div>
    </div>
    <div className="flex items-center justify-between">
      <Label className="text-xs">Hi-Res</Label>
      <Switch
        checked={config.hiresEnabled}
        onCheckedChange={(v) => updateConfig('hiresEnabled', v)}
      />
    </div>
  </div>
);

export default ImageGenSettings;
