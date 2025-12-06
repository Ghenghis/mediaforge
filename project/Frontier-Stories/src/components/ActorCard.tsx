import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Play, Square, Loader2, User } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/hooks/use-toast";
import GeneratePortraitButton from "./GeneratePortraitButton";

interface Actor {
  id: string;
  firstName: string;
  lastName: string;
  fullName: string;
  role: string;
  era: string;
  bio: string;
  voiceId: string;
  tags: string[];
  imageUrl: string;
}

interface ActorCardProps {
  actor: Actor;
  onUpdate?: () => void;
}

const ActorCard = ({ actor, onUpdate }: ActorCardProps) => {
  const { toast } = useToast();
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [currentAudio, setCurrentAudio] = useState<HTMLAudioElement | null>(null);

  const handlePreviewVoice = async () => {
    // Stop if already playing
    if (isPlaying && currentAudio) {
      currentAudio.pause();
      currentAudio.currentTime = 0;
      setIsPlaying(false);
      setCurrentAudio(null);
      return;
    }

    setIsLoading(true);

    try {
      // Sample text based on character bio
      const sampleText = actor.bio.substring(0, 200) || `Howdy, I'm ${actor.fullName}, ${actor.role} from the ${actor.era}.`;

      const { data, error } = await supabase.functions.invoke('text-to-speech', {
        body: {
          text: sampleText,
          voiceId: actor.voiceId,
        },
      });

      if (error) throw error;

      // Create audio from the response
      const audioBlob = new Blob([data], { type: 'audio/mpeg' });
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);

      audio.onended = () => {
        setIsPlaying(false);
        setCurrentAudio(null);
        URL.revokeObjectURL(audioUrl);
      };

      audio.onerror = () => {
        toast({
          title: "Playback Error",
          description: "Failed to play audio",
          variant: "destructive",
        });
        setIsPlaying(false);
        setCurrentAudio(null);
        URL.revokeObjectURL(audioUrl);
      };

      setCurrentAudio(audio);
      await audio.play();
      setIsPlaying(true);

      toast({
        title: "Playing Voice Sample",
        description: `${actor.fullName}'s voice preview`,
      });
    } catch (error) {
      console.error('Error previewing voice:', error);
      toast({
        title: "Error",
        description: "Failed to generate voice preview. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="group relative overflow-hidden transition-all duration-500 hover:scale-105 hover:shadow-lifted border-0 bg-transparent">
      {/* Wanted Poster Background with distressed edges */}
      <div className="absolute inset-0 bg-gradient-to-b from-amber-100 via-amber-50 to-amber-100 opacity-95" 
        style={{
          clipPath: 'polygon(2% 0%, 98% 0%, 100% 2%, 100% 98%, 98% 100%, 2% 100%, 0% 98%, 0% 2%)',
        }}
      />
      
      {/* Rope border decoration */}
      <div className="absolute inset-0 pointer-events-none z-10" 
        style={{
          background: `repeating-linear-gradient(
            0deg,
            transparent,
            transparent 4px,
            rgba(139, 69, 19, 0.3) 4px,
            rgba(139, 69, 19, 0.3) 5px
          )`,
          maskImage: 'linear-gradient(transparent 8px, black 8px, black calc(100% - 8px), transparent calc(100% - 8px))',
        }}
      />
      
      {/* Corner nail/tack decorations */}
      <div className="absolute top-2 left-2 w-3 h-3 rounded-full bg-gradient-radial from-zinc-700 to-zinc-900 shadow-md z-20" />
      <div className="absolute top-2 right-2 w-3 h-3 rounded-full bg-gradient-radial from-zinc-700 to-zinc-900 shadow-md z-20" />
      <div className="absolute bottom-2 left-2 w-3 h-3 rounded-full bg-gradient-radial from-zinc-700 to-zinc-900 shadow-md z-20" />
      <div className="absolute bottom-2 right-2 w-3 h-3 rounded-full bg-gradient-radial from-zinc-700 to-zinc-900 shadow-md z-20" />
      
      <CardContent className="p-6 relative z-10">
        {/* "WANTED" header */}
        <div className="text-center mb-4">
          <h3 className="font-western text-4xl font-bold text-primary tracking-wider border-y-4 border-primary/60 py-2 [text-shadow:_2px_2px_4px_rgb(0_0_0_/_40%)]">
            WANTED
          </h3>
        </div>

        {/* Photo Frame */}
        <div className="relative mb-4 mx-auto" style={{ width: 'calc(100% - 16px)' }}>
          {/* Ornate photo border */}
          <div className="absolute -inset-2 bg-gradient-to-br from-amber-900 via-amber-700 to-amber-900 rounded-sm shadow-2xl" 
            style={{
              boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.5), 0 8px 20px rgba(0,0,0,0.6)',
            }}
          />
          
          <div className="relative aspect-square overflow-hidden rounded-sm shadow-photo">
            <img
              src={actor.imageUrl}
              alt={actor.fullName}
              className="w-full h-full object-cover sepia-[0.3] contrast-110 brightness-95"
              style={{
                filter: 'sepia(30%) contrast(110%) brightness(95%)',
              }}
            />
            {/* Vintage photo overlay */}
            <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-black/20 pointer-events-none" />
            <div className="absolute inset-0 bg-texture-paper opacity-10 mix-blend-overlay pointer-events-none" />
          </div>
        </div>

        {/* Actor Details */}
        <div className="text-center space-y-3">
          <div className="space-y-1">
            <h4 className="font-western text-2xl font-bold text-foreground tracking-wide [text-shadow:_1px_1px_2px_rgb(0_0_0_/_30%)]">
              {actor.fullName}
            </h4>
            <p className="font-body text-lg italic text-primary font-semibold">
              {actor.role}
            </p>
            <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground font-body">
              <User className="h-4 w-4" />
              <span className="font-semibold">{actor.era}</span>
            </div>
          </div>

          <p className="font-body text-sm text-foreground/80 leading-relaxed px-2 min-h-[60px]">
            {actor.bio}
          </p>

          {/* Tags */}
          <div className="flex flex-wrap gap-2 justify-center pt-2">
            {actor.tags.map((tag) => (
              <Badge
                key={tag}
                variant="secondary"
                className="font-body text-xs px-3 py-1 bg-primary/20 text-primary border border-primary/40 shadow-sm font-semibold"
              >
                {tag}
              </Badge>
            ))}
          </div>

          {/* Action Buttons */}
          <div className="space-y-2 mt-4">
            <GeneratePortraitButton
              actorId={actor.id}
              fullName={actor.fullName}
              role={actor.role}
              era={actor.era}
              onGenerated={onUpdate}
            />
            
            <Button
              onClick={handlePreviewVoice}
              disabled={isLoading}
              className="w-full bg-gradient-western text-primary-foreground font-body font-bold shadow-photo hover:shadow-lifted transition-all border-2 border-primary/30 hover:scale-105 disabled:opacity-50"
              size="lg"
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Generating...
                </>
              ) : isPlaying ? (
                <>
                  <Square className="mr-2 h-5 w-5" />
                  Stop Voice
                </>
              ) : (
                <>
                  <Play className="mr-2 h-5 w-5" />
                  Preview Voice
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Distressed texture overlay on entire card */}
        <div className="absolute inset-0 bg-texture-paper opacity-20 mix-blend-multiply pointer-events-none rounded-lg" />
      </CardContent>
    </Card>
  );
};

export default ActorCard;
