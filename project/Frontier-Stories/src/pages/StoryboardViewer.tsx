import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ArrowLeft, Play, Pause, SkipBack, SkipForward, Loader2, Wand2, Image as ImageIcon } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface Story {
  id: string;
  title: string;
  era: string;
  script_content: string | null;
}

interface StoryLine {
  id: string;
  line_number: number;
  text: string;
  actor_id: string;
}

interface StoryboardScene {
  id: string;
  scene_number: number;
  line_range_start: number;
  line_range_end: number;
  scene_description: string;
  image_url: string | null;
  setting: string;
  time_of_day: string;
  weather: string;
  mood: string;
}

const StoryboardViewer = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const storyId = searchParams.get('storyId');
  const { toast } = useToast();

  const [story, setStory] = useState<Story | null>(null);
  const [lines, setLines] = useState<StoryLine[]>([]);
  const [scenes, setScenes] = useState<StoryboardScene[]>([]);
  const [currentLineIndex, setCurrentLineIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [generating, setGenerating] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (storyId) {
      fetchStoryData();
    }
  }, [storyId]);

  useEffect(() => {
    if (isPlaying && currentLineIndex < lines.length - 1) {
      const timer = setTimeout(() => {
        setCurrentLineIndex(prev => prev + 1);
      }, 3000); // Auto-advance every 3 seconds
      return () => clearTimeout(timer);
    } else if (currentLineIndex >= lines.length - 1) {
      setIsPlaying(false);
    }
  }, [isPlaying, currentLineIndex, lines]);

  const fetchStoryData = async () => {
    try {
      setLoading(true);

      // Fetch story
      const { data: storyData, error: storyError } = await supabase
        .from('stories')
        .select('*')
        .eq('id', storyId)
        .single();

      if (storyError) throw storyError;
      setStory(storyData);

      // Fetch story lines
      const { data: linesData, error: linesError } = await supabase
        .from('story_lines')
        .select('*')
        .eq('story_id', storyId)
        .order('line_number', { ascending: true });

      if (linesError) throw linesError;
      setLines(linesData || []);

      // Fetch storyboard scenes
      const { data: scenesData, error: scenesError } = await supabase
        .from('storyboard_scenes')
        .select('*')
        .eq('story_id', storyId)
        .order('scene_number', { ascending: true });

      if (scenesError) throw scenesError;
      setScenes(scenesData || []);

    } catch (error: any) {
      toast({
        title: "Error",
        description: "Failed to load story data",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeScenes = async () => {
    setAnalyzing(true);

    try {
      const { data, error } = await supabase.functions.invoke('analyze-story-scenes', {
        body: { storyId }
      });

      if (error) throw error;

      toast({
        title: "Scenes Analyzed",
        description: `Identified ${data.scenes} visual scenes`,
      });

      await fetchStoryData();
    } catch (error: any) {
      toast({
        title: "Analysis Failed",
        description: error.message || "Failed to analyze scenes",
        variant: "destructive",
      });
    } finally {
      setAnalyzing(false);
    }
  };

  const handleGenerateSceneImage = async (scene: StoryboardScene) => {
    setGenerating({ ...generating, [scene.id]: true });

    try {
      const { data, error } = await supabase.functions.invoke('generate-scene-imagery', {
        body: { sceneId: scene.id }
      });

      if (error) throw error;

      toast({
        title: "Scene Generated",
        description: "4K color imagery created",
      });

      await fetchStoryData();
    } catch (error: any) {
      toast({
        title: "Generation Failed",
        description: error.message || "Failed to generate imagery",
        variant: "destructive",
      });
    } finally {
      setGenerating({ ...generating, [scene.id]: false });
    }
  };

  const handleGenerateAll = async () => {
    const scenesWithoutImages = scenes.filter(s => !s.image_url);
    
    for (const scene of scenesWithoutImages) {
      await handleGenerateSceneImage(scene);
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  };

  // Find current scene based on current line
  const currentScene = scenes.find(
    s => currentLineIndex >= s.line_range_start - 1 && currentLineIndex <= s.line_range_end - 1
  );

  const progress = lines.length > 0 ? ((currentLineIndex + 1) / lines.length) * 100 : 0;

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="bg-card border-b border-border sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/story-library')}
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back
              </Button>
              <div>
                <h1 className="font-western text-2xl text-foreground">{story?.title}</h1>
                <p className="text-sm text-muted-foreground">Visual Storyboard</p>
              </div>
            </div>
            <div className="flex gap-2">
              {scenes.length === 0 ? (
                <Button
                  onClick={handleAnalyzeScenes}
                  disabled={analyzing}
                  className="bg-gradient-western"
                >
                  {analyzing ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <Wand2 className="mr-2 h-4 w-4" />
                      Analyze Scenes
                    </>
                  )}
                </Button>
              ) : (
                <Button
                  onClick={handleGenerateAll}
                  disabled={!scenes.some(s => !s.image_url)}
                  variant="outline"
                >
                  <ImageIcon className="mr-2 h-4 w-4" />
                  Generate All Images
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="container mx-auto px-4 py-2">
        <Progress value={progress} className="h-2" />
        <p className="text-xs text-muted-foreground text-center mt-1">
          Line {currentLineIndex + 1} of {lines.length}
        </p>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Scenery Display */}
          <div>
            <Card className="overflow-hidden">
              <CardContent className="p-0">
                <div className="aspect-square bg-muted relative">
                  {currentScene?.image_url ? (
                    <img
                      src={currentScene.image_url}
                      alt={currentScene.scene_description}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex flex-col items-center justify-center text-muted-foreground p-8 text-center">
                      {currentScene ? (
                        <>
                          <ImageIcon className="h-16 w-16 mb-4" />
                          <p className="mb-4">{currentScene.scene_description}</p>
                          <Button
                            onClick={() => handleGenerateSceneImage(currentScene)}
                            disabled={generating[currentScene.id]}
                            className="bg-gradient-western"
                          >
                            {generating[currentScene.id] ? (
                              <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Generating 4K...
                              </>
                            ) : (
                              <>
                                <Wand2 className="mr-2 h-4 w-4" />
                                Generate 4K Scene
                              </>
                            )}
                          </Button>
                        </>
                      ) : (
                        <p>No scene for current dialogue</p>
                      )}
                    </div>
                  )}
                </div>
                {currentScene && (
                  <div className="p-4 space-y-2">
                    <div className="flex gap-2 flex-wrap">
                      <Badge variant="secondary">Scene {currentScene.scene_number}</Badge>
                      <Badge variant="outline">{currentScene.setting}</Badge>
                      <Badge variant="outline">{currentScene.time_of_day}</Badge>
                      <Badge variant="outline">{currentScene.weather}</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground italic">{currentScene.mood}</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Playback Controls */}
            <div className="mt-4 flex items-center justify-center gap-4">
              <Button
                variant="outline"
                size="icon"
                onClick={() => setCurrentLineIndex(Math.max(0, currentLineIndex - 1))}
                disabled={currentLineIndex === 0}
              >
                <SkipBack className="h-4 w-4" />
              </Button>
              <Button
                variant="default"
                size="icon"
                onClick={() => setIsPlaying(!isPlaying)}
                className="bg-gradient-western"
              >
                {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              </Button>
              <Button
                variant="outline"
                size="icon"
                onClick={() => setCurrentLineIndex(Math.min(lines.length - 1, currentLineIndex + 1))}
                disabled={currentLineIndex === lines.length - 1}
              >
                <SkipForward className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Script Display */}
          <div>
            <Card>
              <CardContent className="p-6">
                <h3 className="font-western text-xl mb-4">Story Script</h3>
                <div className="space-y-4 max-h-[600px] overflow-y-auto">
                  {lines.map((line, index) => (
                    <div
                      key={line.id}
                      className={`p-3 rounded-lg transition-colors ${
                        index === currentLineIndex
                          ? 'bg-primary/10 border-2 border-primary'
                          : 'bg-muted/50'
                      }`}
                    >
                      <div className="flex items-start gap-2">
                        <Badge variant="outline" className="mt-1">
                          {line.line_number}
                        </Badge>
                        <p className="flex-1 text-sm">{line.text}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Scene Thumbnails */}
        {scenes.length > 0 && (
          <div className="mt-8">
            <h3 className="font-western text-xl mb-4">All Scenes</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {scenes.map((scene) => (
                <Card
                  key={scene.id}
                  className={`cursor-pointer transition-all ${
                    currentScene?.id === scene.id ? 'ring-2 ring-primary' : ''
                  }`}
                  onClick={() => setCurrentLineIndex(scene.line_range_start - 1)}
                >
                  <CardContent className="p-2">
                    <div className="aspect-square bg-muted rounded overflow-hidden mb-2">
                      {scene.image_url ? (
                        <img
                          src={scene.image_url}
                          alt={`Scene ${scene.scene_number}`}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <ImageIcon className="h-8 w-8 text-muted-foreground" />
                        </div>
                      )}
                    </div>
                    <p className="text-xs text-center font-medium">Scene {scene.scene_number}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default StoryboardViewer;
