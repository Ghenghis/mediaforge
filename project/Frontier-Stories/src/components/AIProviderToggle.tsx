import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Loader2, Cloud, Server, RefreshCw, Check, X, Wifi, WifiOff } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { 
  getAIConfig, 
  saveAIConfig, 
  checkLocalAvailability, 
  checkLMStudioStatus,
  type AIProvider 
} from "@/services/aiProvider";

interface AIProviderToggleProps {
  onProviderChange?: (provider: AIProvider) => void;
}

const AIProviderToggle = ({ onProviderChange }: AIProviderToggleProps) => {
  const { toast } = useToast();
  const [provider, setProvider] = useState<AIProvider>('cloud');
  const [checking, setChecking] = useState(false);
  const [localStatus, setLocalStatus] = useState<{
    available: boolean;
    connected: boolean;
    modelsLoaded: boolean;
    models: string[];
    error?: string;
  }>({
    available: false,
    connected: false,
    modelsLoaded: false,
    models: [],
  });

  // Load saved config on mount
  useEffect(() => {
    const config = getAIConfig();
    setProvider(config.provider);
    checkLocalStatus();
  }, []);

  const checkLocalStatus = async () => {
    setChecking(true);
    try {
      const availability = await checkLocalAvailability();
      const lmStatus = await checkLMStudioStatus();
      
      setLocalStatus({
        available: availability.available,
        connected: lmStatus.connected,
        modelsLoaded: lmStatus.modelsLoaded,
        models: lmStatus.loadedModels,
        error: availability.error || lmStatus.error,
      });
    } catch (error) {
      setLocalStatus({
        available: false,
        connected: false,
        modelsLoaded: false,
        models: [],
        error: error instanceof Error ? error.message : 'Unknown error',
      });
    } finally {
      setChecking(false);
    }
  };

  const handleProviderChange = (newProvider: AIProvider) => {
    if (newProvider === 'local' && !localStatus.available) {
      toast({
        title: "Local server not available",
        description: "Please ensure the local functions server and LM Studio are running.",
        variant: "destructive",
      });
      return;
    }

    setProvider(newProvider);
    saveAIConfig({ provider: newProvider });
    onProviderChange?.(newProvider);

    toast({
      title: "AI Provider Changed",
      description: `Now using ${newProvider === 'cloud' ? 'Cloud (Supabase)' : 'Local (LM Studio)'} for AI generation.`,
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {provider === 'cloud' ? (
            <Cloud className="h-5 w-5 text-blue-500" />
          ) : (
            <Server className="h-5 w-5 text-green-500" />
          )}
          AI Provider
        </CardTitle>
        <CardDescription>
          Choose between cloud-based AI (Lovable) or local AI (LM Studio) for generation.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <RadioGroup
          value={provider}
          onValueChange={(value) => handleProviderChange(value as AIProvider)}
          className="grid gap-4"
        >
          {/* Cloud Option */}
          <div className="flex items-start space-x-3 p-4 border rounded-lg hover:bg-accent/50 transition-colors">
            <RadioGroupItem value="cloud" id="cloud" className="mt-1" />
            <div className="flex-1 space-y-1">
              <Label htmlFor="cloud" className="flex items-center gap-2 cursor-pointer">
                <Cloud className="h-4 w-4 text-blue-500" />
                <span className="font-medium">Cloud (Lovable AI Gateway)</span>
                <Badge variant="secondary" className="ml-2">Recommended</Badge>
              </Label>
              <p className="text-sm text-muted-foreground">
                Uses Lovable's cloud AI for image and text generation. Requires internet connection.
                Fast and reliable, but may have content restrictions.
              </p>
              <div className="flex items-center gap-2 mt-2">
                <Wifi className="h-4 w-4 text-green-500" />
                <span className="text-xs text-muted-foreground">Always available with internet</span>
              </div>
            </div>
          </div>

          {/* Local Option */}
          <div className="flex items-start space-x-3 p-4 border rounded-lg hover:bg-accent/50 transition-colors">
            <RadioGroupItem 
              value="local" 
              id="local" 
              className="mt-1"
              disabled={!localStatus.available}
            />
            <div className="flex-1 space-y-1">
              <Label htmlFor="local" className="flex items-center gap-2 cursor-pointer">
                <Server className="h-4 w-4 text-green-500" />
                <span className="font-medium">Local (LM Studio)</span>
                <Badge variant="outline" className="ml-2">Uncensored</Badge>
              </Label>
              <p className="text-sm text-muted-foreground">
                Uses your local LM Studio for AI generation. Fully offline, no restrictions.
                Requires LM Studio running with models loaded.
              </p>
              
              {/* Local Status */}
              <div className="flex items-center gap-4 mt-2">
                <div className="flex items-center gap-2">
                  {checking ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : localStatus.connected ? (
                    <Check className="h-4 w-4 text-green-500" />
                  ) : (
                    <X className="h-4 w-4 text-red-500" />
                  )}
                  <span className="text-xs text-muted-foreground">
                    Functions Server: {localStatus.available ? 'Connected' : 'Disconnected'}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  {localStatus.modelsLoaded ? (
                    <Check className="h-4 w-4 text-green-500" />
                  ) : (
                    <WifiOff className="h-4 w-4 text-yellow-500" />
                  )}
                  <span className="text-xs text-muted-foreground">
                    LM Studio: {localStatus.modelsLoaded ? `${localStatus.models.length} models` : 'No models'}
                  </span>
                </div>
              </div>

              {localStatus.error && (
                <p className="text-xs text-red-500 mt-1">{localStatus.error}</p>
              )}
            </div>
          </div>
        </RadioGroup>

        {/* Refresh Button */}
        <div className="flex justify-end">
          <Button 
            variant="outline" 
            size="sm" 
            onClick={checkLocalStatus}
            disabled={checking}
          >
            {checking ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4 mr-2" />
            )}
            Check Status
          </Button>
        </div>

        {/* Info Box */}
        <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
          <h4 className="font-medium text-amber-900 mb-2">💡 When to use each provider</h4>
          <ul className="text-sm text-amber-800 space-y-1">
            <li><strong>Cloud:</strong> Quick access, no setup required, good for general content</li>
            <li><strong>Local:</strong> Full control, no restrictions, works offline, adult content support</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
};

export default AIProviderToggle;
