import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Settings as SettingsIcon, Database, Cpu, Image, FileText, Volume2, Shield, RefreshCw, Check, X, Loader2, Cloud } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { useToast } from "@/hooks/use-toast";
import AIProviderToggle from "@/components/AIProviderToggle";

interface LMStudioModel {
  id: string;
  object: string;
  owned_by: string;
}

interface ModelConfig {
  visionModel: string;
  textModel: string;
  ttsEnabled: boolean;
  ttsService: string | null;
}

interface ConnectionStatus {
  lmStudio: 'connected' | 'disconnected' | 'checking';
  database: 'connected' | 'disconnected' | 'checking';
  functions: 'connected' | 'disconnected' | 'checking';
}

const Settings = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  
  // LM Studio Settings
  const [lmStudioUrl, setLmStudioUrl] = useState(import.meta.env.VITE_LM_STUDIO_URL || "http://localhost:1234");
  const [modelsPath, setModelsPath] = useState(import.meta.env.VITE_LM_STUDIO_MODELS_PATH || "C:\\Users\\Admin\\.lmstudio\\models");
  const [availableModels, setAvailableModels] = useState<LMStudioModel[]>([]);
  const [selectedVisionModel, setSelectedVisionModel] = useState("default");
  const [selectedTextModel, setSelectedTextModel] = useState("default");
  const [loadingModels, setLoadingModels] = useState(false);
  
  // Generation Settings
  const [temperature, setTemperature] = useState([0.8]);
  const [maxTokens, setMaxTokens] = useState([4096]);
  const [topP, setTopP] = useState([0.9]);
  
  // Content Settings
  const [adultContentEnabled, setAdultContentEnabled] = useState(import.meta.env.VITE_ADULT_CONTENT_ENABLED === "true");
  const [defaultRating, setDefaultRating] = useState("adult_21_plus");
  
  // Database Settings
  const [databaseUrl, setDatabaseUrl] = useState("postgresql://postgres:postgres@localhost:5432/frontier_stories");
  
  // Connection Status
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({
    lmStudio: 'checking',
    database: 'checking',
    functions: 'checking'
  });

  // Fetch available models from LM Studio
  const fetchModels = async () => {
    setLoadingModels(true);
    try {
      const response = await fetch(`${lmStudioUrl}/v1/models`);
      if (response.ok) {
        const data = await response.json();
        setAvailableModels(data.data || []);
        setConnectionStatus(prev => ({ ...prev, lmStudio: 'connected' }));
        toast({
          title: "Models loaded",
          description: `Found ${data.data?.length || 0} models in LM Studio`,
        });
      } else {
        throw new Error("Failed to fetch models");
      }
    } catch (error) {
      setConnectionStatus(prev => ({ ...prev, lmStudio: 'disconnected' }));
      toast({
        title: "Connection failed",
        description: "Could not connect to LM Studio. Make sure it's running on port 1234.",
        variant: "destructive",
      });
    } finally {
      setLoadingModels(false);
    }
  };

  // Check functions server status
  const checkFunctionsServer = async () => {
    try {
      const functionsUrl = import.meta.env.VITE_FUNCTIONS_URL || "http://localhost:54321";
      const response = await fetch(`${functionsUrl}/health`);
      if (response.ok) {
        const data = await response.json();
        setConnectionStatus(prev => ({ ...prev, functions: 'connected' }));
        
        // Load current model config
        const configResponse = await fetch(`${functionsUrl}/config`);
        if (configResponse.ok) {
          const config: ModelConfig = await configResponse.json();
          setSelectedVisionModel(config.visionModel);
          setSelectedTextModel(config.textModel);
        }
      }
    } catch (error) {
      setConnectionStatus(prev => ({ ...prev, functions: 'disconnected' }));
    }
  };

  // Save model configuration
  const saveModelConfig = async () => {
    try {
      const functionsUrl = import.meta.env.VITE_FUNCTIONS_URL || "http://localhost:54321";
      const response = await fetch(`${functionsUrl}/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          visionModel: selectedVisionModel,
          textModel: selectedTextModel,
        }),
      });
      
      if (response.ok) {
        toast({
          title: "Settings saved",
          description: "Model configuration has been updated.",
        });
      }
    } catch (error) {
      toast({
        title: "Save failed",
        description: "Could not save settings to the functions server.",
        variant: "destructive",
      });
    }
  };

  // Check all connections on mount
  useEffect(() => {
    fetchModels();
    checkFunctionsServer();
  }, []);

  const ConnectionIndicator = ({ status }: { status: 'connected' | 'disconnected' | 'checking' }) => {
    if (status === 'checking') {
      return <Loader2 className="h-4 w-4 animate-spin text-yellow-500" />;
    }
    if (status === 'connected') {
      return <Check className="h-4 w-4 text-green-500" />;
    }
    return <X className="h-4 w-4 text-red-500" />;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 via-orange-50 to-yellow-50">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div className="flex items-center gap-2">
              <SettingsIcon className="h-6 w-6 text-amber-600" />
              <h1 className="text-2xl font-bold text-amber-900">Settings</h1>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={connectionStatus.lmStudio === 'connected' ? 'default' : 'destructive'}>
              <ConnectionIndicator status={connectionStatus.lmStudio} />
              <span className="ml-1">LM Studio</span>
            </Badge>
            <Badge variant={connectionStatus.functions === 'connected' ? 'default' : 'destructive'}>
              <ConnectionIndicator status={connectionStatus.functions} />
              <span className="ml-1">Functions</span>
            </Badge>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <Tabs defaultValue="ai-provider" className="space-y-6">
          <TabsList className="grid w-full grid-cols-6 lg:w-auto lg:inline-flex">
            <TabsTrigger value="ai-provider" className="flex items-center gap-2">
              <Cloud className="h-4 w-4" />
              <span className="hidden sm:inline">AI Provider</span>
            </TabsTrigger>
            <TabsTrigger value="lm-studio" className="flex items-center gap-2">
              <Cpu className="h-4 w-4" />
              <span className="hidden sm:inline">LM Studio</span>
            </TabsTrigger>
            <TabsTrigger value="models" className="flex items-center gap-2">
              <Image className="h-4 w-4" />
              <span className="hidden sm:inline">Models</span>
            </TabsTrigger>
            <TabsTrigger value="generation" className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              <span className="hidden sm:inline">Generation</span>
            </TabsTrigger>
            <TabsTrigger value="database" className="flex items-center gap-2">
              <Database className="h-4 w-4" />
              <span className="hidden sm:inline">Database</span>
            </TabsTrigger>
            <TabsTrigger value="content" className="flex items-center gap-2">
              <Shield className="h-4 w-4" />
              <span className="hidden sm:inline">Content</span>
            </TabsTrigger>
          </TabsList>

          {/* AI Provider Tab */}
          <TabsContent value="ai-provider">
            <AIProviderToggle />
          </TabsContent>

          {/* LM Studio Tab */}
          <TabsContent value="lm-studio">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Cpu className="h-5 w-5" />
                  LM Studio Configuration
                </CardTitle>
                <CardDescription>
                  Configure your local LM Studio connection for AI-powered image and story generation.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="lm-studio-url">LM Studio URL</Label>
                    <div className="flex gap-2">
                      <Input
                        id="lm-studio-url"
                        value={lmStudioUrl}
                        onChange={(e) => setLmStudioUrl(e.target.value)}
                        placeholder="http://localhost:1234"
                      />
                      <Button variant="outline" size="icon" onClick={fetchModels} disabled={loadingModels}>
                        {loadingModels ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                      </Button>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Default: http://localhost:1234
                    </p>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="models-path">Models Directory</Label>
                    <Input
                      id="models-path"
                      value={modelsPath}
                      onChange={(e) => setModelsPath(e.target.value)}
                      placeholder="C:\Users\Admin\.lmstudio\models"
                    />
                    <p className="text-sm text-muted-foreground">
                      Path to your LM Studio models folder
                    </p>
                  </div>
                </div>

                <Separator />

                <div className="space-y-4">
                  <h3 className="font-medium">Connection Status</h3>
                  <div className="grid gap-4 md:grid-cols-3">
                    <Card className="p-4">
                      <div className="flex items-center justify-between">
                        <span>LM Studio API</span>
                        <ConnectionIndicator status={connectionStatus.lmStudio} />
                      </div>
                    </Card>
                    <Card className="p-4">
                      <div className="flex items-center justify-between">
                        <span>Functions Server</span>
                        <ConnectionIndicator status={connectionStatus.functions} />
                      </div>
                    </Card>
                    <Card className="p-4">
                      <div className="flex items-center justify-between">
                        <span>Available Models</span>
                        <Badge variant="secondary">{availableModels.length}</Badge>
                      </div>
                    </Card>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Models Tab */}
          <TabsContent value="models">
            <div className="grid gap-6 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Image className="h-5 w-5" />
                    Vision Model (Images)
                  </CardTitle>
                  <CardDescription>
                    Select the model for generating character portraits and scene imagery.
                    Use uncensored vision models for adult content.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Selected Vision Model</Label>
                    <Select value={selectedVisionModel} onValueChange={setSelectedVisionModel}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select a vision model" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="default">Default (Auto-detect)</SelectItem>
                        {availableModels.map((model) => (
                          <SelectItem key={model.id} value={model.id}>
                            {model.id}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Recommended: Use uncensored vision models like LLaVA-uncensored or similar for 18+ content generation.
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FileText className="h-5 w-5" />
                    Text Model (Stories)
                  </CardTitle>
                  <CardDescription>
                    Select the model for generating story dialogue and narratives.
                    Use uncensored text models for adult stories.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Selected Text Model</Label>
                    <Select value={selectedTextModel} onValueChange={setSelectedTextModel}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select a text model" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="default">Default (Auto-detect)</SelectItem>
                        {availableModels.map((model) => (
                          <SelectItem key={model.id} value={model.id}>
                            {model.id}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Recommended: Use uncensored models like Llama-uncensored, Mistral-uncensored, or similar.
                  </p>
                </CardContent>
              </Card>
            </div>

            <div className="mt-6 flex justify-end">
              <Button onClick={saveModelConfig}>
                Save Model Configuration
              </Button>
            </div>
          </TabsContent>

          {/* Generation Settings Tab */}
          <TabsContent value="generation">
            <Card>
              <CardHeader>
                <CardTitle>Generation Parameters</CardTitle>
                <CardDescription>
                  Fine-tune the AI generation parameters for optimal results.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label>Temperature</Label>
                      <span className="text-sm text-muted-foreground">{temperature[0]}</span>
                    </div>
                    <Slider
                      value={temperature}
                      onValueChange={setTemperature}
                      min={0}
                      max={2}
                      step={0.1}
                    />
                    <p className="text-sm text-muted-foreground">
                      Higher values make output more creative but less predictable. Recommended: 0.7-1.0 for stories, 0.6-0.8 for images.
                    </p>
                  </div>

                  <Separator />

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label>Max Tokens</Label>
                      <span className="text-sm text-muted-foreground">{maxTokens[0]}</span>
                    </div>
                    <Slider
                      value={maxTokens}
                      onValueChange={setMaxTokens}
                      min={256}
                      max={8192}
                      step={256}
                    />
                    <p className="text-sm text-muted-foreground">
                      Maximum length of generated content. Higher values allow longer stories but take more time.
                    </p>
                  </div>

                  <Separator />

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label>Top P (Nucleus Sampling)</Label>
                      <span className="text-sm text-muted-foreground">{topP[0]}</span>
                    </div>
                    <Slider
                      value={topP}
                      onValueChange={setTopP}
                      min={0}
                      max={1}
                      step={0.05}
                    />
                    <p className="text-sm text-muted-foreground">
                      Controls diversity of output. Lower values are more focused, higher values are more diverse.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Database Tab */}
          <TabsContent value="database">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database className="h-5 w-5" />
                  Database Configuration
                </CardTitle>
                <CardDescription>
                  Configure the local PostgreSQL database connection.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="database-url">Database URL</Label>
                  <Input
                    id="database-url"
                    value={databaseUrl}
                    onChange={(e) => setDatabaseUrl(e.target.value)}
                    placeholder="postgresql://postgres:postgres@localhost:5432/frontier_stories"
                  />
                  <p className="text-sm text-muted-foreground">
                    Local PostgreSQL connection string. Default uses Docker container.
                  </p>
                </div>

                <Separator />

                <div className="space-y-4">
                  <h3 className="font-medium">Quick Access</h3>
                  <div className="grid gap-4 md:grid-cols-2">
                    <Button variant="outline" asChild>
                      <a href="http://localhost:5050" target="_blank" rel="noopener noreferrer">
                        Open pgAdmin
                      </a>
                    </Button>
                    <Button variant="outline" disabled>
                      Run Migrations
                    </Button>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    pgAdmin credentials: admin@frontier-stories.local / admin
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Content Settings Tab */}
          <TabsContent value="content">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  Content Settings
                </CardTitle>
                <CardDescription>
                  Configure content generation preferences and restrictions.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Adult Content (18+)</Label>
                    <p className="text-sm text-muted-foreground">
                      Enable generation of adult/NSFW content using uncensored models.
                    </p>
                  </div>
                  <Switch
                    checked={adultContentEnabled}
                    onCheckedChange={setAdultContentEnabled}
                  />
                </div>

                <Separator />

                <div className="space-y-2">
                  <Label>Default Content Rating</Label>
                  <Select value={defaultRating} onValueChange={setDefaultRating}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="general">General Audiences</SelectItem>
                      <SelectItem value="teen_plus">Teen+ (13+)</SelectItem>
                      <SelectItem value="adult_21_plus">Adult (21+)</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-sm text-muted-foreground">
                    Default rating for new stories and image generation.
                  </p>
                </div>

                <Separator />

                <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                  <h4 className="font-medium text-amber-900 mb-2">⚠️ Content Notice</h4>
                  <p className="text-sm text-amber-800">
                    This project is configured for adult content generation. Ensure you are using
                    appropriate uncensored models in LM Studio for the best results. All content
                    is generated locally and never leaves your machine.
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};

export default Settings;
