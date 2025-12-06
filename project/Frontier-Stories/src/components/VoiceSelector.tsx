import { useState } from "react";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import { Play, Upload, Loader2 } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/hooks/use-toast";

interface VoiceSelectorProps {
  selectedVoiceId: string;
  onVoiceSelect: (voiceId: string, method: 'preset' | 'design' | 'clone') => void;
  characterBio?: string;
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

const VoiceSelector = ({ selectedVoiceId, onVoiceSelect, characterBio }: VoiceSelectorProps) => {
  const { toast } = useToast();
  const [isTestingVoice, setIsTestingVoice] = useState<string | null>(null);
  const [currentAudio, setCurrentAudio] = useState<HTMLAudioElement | null>(null);
  
  // Voice Design state
  const [voiceDescription, setVoiceDescription] = useState('');
  const [isGeneratingVoice, setIsGeneratingVoice] = useState(false);
  
  // Voice Clone state
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [cloneName, setCloneName] = useState('');
  const [isCloning, setIsCloning] = useState(false);

  const handleTestVoice = async (voiceId: string) => {
    if (currentAudio) {
      currentAudio.pause();
      setCurrentAudio(null);
      setIsTestingVoice(null);
      return;
    }

    setIsTestingVoice(voiceId);

    try {
      const testText = characterBio?.substring(0, 150) || "Howdy partner, this is a test of my voice from the Old West days.";

      const { data, error } = await supabase.functions.invoke('text-to-speech', {
        body: { text: testText, voiceId },
      });

      if (error) throw error;

      const audioBlob = new Blob([data], { type: 'audio/mpeg' });
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);

      audio.onended = () => {
        setIsTestingVoice(null);
        setCurrentAudio(null);
        URL.revokeObjectURL(audioUrl);
      };

      setCurrentAudio(audio);
      await audio.play();
    } catch (error) {
      console.error('Error testing voice:', error);
      toast({
        title: "Error",
        description: "Failed to test voice",
        variant: "destructive",
      });
      setIsTestingVoice(null);
    }
  };

  const handleGenerateVoice = async () => {
    if (!voiceDescription.trim()) {
      toast({
        title: "Description Required",
        description: "Please describe the voice characteristics",
        variant: "destructive",
      });
      return;
    }

    setIsGeneratingVoice(true);

    try {
      const { data, error } = await supabase.functions.invoke('voice-design', {
        body: {
          description: voiceDescription,
          characterBio,
        },
      });

      if (error) throw error;

      onVoiceSelect(data.voice_id, 'design');
      
      toast({
        title: "Voice Generated",
        description: "Custom voice created successfully",
      });
    } catch (error) {
      console.error('Error generating voice:', error);
      toast({
        title: "Error",
        description: "Failed to generate custom voice",
        variant: "destructive",
      });
    } finally {
      setIsGeneratingVoice(false);
    }
  };

  const handleCloneVoice = async () => {
    if (!audioFile || !cloneName.trim()) {
      toast({
        title: "Missing Information",
        description: "Please provide both audio file and voice name",
        variant: "destructive",
      });
      return;
    }

    setIsCloning(true);

    try {
      const formData = new FormData();
      formData.append('audio', audioFile);
      formData.append('name', cloneName);
      formData.append('description', characterBio || '');

      const { data, error } = await supabase.functions.invoke('voice-clone', {
        body: formData,
      });

      if (error) throw error;

      onVoiceSelect(data.voice_id, 'clone');
      
      toast({
        title: "Voice Cloned",
        description: "Professional voice clone created successfully",
      });

      setAudioFile(null);
      setCloneName('');
    } catch (error) {
      console.error('Error cloning voice:', error);
      toast({
        title: "Error",
        description: "Failed to clone voice",
        variant: "destructive",
      });
    } finally {
      setIsCloning(false);
    }
  };

  return (
    <div className="space-y-4">
      <Label>Voice Selection Method</Label>
      <Tabs defaultValue="preset" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="preset">Preset Voices</TabsTrigger>
          <TabsTrigger value="design">Voice Design</TabsTrigger>
          <TabsTrigger value="clone">Voice Clone</TabsTrigger>
        </TabsList>

        {/* Preset Voices */}
        <TabsContent value="preset" className="space-y-3 mt-4">
          <p className="text-sm text-muted-foreground">
            Choose from ElevenLabs professional voices
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-[400px] overflow-y-auto pr-2">
            {PRESET_VOICES.map((voice) => (
              <Card
                key={voice.id}
                className={`cursor-pointer transition-all hover:shadow-lg ${
                  selectedVoiceId === voice.id ? 'ring-2 ring-primary' : ''
                }`}
                onClick={() => onVoiceSelect(voice.id, 'preset')}
              >
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <h4 className="font-semibold">{voice.name}</h4>
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
                    >
                      {isTestingVoice === voice.id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Play className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Voice Design */}
        <TabsContent value="design" className="space-y-4 mt-4">
          <p className="text-sm text-muted-foreground">
            Create a custom voice by describing characteristics like age, accent, tone, and style
          </p>
          <div className="space-y-3">
            <Label htmlFor="voiceDescription">Voice Description</Label>
            <Textarea
              id="voiceDescription"
              value={voiceDescription}
              onChange={(e) => setVoiceDescription(e.target.value)}
              placeholder="Example: Elderly Native American male, wise and resonant voice with Lakota accent, deep and gravelly tone"
              rows={4}
              className="bg-background"
            />
            <p className="text-xs text-muted-foreground">
              Include: gender, age, accent/dialect, tone (deep/raspy/bold), and speaking style
            </p>
            <Button
              onClick={handleGenerateVoice}
              disabled={isGeneratingVoice || !voiceDescription.trim()}
              className="w-full"
            >
              {isGeneratingVoice ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Generating Voice...</>
              ) : (
                <>Generate Custom Voice</>
              )}
            </Button>
          </div>
        </TabsContent>

        {/* Voice Clone */}
        <TabsContent value="clone" className="space-y-4 mt-4">
          <p className="text-sm text-muted-foreground">
            Upload audio samples to create an authentic voice clone with proper dialect
          </p>
          <div className="space-y-3">
            <div className="space-y-2">
              <Label htmlFor="cloneName">Voice Name</Label>
              <Input
                id="cloneName"
                value={cloneName}
                onChange={(e) => setCloneName(e.target.value)}
                placeholder="e.g., Black Hawk Authentic"
                className="bg-background"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="audioFile">Audio Sample (MP3, WAV)</Label>
              <Input
                id="audioFile"
                type="file"
                accept="audio/mp3,audio/wav,audio/mpeg"
                onChange={(e) => setAudioFile(e.target.files?.[0] || null)}
                className="bg-background cursor-pointer"
              />
              <p className="text-xs text-muted-foreground">
                Upload at least 1 minute of clear audio for best results
              </p>
            </div>
            <Button
              onClick={handleCloneVoice}
              disabled={isCloning || !audioFile || !cloneName.trim()}
              className="w-full"
            >
              {isCloning ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Cloning Voice...</>
              ) : (
                <><Upload className="mr-2 h-4 w-4" />Clone Voice</>
              )}
            </Button>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default VoiceSelector;
