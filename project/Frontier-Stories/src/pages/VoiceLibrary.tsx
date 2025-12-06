import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ArrowLeft, Play, Square, Save, Upload, Loader2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/hooks/use-toast";
import woodTexture from "@/assets/wood-texture.jpg";
import parchmentTexture from "@/assets/parchment-texture.jpg";

interface Actor {
  id: string;
  full_name: string;
  role: string;
  era: string;
  bio: string;
  voice_id: string | null;
  voice_settings: any;
  image_url: string | null;
  tags: string[];
}

const PRESET_VOICES = [
  { id: '9BWtsMINqrJLrRacOk9x', name: 'Aria', description: 'Clear, balanced female voice' },
  { id: 'CwhRBWXzGAHq8TQ4Fs17', name: 'Roger', description: 'Deep, confident male voice' },
  { id: 'EXAVITQu4vr4xnSDxMaL', name: 'Sarah', description: 'Warm, friendly female voice' },
  { id: 'FGY2WhTYpPnrIDTdsKH5', name: 'Laura', description: 'Professional female narrator' },
  { id: 'IKne3meq5aSn9XLyUdCD', name: 'Charlie', description: 'Natural, conversational male' },
  { id: 'JBFqnCBsd6RMkjVDRZzb', name: 'George', description: 'Authoritative male voice' },
  { id: 'N2lVS1w4EtoT3dr4eOWO', name: 'Callum', description: 'Young, energetic male' },
  { id: 'TX3LPaxmHKxFdv7VOQHJ', name: 'Liam', description: 'Articulate male narrator' },
  { id: 'XB0fDUnXU5powFXDhCwa', name: 'Charlotte', description: 'Elegant British female' },
  { id: 'bIHbv24MWmeRgasZH58o', name: 'Will', description: 'Friendly American male' },
  { id: 'pqHfZKP75CvOlQylNhV4', name: 'Bill', description: 'Mature, gravelly male voice' },
];

