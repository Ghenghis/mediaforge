import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Slider } from "@/components/ui/slider";
import { ArrowLeft, Play, Square, Download, Loader2, Plus, X, Volume2, Volume1, Save, BookOpen } from "lucide-react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/hooks/use-toast";
import woodTexture from "@/assets/wood-texture.jpg";
import parchmentTexture from "@/assets/parchment-texture.jpg";
import SceneryGenerator from "@/components/SceneryGenerator";

interface Actor {
  id: string;
  full_name: string;
  role: string;
  voice_id: string | null;
  image_url: string | null;
}

interface StoryLine {
  id: string;
  actorId: string;
  text: string;
  audioUrl?: string;
  isGenerating?: boolean;
  volume: number; // 0 to 1
  fadeIn: boolean;
  fadeOut: boolean;
}

const StoryCreation = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [searchParams] = useSearchParams();
  const storyId = searchParams.get('id');
  
  const [actors, setActors] = useState<Actor[]>([]);
  const [selectedActors, setSelectedActors] = useState<string[]>([]);
  const [storyTitle, setStoryTitle] = useState("");
  const [storyDescription, setStoryDescription] = useState("");
  const [storyEra, setStoryEra] = useState("1870s");
  const [storyLines, setStoryLines] = useState<StoryLine[]>([]);
  const [currentLine, setCurrentLine] = useState("");
  const [currentActor, setCurrentActor] = useState("");
  const [isPlaying, setIsPlaying] = useState(false);
  const [isGeneratingAll, setIsGeneratingAll] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [currentAudio, setCurrentAudio] = useState<HTMLAudioElement | null>(null);
  const [audioContext, setAudioContext] = useState<AudioContext | null>(null);
  const [masterVolume, setMasterVolume] = useState(1);
  const [currentlyPlayingLine, setCurrentlyPlayingLine] = useState<string | null>(null);
  const [pauseDuration, setPauseDuration] = useState(0.5);
  const [isExporting, setIsExporting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [currentStoryId, setCurrentStoryId] = useState<string | null>(storyId);

  useEffect(() => {
    loadActors();
    // Initialize Web Audio API context
    const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
    setAudioContext(ctx);

    // Check for template parameter
    const templateParam = searchParams.get('template');
    if (templateParam) {
      try {
        const template = JSON.parse(decodeURIComponent(templateParam));
        loadTemplate(template);
      } catch (error) {
        console.error('Error loading template:', error);
        toast({
          title: "Error",
          description: "Failed to load template",
          variant: "destructive",
        });
      }
    }
    // Load story if editing
    else if (storyId) {
      loadStory(storyId);
    }

    return () => {
      if (ctx) {
        ctx.close();
      }
    };
  }, [storyId, searchParams]);

  const loadStory = async (id: string) => {
    try {
      // Load story metadata
      const { data: storyData, error: storyError } = await supabase
        .from('stories')
        .select('*')
        .eq('id', id)
        .single();

      if (storyError) throw storyError;

      setStoryTitle(storyData.title);
      setStoryDescription(storyData.description || '');
      setStoryEra(storyData.era || '1870s');
      setMasterVolume(Number(storyData.master_volume) || 1);
      setPauseDuration(Number(storyData.pause_duration) || 0.5);
      setCurrentStoryId(id);

      // Load story lines
      const { data: linesData, error: linesError } = await supabase
        .from('story_lines')
        .select('*')
        .eq('story_id', id)
        .order('line_number', { ascending: true });

      if (linesError) throw linesError;

      const loadedLines: StoryLine[] = linesData.map((line) => ({
        id: line.id,
        actorId: line.actor_id,
        text: line.text,
        audioUrl: line.audio_url || undefined,
        volume: Number(line.volume),
        fadeIn: line.fade_in,
        fadeOut: line.fade_out,
      }));

      setStoryLines(loadedLines);

      // Set selected actors
      const actorIds = [...new Set(loadedLines.map(line => line.actorId))];
      setSelectedActors(actorIds);

      toast({
        title: "Story Loaded",
        description: `"${storyData.title}" is ready for editing`,
      });
    } catch (error) {
      console.error('Error loading story:', error);
      toast({
        title: "Error",
        description: "Failed to load story",
        variant: "destructive",
      });
    }
  };

  const loadTemplate = async (template: any) => {
    try {
      // Set story metadata from template
      setStoryTitle(template.title);
      setStoryDescription(template.description);
      setStoryEra(template.era);

      // Load all actors to match against template roles
      const { data: allActors, error: actorsError } = await supabase
        .from('actors')
        .select('*');

      if (actorsError) throw actorsError;

      // Create story lines from template
      const templateLines: StoryLine[] = [];
      const actorsToSelect: string[] = [];

      for (let i = 0; i < template.lines.length; i++) {
        const line = template.lines[i];
        
        // Try to find matching actor by name
        const matchingActor = allActors?.find(
          (a) => 
            a.first_name.toLowerCase() === line.actorFirstName.toLowerCase() &&
            a.last_name.toLowerCase() === line.actorLastName.toLowerCase()
        );

        if (matchingActor) {
          // Use existing actor
          templateLines.push({
            id: `line-${Date.now()}-${i}`,
            actorId: matchingActor.id,
            text: line.text,
            volume: 0.8,
            fadeIn: false,
            fadeOut: false,
          });
          
          if (!actorsToSelect.includes(matchingActor.id)) {
            actorsToSelect.push(matchingActor.id);
          }
        } else {
          // Actor doesn't exist, just add the line without an actor for now
          // User will need to assign actors manually or create them
          toast({
            title: "Actor Not Found",
            description: `Actor "${line.actorFirstName} ${line.actorLastName}" not found. Please create the actor and assign manually.`,
          });
        }
      }

      setStoryLines(templateLines);
      setSelectedActors(actorsToSelect);

      toast({
        title: "Template Loaded",
        description: `Loaded "${template.title}" template with ${templateLines.length} lines`,
      });
    } catch (error) {
      console.error('Error loading template:', error);
      throw error;
    }
  };

  const handleSaveStory = async () => {
    if (!storyTitle.trim()) {
      toast({
        title: "Title Required",
        description: "Please enter a title for your story",
        variant: "destructive",
      });
      return;
    }

    if (storyLines.length === 0) {
      toast({
        title: "No Content",
        description: "Add at least one dialogue line before saving",
        variant: "destructive",
      });
      return;
    }

    setIsSaving(true);

    try {
      let savedStoryId = currentStoryId;

      if (savedStoryId) {
        // Update existing story
        const { error: updateError } = await supabase
          .from('stories')
          .update({
            title: storyTitle,
            description: storyDescription,
            era: storyEra,
            master_volume: masterVolume,
            pause_duration: pauseDuration,
            status: 'draft',
          })
          .eq('id', savedStoryId);

        if (updateError) throw updateError;

        // Delete existing lines
        const { error: deleteError } = await supabase
          .from('story_lines')
          .delete()
          .eq('story_id', savedStoryId);

        if (deleteError) throw deleteError;
      } else {
        // Create new story
        const { data: newStory, error: createError } = await supabase
          .from('stories')
          .insert({
            title: storyTitle,
            description: storyDescription,
            era: storyEra,
            master_volume: masterVolume,
            pause_duration: pauseDuration,
            status: 'draft',
          })
          .select()
          .single();

        if (createError) throw createError;

        savedStoryId = newStory.id;
        setCurrentStoryId(savedStoryId);
      }

      // Insert story lines
      const linesToInsert = storyLines.map((line, index) => ({
        story_id: savedStoryId,
        actor_id: line.actorId,
        line_number: index + 1,
        text: line.text,
        audio_url: line.audioUrl || null,
        volume: line.volume,
        fade_in: line.fadeIn,
        fade_out: line.fadeOut,
      }));

      const { error: linesError } = await supabase
        .from('story_lines')
        .insert(linesToInsert);

      if (linesError) throw linesError;

      toast({
        title: "Story Saved",
        description: `"${storyTitle}" has been saved successfully`,
      });
    } catch (error) {
      console.error('Error saving story:', error);
      toast({
        title: "Error",
        description: "Failed to save story",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const loadActors = async () => {
    const { data, error } = await supabase
      .from('actors')
      .select('id, full_name, role, voice_id, image_url')
      .order('created_at', { ascending: false });

    if (error) {
      toast({
        title: "Error",
        description: "Failed to load actors",
        variant: "destructive",
      });
      return;
    }

    setActors(data || []);
  };

  const handleActorToggle = (actorId: string) => {
    setSelectedActors(prev =>
      prev.includes(actorId)
        ? prev.filter(id => id !== actorId)
        : [...prev, actorId]
    );
  };

  const handleBulkVoiceTest = async () => {
    if (selectedActors.length === 0) {
      toast({
        title: "No Actors Selected",
        description: "Please select at least one actor to test",
        variant: "destructive",
      });
      return;
    }

    setIsTesting(true);
    let currentIndex = 0;

    const testNextActor = async () => {
      if (currentIndex >= selectedActors.length) {
        setIsTesting(false);
        toast({
          title: "Testing Complete",
          description: "All actor voices have been previewed",
        });
        return;
      }

      const actorId = selectedActors[currentIndex];
      const actor = actors.find(a => a.id === actorId);
      if (!actor) {
        currentIndex++;
        testNextActor();
        return;
      }

      try {
        const testText = `Howdy, I'm ${actor.full_name}, ${actor.role}. This is my voice from the Old West.`;

        const { data, error } = await supabase.functions.invoke('text-to-speech', {
          body: {
            text: testText,
            voiceId: actor.voice_id,
          },
        });

        if (error) throw error;

        const audioBlob = new Blob([data], { type: 'audio/mpeg' });
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);

        audio.onended = () => {
          URL.revokeObjectURL(audioUrl);
          currentIndex++;
          setTimeout(() => testNextActor(), 1000); // 1 second pause between actors
        };

        audio.onerror = () => {
          URL.revokeObjectURL(audioUrl);
          currentIndex++;
          testNextActor();
        };

        await audio.play();

        toast({
          title: `Playing: ${actor.full_name}`,
          description: `${currentIndex + 1} of ${selectedActors.length}`,
        });
      } catch (error) {
        console.error('Error testing voice:', error);
        currentIndex++;
        testNextActor();
      }
    };

    testNextActor();
  };

  const handleAddLine = () => {
    if (!currentLine.trim() || !currentActor) {
      toast({
        title: "Missing Information",
        description: "Please select an actor and enter dialogue",
        variant: "destructive",
      });
      return;
    }

    const newLine: StoryLine = {
      id: `line_${Date.now()}`,
      actorId: currentActor,
      text: currentLine,
      volume: 0.8, // Default volume
      fadeIn: false,
      fadeOut: false,
    };

    setStoryLines([...storyLines, newLine]);
    setCurrentLine("");
  };

  const handleRemoveLine = (lineId: string) => {
    setStoryLines(storyLines.filter(line => line.id !== lineId));
  };

  const handleGenerateLineAudio = async (lineId: string) => {
    const line = storyLines.find(l => l.id === lineId);
    if (!line) return;

    const actor = actors.find(a => a.id === line.actorId);
    if (!actor || !actor.voice_id) {
      toast({
        title: "Voice Not Available",
        description: "This actor doesn't have a voice configured",
        variant: "destructive",
      });
      return;
    }

    setStoryLines(storyLines.map(l =>
      l.id === lineId ? { ...l, isGenerating: true } : l
    ));

    try {
      const { data, error } = await supabase.functions.invoke('text-to-speech', {
        body: {
          text: line.text,
          voiceId: actor.voice_id,
        },
      });

      if (error) throw error;

      const audioBlob = new Blob([data], { type: 'audio/mpeg' });
      const audioUrl = URL.createObjectURL(audioBlob);

      setStoryLines(storyLines.map(l =>
        l.id === lineId ? { ...l, audioUrl, isGenerating: false } : l
      ));

      toast({
        title: "Audio Generated",
        description: `Audio for ${actor.full_name}'s line is ready`,
      });
    } catch (error) {
      console.error('Error generating audio:', error);
      toast({
        title: "Error",
        description: "Failed to generate audio",
        variant: "destructive",
      });
      setStoryLines(storyLines.map(l =>
        l.id === lineId ? { ...l, isGenerating: false } : l
      ));
    }
  };

  const handleGenerateAllAudio = async () => {
    setIsGeneratingAll(true);

    for (const line of storyLines) {
      if (!line.audioUrl) {
        await handleGenerateLineAudio(line.id);
      }
    }

    setIsGeneratingAll(false);
    toast({
      title: "All Audio Generated",
      description: "Your story is ready to play",
    });
  };

  const playAudioWithVolume = async (audioUrl: string, volume: number, fadeIn: boolean, fadeOut: boolean): Promise<void> => {
    return new Promise(async (resolve, reject) => {
      if (!audioContext) {
        reject(new Error('Audio context not available'));
        return;
      }

      try {
        // Fetch audio data
        const response = await fetch(audioUrl);
        const arrayBuffer = await response.arrayBuffer();
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

        // Create nodes
        const source = audioContext.createBufferSource();
        const gainNode = audioContext.createGain();

        source.buffer = audioBuffer;
        source.connect(gainNode);
        gainNode.connect(audioContext.destination);

        // Calculate final volume (line volume * master volume)
        const finalVolume = volume * masterVolume;
        const duration = audioBuffer.duration;

        // Apply fade effects
        if (fadeIn) {
          gainNode.gain.setValueAtTime(0, audioContext.currentTime);
          gainNode.gain.linearRampToValueAtTime(finalVolume, audioContext.currentTime + 0.5);
        } else {
          gainNode.gain.setValueAtTime(finalVolume, audioContext.currentTime);
        }

        if (fadeOut) {
          gainNode.gain.setValueAtTime(finalVolume, audioContext.currentTime + duration - 0.5);
          gainNode.gain.linearRampToValueAtTime(0, audioContext.currentTime + duration);
        }

        source.onended = () => {
          source.disconnect();
          gainNode.disconnect();
          resolve();
        };

        source.start(0);
      } catch (error) {
        reject(error);
      }
    });
  };

  const handlePlayStory = async () => {
    if (isPlaying) {
      setIsPlaying(false);
      setCurrentlyPlayingLine(null);
      if (audioContext) {
        await audioContext.close();
        const newCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
        setAudioContext(newCtx);
      }
      return;
    }

    const linesWithAudio = storyLines.filter(line => line.audioUrl);
    if (linesWithAudio.length === 0) {
      toast({
        title: "No Audio Available",
        description: "Generate audio for at least one line first",
        variant: "destructive",
      });
      return;
    }

    setIsPlaying(true);

    try {
      for (let i = 0; i < linesWithAudio.length; i++) {
        if (!isPlaying) break;

        const line = linesWithAudio[i];
        setCurrentlyPlayingLine(line.id);

        await playAudioWithVolume(line.audioUrl!, line.volume, line.fadeIn, line.fadeOut);
        
        // Small pause between lines
        await new Promise(resolve => setTimeout(resolve, 500));
      }

      setIsPlaying(false);
      setCurrentlyPlayingLine(null);
      toast({
        title: "Story Complete",
        description: "The story has finished playing",
      });
    } catch (error) {
      console.error('Error playing story:', error);
      setIsPlaying(false);
      setCurrentlyPlayingLine(null);
      toast({
        title: "Playback Error",
        description: "Failed to play story",
        variant: "destructive",
      });
    }
  };

  const handleUpdateLineVolume = (lineId: string, volume: number) => {
    setStoryLines(storyLines.map(line =>
      line.id === lineId ? { ...line, volume } : line
    ));
  };

  const handleToggleFade = (lineId: string, fadeType: 'fadeIn' | 'fadeOut') => {
    setStoryLines(storyLines.map(line =>
      line.id === lineId ? { ...line, [fadeType]: !line[fadeType] } : line
    ));
  };

  const handleTestLine = async (line: StoryLine) => {
    if (!line.audioUrl || !audioContext) return;

    try {
      await playAudioWithVolume(line.audioUrl, line.volume, line.fadeIn, line.fadeOut);
      toast({
        title: "Line Played",
        description: "Audio preview completed",
      });
    } catch (error) {
      console.error('Error testing line:', error);
      toast({
        title: "Error",
        description: "Failed to play audio",
        variant: "destructive",
      });
    }
  };

  const handleExportStory = async () => {
    const linesWithAudio = storyLines.filter(line => line.audioUrl);
    
    if (linesWithAudio.length === 0) {
      toast({
        title: "No Audio to Export",
        description: "Generate audio for at least one line first",
        variant: "destructive",
      });
      return;
    }

    if (!storyTitle.trim()) {
      toast({
        title: "Story Title Required",
        description: "Please enter a title for your story",
        variant: "destructive",
      });
      return;
    }

    setIsExporting(true);

    try {
      console.log('Exporting story with', linesWithAudio.length, 'lines');

      const { data, error } = await supabase.functions.invoke('export-story', {
        body: {
          storyLines: linesWithAudio.map(line => ({
            audioUrl: line.audioUrl,
            volume: line.volume,
            fadeIn: line.fadeIn,
            fadeOut: line.fadeOut,
          })),
          masterVolume,
          pauseDuration,
        },
      });

      if (error) throw error;

      // Create blob from response and trigger download
      const blob = new Blob([data], { type: 'audio/mpeg' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${storyTitle.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_story.mp3`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast({
        title: "Story Exported",
        description: `${storyTitle} has been downloaded as MP3`,
      });
    } catch (error) {
      console.error('Error exporting story:', error);
      toast({
        title: "Export Failed",
        description: "Failed to export story. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsExporting(false);
    }
  };

  const getActorById = (actorId: string) => {
    return actors.find(a => a.id === actorId);
  };

  return (
    <div className="min-h-screen relative">
      {/* Background */}
      <div 
        className="fixed inset-0 pointer-events-none opacity-40" 
        style={{ 
          backgroundImage: `url(${woodTexture})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundAttachment: 'fixed'
        }} 
      />
      <div 
        className="fixed inset-0 pointer-events-none opacity-30" 
        style={{ 
          backgroundImage: `url(${parchmentTexture})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundAttachment: 'fixed',
          mixBlendMode: 'multiply'
        }} 
      />

      {/* Content */}
      <div className="relative z-10 container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <Button
            variant="ghost"
            onClick={() => navigate('/')}
            className="mb-4 text-foreground hover:text-primary"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Library
          </Button>
          <h1 className="font-western text-5xl text-foreground mb-2 [text-shadow:_2px_2px_4px_rgb(0_0_0_/_40%)]">
            {currentStoryId ? 'Edit Story' : 'Story Creation'}
          </h1>
          <p className="font-body text-muted-foreground">
            Create multi-actor narratives with voice synthesis
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Actor Selection */}
          <Card className="bg-card/95 backdrop-blur border-border">
            <CardHeader>
              <CardTitle className="font-western flex justify-between items-center">
                Select Actors
                <Button
                  onClick={handleBulkVoiceTest}
                  disabled={isTesting || selectedActors.length === 0}
                  size="sm"
                  variant="outline"
                >
                  {isTesting ? (
                    <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Testing...</>
                  ) : (
                    <><Play className="mr-2 h-4 w-4" />Test All</>
                  )}
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {actors.map((actor) => (
                <div
                  key={actor.id}
                  className="flex items-center space-x-3 p-3 rounded-lg border border-border hover:bg-accent/50 transition-colors"
                >
                  <Checkbox
                    checked={selectedActors.includes(actor.id)}
                    onCheckedChange={() => handleActorToggle(actor.id)}
                  />
                  <div className="flex-1">
                    <p className="font-semibold">{actor.full_name}</p>
                    <p className="text-xs text-muted-foreground">{actor.role}</p>
                  </div>
                </div>
              ))}
              {actors.length === 0 && (
                <p className="text-sm text-muted-foreground text-center py-4">
                  No actors available. Create actors first.
                </p>
              )}
            </CardContent>
          </Card>

          {/* Story Composition */}
          <Card className="lg:col-span-2 bg-card/95 backdrop-blur border-border">
            <CardHeader>
              <CardTitle className="font-western">Story Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Story Info */}
              <div className="space-y-4">
                <div>
                  <Label htmlFor="title">Story Title *</Label>
                  <Input
                    id="title"
                    value={storyTitle}
                    onChange={(e) => setStoryTitle(e.target.value)}
                    placeholder="The Legend of Black Hawk"
                    className="bg-background"
                  />
                </div>
                <div>
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    value={storyDescription}
                    onChange={(e) => setStoryDescription(e.target.value)}
                    placeholder="A tale of courage and wisdom from the Old West..."
                    rows={3}
                    className="bg-background"
                  />
                </div>
                <div>
                  <Label htmlFor="era">Era</Label>
                  <select
                    id="era"
                    value={storyEra}
                    onChange={(e) => setStoryEra(e.target.value)}
                    className="w-full p-2 rounded-md border border-border bg-background"
                  >
                    <option value="1800s">1800s (Early Century)</option>
                    <option value="1850s">1850s</option>
                    <option value="1860s">1860s</option>
                    <option value="1870s">1870s</option>
                    <option value="1880s">1880s</option>
                    <option value="1890s">1890s</option>
                    <option value="1900s">1900s (Turn of Century)</option>
                  </select>
                </div>
              </div>

              <Separator />

              {/* Period Scenery Generator */}
              <SceneryGenerator era={storyEra} storyId={currentStoryId || undefined} />

              <Separator />

              {/* Add Dialogue Line */}
              <div className="space-y-4">
                <Label>Add Dialogue</Label>
                <div className="space-y-3">
                  <select
                    value={currentActor}
                    onChange={(e) => setCurrentActor(e.target.value)}
                    className="w-full p-2 rounded-md border border-border bg-background"
                  >
                    <option value="">Select actor...</option>
                    {selectedActors.map(actorId => {
                      const actor = getActorById(actorId);
                      return actor ? (
                        <option key={actor.id} value={actor.id}>
                          {actor.full_name}
                        </option>
                      ) : null;
                    })}
                  </select>
                  <Textarea
                    value={currentLine}
                    onChange={(e) => setCurrentLine(e.target.value)}
                    placeholder="Enter the character's dialogue..."
                    rows={3}
                    className="bg-background"
                  />
                  <Button onClick={handleAddLine} className="w-full">
                    <Plus className="mr-2 h-4 w-4" />
                    Add Line
                  </Button>
                </div>
              </div>

              <Separator />

              {/* Master Volume Control */}
              <div className="p-4 bg-accent/30 rounded-lg border border-border space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <Label className="flex items-center gap-2">
                      <Volume2 className="h-4 w-4" />
                      Master Volume
                    </Label>
                    <span className="text-sm font-mono">{Math.round(masterVolume * 100)}%</span>
                  </div>
                  <Slider
                    value={[masterVolume]}
                    onValueChange={(v) => setMasterVolume(v[0])}
                    min={0}
                    max={1}
                    step={0.01}
                    className="w-full"
                  />
                </div>

                {/* Pause Duration Control */}
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <Label className="text-sm">
                      Pause Between Lines
                    </Label>
                    <span className="text-sm font-mono">{pauseDuration.toFixed(1)}s</span>
                  </div>
                  <Slider
                    value={[pauseDuration]}
                    onValueChange={(v) => setPauseDuration(v[0])}
                    min={0}
                    max={3}
                    step={0.1}
                    className="w-full"
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Silence duration between character lines
                  </p>
                </div>
              </div>

              <Separator />

              {/* Story Timeline */}
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <Label>Story Timeline ({storyLines.length} lines)</Label>
                  <div className="flex gap-2 flex-wrap">
                    <Button
                      onClick={handleSaveStory}
                      disabled={isSaving || storyLines.length === 0}
                      size="sm"
                      variant="outline"
                    >
                      {isSaving ? (
                        <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Saving...</>
                      ) : (
                        <><Save className="mr-2 h-4 w-4" />Save</>
                      )}
                    </Button>
                    <Button
                      onClick={() => navigate('/story-library')}
                      size="sm"
                      variant="outline"
                    >
                      <BookOpen className="mr-2 h-4 w-4" />
                      Library
                    </Button>
                    <Button
                      onClick={handleGenerateAllAudio}
                      disabled={isGeneratingAll || storyLines.length === 0}
                      size="sm"
                      variant="outline"
                    >
                      {isGeneratingAll ? (
                        <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Generating...</>
                      ) : (
                        <>Generate All</>
                      )}
                    </Button>
                    <Button
                      onClick={handlePlayStory}
                      disabled={storyLines.length === 0}
                      size="sm"
                      variant="outline"
                    >
                      {isPlaying ? (
                        <><Square className="mr-2 h-4 w-4" />Stop</>
                      ) : (
                        <><Play className="mr-2 h-4 w-4" />Play</>
                      )}
                    </Button>
                    <Button
                      onClick={handleExportStory}
                      disabled={isExporting || storyLines.filter(l => l.audioUrl).length === 0}
                      size="sm"
                      className="bg-gradient-western"
                    >
                      {isExporting ? (
                        <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Exporting...</>
                      ) : (
                        <><Download className="mr-2 h-4 w-4" />Export MP3</>
                      )}
                    </Button>
                  </div>
                </div>

                <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2">
                  {storyLines.map((line, index) => {
                    const actor = getActorById(line.actorId);
                    const isCurrentlyPlaying = currentlyPlayingLine === line.id;
                    return (
                      <div
                        key={line.id}
                        className={`p-4 rounded-lg border space-y-3 transition-all ${
                          isCurrentlyPlaying
                            ? 'border-primary bg-primary/10 shadow-lg'
                            : 'border-border bg-background'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <Badge variant="secondary">
                                {index + 1}. {actor?.full_name}
                              </Badge>
                              {isCurrentlyPlaying && (
                                <Badge variant="default" className="animate-pulse">
                                  Playing
                                </Badge>
                              )}
                            </div>
                            <p className="text-sm">{line.text}</p>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRemoveLine(line.id)}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>

                        {/* Audio Generation Status */}
                        <div className="flex gap-2 flex-wrap">
                          {line.audioUrl ? (
                            <>
                              <Badge variant="default">Audio Ready</Badge>
                              <Button
                                onClick={() => handleTestLine(line)}
                                disabled={isPlaying}
                                size="sm"
                                variant="outline"
                              >
                                <Play className="mr-1 h-3 w-3" />
                                Test
                              </Button>
                            </>
                          ) : (
                            <Button
                              onClick={() => handleGenerateLineAudio(line.id)}
                              disabled={line.isGenerating}
                              size="sm"
                              variant="outline"
                            >
                              {line.isGenerating ? (
                                <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Generating...</>
                              ) : (
                                <>Generate Audio</>
                              )}
                            </Button>
                          )}
                        </div>

                        {/* Audio Mixing Controls */}
                        {line.audioUrl && (
                          <div className="pt-3 border-t border-border space-y-3">
                            {/* Volume Control */}
                            <div>
                              <div className="flex items-center justify-between mb-2">
                                <Label className="text-xs flex items-center gap-1">
                                  <Volume1 className="h-3 w-3" />
                                  Volume
                                </Label>
                                <span className="text-xs font-mono">{Math.round(line.volume * 100)}%</span>
                              </div>
                              <Slider
                                value={[line.volume]}
                                onValueChange={(v) => handleUpdateLineVolume(line.id, v[0])}
                                min={0}
                                max={1}
                                step={0.01}
                                className="w-full"
                              />
                            </div>

                            {/* Fade Effects */}
                            <div className="flex gap-4">
                              <div className="flex items-center space-x-2">
                                <Checkbox
                                  id={`fade-in-${line.id}`}
                                  checked={line.fadeIn}
                                  onCheckedChange={() => handleToggleFade(line.id, 'fadeIn')}
                                />
                                <Label htmlFor={`fade-in-${line.id}`} className="text-xs cursor-pointer">
                                  Fade In
                                </Label>
                              </div>
                              <div className="flex items-center space-x-2">
                                <Checkbox
                                  id={`fade-out-${line.id}`}
                                  checked={line.fadeOut}
                                  onCheckedChange={() => handleToggleFade(line.id, 'fadeOut')}
                                />
                                <Label htmlFor={`fade-out-${line.id}`} className="text-xs cursor-pointer">
                                  Fade Out
                                </Label>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                  {storyLines.length === 0 && (
                    <p className="text-sm text-muted-foreground text-center py-8">
                      No dialogue lines yet. Add your first line above.
                    </p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default StoryCreation;
