import { useState, useEffect } from "react";
import { Cpu, Image, FileText, Video, Eye, Zap, HardDrive, Check } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { useToast } from "@/hooks/use-toast";
import {
  UNCENSORED_TEXT_MODELS,
  UNCENSORED_VISION_MODELS,
  WRITER_MODELS,
  IMAGE_GEN_MODELS,
  VIDEO_GEN_MODELS,
  TASK_MODEL_MAPPING,
  getModelForTask,
  getUncensoredModels,
  getModelsForVram,
  DEFAULT_MODEL_CONFIG,
  type ModelDefinition,
  type TaskModelMapping
} from "@/config/modelConfig";

interface ModelSelectorProps {
  onConfigChange?: (config: ModelConfig) => void;
}

interface ModelConfig {
  storyGeneration: string;
  imageAnalysis: string;
  portraitGeneration: string;
  quickDraft: string;
  sceneAnalysis: string;
  autoSwitch: boolean;
  vramLimit: number;
}

const ModelSelector = ({ onConfigChange }: ModelSelectorProps) => {
  const { toast } = useToast();
  const [config, setConfig] = useState<ModelConfig>({
    ...DEFAULT_MODEL_CONFIG,
    autoSwitch: true,
    vramLimit: 12
  });
  const [availableModels, setAvailableModels] = useState<ModelDefinition[]>([]);

  useEffect(() => {
    // Filter models based on VRAM limit
    const models = getModelsForVram(config.vramLimit);
    setAvailableModels(models);
  }, [config.vramLimit]);

  const updateConfig = (key: keyof ModelConfig, value: string | boolean | number) => {
    const newConfig = { ...config, [key]: value };
    setConfig(newConfig);
    onConfigChange?.(newConfig);
  };

  const applyAutoConfig = () => {
    const autoConfig: ModelConfig = {
      storyGeneration: getModelForTask('adult_story_generation', config.vramLimit)?.id || DEFAULT_MODEL_CONFIG.storyGeneration,
      imageAnalysis: getModelForTask('adult_image_analysis', config.vramLimit)?.id || DEFAULT_MODEL_CONFIG.imageAnalysis,
      portraitGeneration: getModelForTask('portrait_generation', config.vramLimit)?.id || DEFAULT_MODEL_CONFIG.portraitGeneration,
      quickDraft: getModelForTask('quick_draft', config.vramLimit)?.id || DEFAULT_MODEL_CONFIG.quickDraft,
      sceneAnalysis: getModelForTask('scene_description', config.vramLimit)?.id || DEFAULT_MODEL_CONFIG.sceneAnalysis,
      autoSwitch: true,
      vramLimit: config.vramLimit
    };
    setConfig(autoConfig);
    onConfigChange?.(autoConfig);
    toast({
      title: "Auto-configured",
      description: `Models selected for ${config.vramLimit}GB VRAM limit`,
    });
  };

  const getModelById = (id: string): ModelDefinition | undefined => {
    const allModels = [
      ...UNCENSORED_TEXT_MODELS,
      ...UNCENSORED_VISION_MODELS,
      ...WRITER_MODELS,
      ...IMAGE_GEN_MODELS,
      ...VIDEO_GEN_MODELS
    ];
    return allModels.find(m => m.id === id);
  };

  const QualityBadge = ({ quality }: { quality: string }) => {
    const colors: Record<string, string> = {
      ultra: 'bg-purple-500',
      high: 'bg-green-500',
      medium: 'bg-yellow-500',
      low: 'bg-gray-500'
    };
    return (
      <Badge className={`${colors[quality]} text-white text-xs`}>
        {quality}
      </Badge>
    );
  };

  const ModelOption = ({ model }: { model: ModelDefinition }) => (
    <div className="flex items-center justify-between w-full">
      <div className="flex items-center gap-2">
        <span className="truncate max-w-[200px]">{model.name}</span>
        {model.uncensored && (
          <Badge variant="destructive" className="text-xs">18+</Badge>
        )}
      </div>
      <div className="flex items-center gap-1">
        <QualityBadge quality={model.quality} />
        <Badge variant="outline" className="text-xs">{model.size}</Badge>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* VRAM Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <HardDrive className="h-5 w-5" />
            VRAM Configuration
          </CardTitle>
          <CardDescription>
            Set your available VRAM to filter compatible models
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Available VRAM</Label>
              <span className="text-sm font-medium">{config.vramLimit} GB</span>
            </div>
            <Slider
              value={[config.vramLimit]}
              onValueChange={(v) => updateConfig('vramLimit', v[0])}
              min={4}
              max={48}
              step={2}
            />
            <p className="text-sm text-muted-foreground">
              {availableModels.length} models available for your VRAM
            </p>
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Auto-Switch Models</Label>
              <p className="text-sm text-muted-foreground">
                Automatically select best model for each task
              </p>
            </div>
            <Switch
              checked={config.autoSwitch}
              onCheckedChange={(v) => updateConfig('autoSwitch', v)}
            />
          </div>

          <Button onClick={applyAutoConfig} className="w-full">
            <Zap className="h-4 w-4 mr-2" />
            Auto-Configure Best Models
          </Button>
        </CardContent>
      </Card>

      {/* Story Generation Model */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Story Generation
            <Badge variant="destructive">18+</Badge>
          </CardTitle>
          <CardDescription>
            Primary model for generating adult story content
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Select
            value={config.storyGeneration}
            onValueChange={(v) => updateConfig('storyGeneration', v)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select story model" />
            </SelectTrigger>
            <SelectContent>
              <div className="p-2 text-xs font-semibold text-muted-foreground">
                UNCENSORED MODELS (Recommended)
              </div>
              {UNCENSORED_TEXT_MODELS.filter(m => m.vram <= config.vramLimit).map((model) => (
                <SelectItem key={model.id} value={model.id}>
                  <ModelOption model={model} />
                </SelectItem>
              ))}
              <Separator className="my-2" />
              <div className="p-2 text-xs font-semibold text-muted-foreground">
                WRITER MODELS
              </div>
              {WRITER_MODELS.filter(m => m.vram <= config.vramLimit).map((model) => (
                <SelectItem key={model.id} value={model.id}>
                  <ModelOption model={model} />
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {getModelById(config.storyGeneration) && (
            <p className="mt-2 text-sm text-muted-foreground">
              {getModelById(config.storyGeneration)?.description}
            </p>
          )}
        </CardContent>
      </Card>

      {/* Image Analysis Model */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Eye className="h-5 w-5" />
            Image Analysis
            <Badge variant="destructive">18+</Badge>
          </CardTitle>
          <CardDescription>
            Vision model for analyzing images without content restrictions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Select
            value={config.imageAnalysis}
            onValueChange={(v) => updateConfig('imageAnalysis', v)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select vision model" />
            </SelectTrigger>
            <SelectContent>
              <div className="p-2 text-xs font-semibold text-muted-foreground">
                UNCENSORED VISION MODELS
              </div>
              {UNCENSORED_VISION_MODELS.filter(m => m.vram <= config.vramLimit).map((model) => (
                <SelectItem key={model.id} value={model.id}>
                  <ModelOption model={model} />
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {getModelById(config.imageAnalysis) && (
            <p className="mt-2 text-sm text-muted-foreground">
              {getModelById(config.imageAnalysis)?.description}
            </p>
          )}
        </CardContent>
      </Card>

      {/* Portrait Generation Model */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Image className="h-5 w-5" />
            Portrait Generation
          </CardTitle>
          <CardDescription>
            Model for generating character portraits and images
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Select
            value={config.portraitGeneration}
            onValueChange={(v) => updateConfig('portraitGeneration', v)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select image gen model" />
            </SelectTrigger>
            <SelectContent>
              {IMAGE_GEN_MODELS.filter(m => m.vram <= config.vramLimit).map((model) => (
                <SelectItem key={model.id} value={model.id}>
                  <ModelOption model={model} />
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {getModelById(config.portraitGeneration) && (
            <p className="mt-2 text-sm text-muted-foreground">
              {getModelById(config.portraitGeneration)?.description}
            </p>
          )}
        </CardContent>
      </Card>

      {/* Quick Draft Model */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5" />
            Quick Draft
          </CardTitle>
          <CardDescription>
            Fast model for quick iterations and testing
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Select
            value={config.quickDraft}
            onValueChange={(v) => updateConfig('quickDraft', v)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select quick model" />
            </SelectTrigger>
            <SelectContent>
              {UNCENSORED_TEXT_MODELS
                .filter(m => m.vram <= config.vramLimit && m.speed === 'fast')
                .map((model) => (
                  <SelectItem key={model.id} value={model.id}>
                    <ModelOption model={model} />
                  </SelectItem>
                ))}
            </SelectContent>
          </Select>
          {getModelById(config.quickDraft) && (
            <p className="mt-2 text-sm text-muted-foreground">
              {getModelById(config.quickDraft)?.description}
            </p>
          )}
        </CardContent>
      </Card>

      {/* Task Mappings Info */}
      <Card>
        <CardHeader>
          <CardTitle>Automatic Task Switching</CardTitle>
          <CardDescription>
            When auto-switch is enabled, the system automatically selects the best model for each task
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {TASK_MODEL_MAPPING.slice(0, 5).map((mapping) => (
              <div key={mapping.task} className="flex items-center justify-between p-2 bg-muted rounded-lg">
                <div>
                  <p className="font-medium text-sm">{mapping.task.replace(/_/g, ' ').toUpperCase()}</p>
                  <p className="text-xs text-muted-foreground">{mapping.description}</p>
                </div>
                {config.autoSwitch && (
                  <Check className="h-4 w-4 text-green-500" />
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ModelSelector;