const VoiceLibrary = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [actors, setActors] = useState<Actor[]>([]);
  const [selectedActor, setSelectedActor] = useState<Actor | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [currentAudio, setCurrentAudio] = useState<HTMLAudioElement | null>(null);
  const [selectedVoiceId, setSelectedVoiceId] = useState<string>('');
  const [isTestingVoice, setIsTestingVoice] = useState<string | null>(null);
  
  // Voice settings
  const [stability, setStability] = useState(0.5);
  const [similarity, setSimilarity] = useState(0.75);
  const [style, setStyle] = useState(0.5);
  const [speakerBoost, setSpeakerBoost] = useState(true);

  const loadActors = async () => {
    const { data, error } = await supabase
      .from('actors')
      .select('*')
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

  const handleActorSelect = (actor: Actor) => {
    setSelectedActor(actor);
    setSelectedVoiceId(actor.voice_id || '');
    const settings = actor.voice_settings || {};
    setStability(settings.stability || 0.5);
    setSimilarity(settings.similarity_boost || 0.75);
    setStyle(settings.style || 0.5);
    setSpeakerBoost(settings.use_speaker_boost !== false);
  };

  const handleTestVoice = async (voiceIdOverride?: string) => {
    if (!selectedActor) return;

    if (isPlaying && currentAudio) {
      currentAudio.pause();
      currentAudio.currentTime = 0;
      setIsPlaying(false);
      setCurrentAudio(null);
      setIsTestingVoice(null);
      return;
    }

    const testVoiceId = voiceIdOverride || selectedVoiceId;
    setIsLoading(true);
    if (voiceIdOverride) {
      setIsTestingVoice(voiceIdOverride);
    }

    try {
      const sampleText = selectedActor.bio.substring(0, 200) || 
        `Howdy, I'm ${selectedActor.full_name}, ${selectedActor.role} from the ${selectedActor.era}.`;

      const { data, error } = await supabase.functions.invoke('text-to-speech', {
        body: {
          text: sampleText,
          voiceId: testVoiceId,
          voiceSettings: {
            stability,
            similarity_boost: similarity,
            style,
            use_speaker_boost: speakerBoost,
          },
        },
      });

      if (error) throw error;

      const audioBlob = new Blob([data], { type: 'audio/mpeg' });
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);

      audio.onended = () => {
        setIsPlaying(false);
        setCurrentAudio(null);
        setIsTestingVoice(null);
        URL.revokeObjectURL(audioUrl);
      };

      setCurrentAudio(audio);
      await audio.play();
      setIsPlaying(true);
    } catch (error) {
      console.error('Error testing voice:', error);
      toast({
        title: "Error",
        description: "Failed to generate voice preview",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
      if (voiceIdOverride) {
        setIsTestingVoice(null);
      }
    }
  };

  const handleSaveSettings = async () => {
    if (!selectedActor) return;

    setIsSaving(true);

    try {
      const { error } = await supabase
        .from('actors')
        .update({
          voice_id: selectedVoiceId,
          voice_settings: {
            stability,
            similarity_boost: similarity,
            style,
            use_speaker_boost: speakerBoost,
          },
        })
        .eq('id', selectedActor.id);

      if (error) throw error;

      toast({
        title: "Settings Saved",
        description: "Voice ID and settings updated successfully",
      });

      await loadActors();
    } catch (error) {
      console.error('Error saving settings:', error);
      toast({
        title: "Error",
        description: "Failed to save settings",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  useState(() => {
    loadActors();
  });

  return (
    <div className="min-h-screen relative">
      {/* Background layers */}
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
            Voice Management
          </h1>
          <p className="font-body text-muted-foreground">
            Test and customize voice settings for each character
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Actor List */}
          <Card className="lg:col-span-1 bg-card/95 backdrop-blur border-border">
            <CardHeader>
              <CardTitle className="font-western">Your Actors</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {actors.map((actor) => (
                <Button
                  key={actor.id}
                  variant={selectedActor?.id === actor.id ? "default" : "outline"}
                  className="w-full justify-start text-left h-auto py-3"
                  onClick={() => handleActorSelect(actor)}
                >
                  <div className="flex-1">
                    <div className="font-semibold">{actor.full_name}</div>
                    <div className="text-xs opacity-70">{actor.role}</div>
                  </div>
                </Button>
              ))}
              {actors.length === 0 && (
                <p className="text-sm text-muted-foreground text-center py-4">
                  No actors yet. Create one to get started.
                </p>
              )}
            </CardContent>
          </Card>

          {/* Voice Settings */}
          <Card className="lg:col-span-2 bg-card/95 backdrop-blur border-border">
            <CardHeader>
              <CardTitle className="font-western">
                {selectedActor ? `${selectedActor.full_name} - Voice Settings` : "Select an Actor"}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {selectedActor ? (
                <Tabs defaultValue="settings" className="w-full">
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="settings">Settings</TabsTrigger>
                    <TabsTrigger value="info">Character Info</TabsTrigger>
                  </TabsList>

                  <TabsContent value="settings" className="space-y-6 pt-6">
                    {/* Voice Selection */}
                    <div className="space-y-3">
                      <Label>Select Voice</Label>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-[300px] overflow-y-auto pr-2 border border-border rounded-md p-3 bg-muted/30">
                        {PRESET_VOICES.map((voice) => (
                          <Card
                            key={voice.id}
                            className={`cursor-pointer transition-all hover:shadow-md ${
                              selectedVoiceId === voice.id ? 'ring-2 ring-primary bg-primary/5' : ''
                            }`}
                            onClick={() => setSelectedVoiceId(voice.id)}
                          >
                            <CardContent className="p-3">
                              <div className="flex items-start justify-between">
                                <div className="flex-1">
                                  <h4 className="font-semibold text-sm">{voice.name}</h4>
                                  <p className="text-xs text-muted-foreground">{voice.description}</p>
                                </div>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleTestVoice(voice.id);
                                  }}
                                  disabled={isTestingVoice !== null && isTestingVoice !== voice.id}
                                  className="h-8 w-8 p-0"
                                >
                                  {isTestingVoice === voice.id ? (
                                    <Loader2 className="h-3 w-3 animate-spin" />
                                  ) : (
                                    <Play className="h-3 w-3" />
                                  )}
                                </Button>
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Selected: {PRESET_VOICES.find(v => v.id === selectedVoiceId)?.name || 'None'}
                      </p>
                    </div>

                    {/* Stability */}
                    <div className="space-y-2">
                      <Label className="flex justify-between">
                        <span>Stability</span>
                        <span className="text-muted-foreground">{stability.toFixed(2)}</span>
                      </Label>
                      <Slider
                        value={[stability]}
                        onValueChange={(v) => setStability(v[0])}
                        min={0}
                        max={1}
                        step={0.01}
                        className="w-full"
                      />
                      <p className="text-xs text-muted-foreground">
                        Higher values make the voice more consistent but less expressive
                      </p>
                    </div>

                    {/* Similarity */}
                    <div className="space-y-2">
                      <Label className="flex justify-between">
                        <span>Similarity Boost</span>
                        <span className="text-muted-foreground">{similarity.toFixed(2)}</span>
                      </Label>
                      <Slider
                        value={[similarity]}
                        onValueChange={(v) => setSimilarity(v[0])}
                        min={0}
                        max={1}
                        step={0.01}
                        className="w-full"
                      />
                      <p className="text-xs text-muted-foreground">
                        Enhances similarity to the original voice
                      </p>
                    </div>

                    {/* Style */}
                    <div className="space-y-2">
                      <Label className="flex justify-between">
                        <span>Style Exaggeration</span>
                        <span className="text-muted-foreground">{style.toFixed(2)}</span>
                      </Label>
                      <Slider
                        value={[style]}
                        onValueChange={(v) => setStyle(v[0])}
                        min={0}
                        max={1}
                        step={0.01}
                        className="w-full"
                      />
                      <p className="text-xs text-muted-foreground">
                        Higher values amplify the character's speaking style
                      </p>
                    </div>

                    {/* Speaker Boost */}
                    <div className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        id="speakerBoost"
                        checked={speakerBoost}
                        onChange={(e) => setSpeakerBoost(e.target.checked)}
                        className="rounded"
                      />
                      <Label htmlFor="speakerBoost" className="cursor-pointer">
                        Enable Speaker Boost (improves quality)
                      </Label>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-3 pt-4">
                      <Button
                        onClick={() => handleTestVoice()}
                        disabled={isLoading}
                        className="flex-1"
                        variant="outline"
                      >
                        {isLoading ? (
                          <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Generating...</>
                        ) : isPlaying ? (
                          <><Square className="mr-2 h-4 w-4" />Stop</>
                        ) : (
                          <><Play className="mr-2 h-4 w-4" />Test Voice</>
                        )}
                      </Button>
                      <Button
                        onClick={handleSaveSettings}
                        disabled={isSaving}
                        className="flex-1 bg-gradient-western"
                      >
                        {isSaving ? (
                          <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Saving...</>
                        ) : (
                          <><Save className="mr-2 h-4 w-4" />Save Settings</>
                        )}
                      </Button>
                    </div>
                  </TabsContent>

                  <TabsContent value="info" className="space-y-4 pt-6">
                    <div>
                      <Label className="text-muted-foreground">Full Name</Label>
                      <p className="font-semibold">{selectedActor.full_name}</p>
                    </div>
                    <div>
                      <Label className="text-muted-foreground">Role</Label>
                      <p className="font-semibold">{selectedActor.role}</p>
                    </div>
                    <div>
                      <Label className="text-muted-foreground">Era</Label>
                      <p className="font-semibold">{selectedActor.era}</p>
                    </div>
                    <div>
                      <Label className="text-muted-foreground">Biography</Label>
                      <p className="text-sm">{selectedActor.bio}</p>
                    </div>
                    <div>
                      <Label className="text-muted-foreground">Tags</Label>
                      <div className="flex flex-wrap gap-2 mt-2">
                        {selectedActor.tags?.map((tag) => (
                          <Badge key={tag} variant="secondary">{tag}</Badge>
                        ))}
                      </div>
                    </div>
                    <div>
                      <Label className="text-muted-foreground">Voice ID</Label>
                      <p className="text-sm font-mono">{selectedActor.voice_id || "Not set"}</p>
                    </div>
                  </TabsContent>
                </Tabs>
              ) : (
                <div className="text-center py-12 text-muted-foreground">
                  Select an actor from the list to manage their voice settings
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default VoiceLibrary;
