import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { X, Upload, Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { supabase } from "@/integrations/supabase/client";
import VoiceSelector from "./VoiceSelector";

interface CreateActorDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onActorCreated?: () => void;
}

const CreateActorDialog = ({ open, onOpenChange, onActorCreated }: CreateActorDialogProps) => {
  const { toast } = useToast();
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [middleName, setMiddleName] = useState("");
  const [role, setRole] = useState("");
  const [era, setEra] = useState("1870s");
  const [characterType, setCharacterType] = useState("professional");
  const [bio, setBio] = useState("");
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState("");
  const [voiceId, setVoiceId] = useState("9BWtsMINqrJLrRacOk9x");
  const [voiceMethod, setVoiceMethod] = useState<'preset' | 'design' | 'clone'>('preset');
  const [isCreating, setIsCreating] = useState(false);

  const handleAddTag = () => {
    if (tagInput.trim() && !tags.includes(tagInput.trim())) {
      setTags([...tags, tagInput.trim()]);
      setTagInput("");
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter((tag) => tag !== tagToRemove));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!bio || bio.length < 100) {
      toast({
        title: "Biography Required",
        description: "Please provide at least 100 characters for the biography",
        variant: "destructive",
      });
      return;
    }

    setIsCreating(true);

    try {
      const fullName = [firstName, middleName, lastName].filter(Boolean).join(' ');

      const { error } = await supabase.from('actors').insert({
        first_name: firstName,
        middle_name: middleName || null,
        last_name: lastName,
        full_name: fullName,
        role,
        era,
        bio,
        tags,
        character_type: characterType,
        voice_id: voiceId,
        voice_provider: 'elevenlabs',
        voice_settings: {
          stability: 0.5,
          similarity_boost: 0.75,
          style: 0.5,
          use_speaker_boost: true,
        },
      });

      if (error) throw error;

      toast({
        title: "Actor Created",
        description: `${fullName} has been added to your voice library.`,
      });

      // Trigger callback to refresh parent
      if (onActorCreated) {
        onActorCreated();
      }

      // Reset form
      setFirstName("");
      setLastName("");
      setMiddleName("");
      setRole("");
      setEra("1870s");
      setCharacterType("professional");
      setBio("");
      setTags([]);
      setVoiceId("9BWtsMINqrJLrRacOk9x");
      onOpenChange(false);
    } catch (error) {
      console.error('Error creating actor:', error);
      toast({
        title: "Error",
        description: "Failed to create actor. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto bg-card border-border">
        <DialogHeader>
          <DialogTitle className="text-2xl font-western">Create New Actor</DialogTitle>
          <DialogDescription>
            Add a new character to your voice library with biographical details and voice profile.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Name Fields */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="firstName">First Name *</Label>
              <Input
                id="firstName"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                placeholder="Black"
                required
                className="bg-background"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="middleName">Middle Name</Label>
              <Input
                id="middleName"
                value={middleName}
                onChange={(e) => setMiddleName(e.target.value)}
                placeholder="Eagle"
                className="bg-background"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="lastName">Last Name *</Label>
              <Input
                id="lastName"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                placeholder="Hawk"
                required
                className="bg-background"
              />
            </div>
          </div>

          {/* Role and Era */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="role">Role/Title *</Label>
              <Input
                id="role"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                placeholder="Lakota Chief"
                required
                className="bg-background"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="era">Era *</Label>
              <Select value={era} onValueChange={setEra}>
                <SelectTrigger className="bg-background">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1800s">1800s (Early Century)</SelectItem>
                  <SelectItem value="1850s">1850s</SelectItem>
                  <SelectItem value="1860s">1860s</SelectItem>
                  <SelectItem value="1870s">1870s</SelectItem>
                  <SelectItem value="1880s">1880s</SelectItem>
                  <SelectItem value="1890s">1890s</SelectItem>
                  <SelectItem value="1900s">1900s (Turn of Century)</SelectItem>
                  <SelectItem value="Modern">Modern Day</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Character Type */}
          <div className="space-y-2">
            <Label htmlFor="characterType">Character Type *</Label>
            <Select value={characterType} onValueChange={setCharacterType}>
              <SelectTrigger className="bg-background">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="max-h-[300px]">
                <SelectItem value="professional">Professional</SelectItem>
                <SelectItem value="sexy">Sexy</SelectItem>
                <SelectItem value="farm-girl">Farm Girl</SelectItem>
                <SelectItem value="gymnast">Gymnast</SelectItem>
                <SelectItem value="volleyball-player">Volleyball Player</SelectItem>
                <SelectItem value="hooters-girl">Hooters Girl</SelectItem>
                <SelectItem value="dancer">Dancer</SelectItem>
                <SelectItem value="cheerleader">Cheerleader</SelectItem>
                <SelectItem value="athlete">Athlete</SelectItem>
                <SelectItem value="bartender">Bartender</SelectItem>
                <SelectItem value="secretary">Secretary</SelectItem>
                <SelectItem value="teacher">Teacher</SelectItem>
                <SelectItem value="nurse">Nurse</SelectItem>
                <SelectItem value="cowgirl">Cowgirl</SelectItem>
                <SelectItem value="model">Model</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Biography */}
          <div className="space-y-2">
            <Label htmlFor="bio">Biography *</Label>
            <Textarea
              id="bio"
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              placeholder="Write a detailed background story for this character. Include their personality, history, and significance in the Old West era..."
              rows={6}
              required
              className="bg-background resize-none"
            />
            <p className="text-xs text-muted-foreground">
              Minimum 100 characters. This helps create an authentic voice profile.
            </p>
          </div>

          {/* Tags */}
          <div className="space-y-2">
            <Label htmlFor="tags">Tags</Label>
            <div className="flex gap-2">
              <Input
                id="tags"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && (e.preventDefault(), handleAddTag())}
                placeholder="Add tags (Native American, Chief, etc.)"
                className="bg-background"
              />
              <Button type="button" onClick={handleAddTag} variant="outline">
                Add
              </Button>
            </div>
            {tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-3">
                {tags.map((tag) => (
                  <Badge key={tag} variant="secondary" className="pl-3 pr-2 py-1.5">
                    {tag}
                    <button
                      type="button"
                      onClick={() => handleRemoveTag(tag)}
                      className="ml-2 hover:text-destructive transition-colors"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}
          </div>

          {/* Voice Selection */}
          <div className="space-y-4 p-4 bg-muted rounded-lg border border-border">
            <h4 className="font-semibold text-foreground flex items-center gap-2">
              <Upload className="h-5 w-5 text-accent" />
              Voice Profile Settings
            </h4>
            <VoiceSelector
              selectedVoiceId={voiceId}
              onVoiceSelect={(id, method) => {
                setVoiceId(id);
                setVoiceMethod(method);
              }}
              characterBio={bio}
            />
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t border-border">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isCreating}
              className="flex-1 bg-gradient-western hover:opacity-90"
            >
              {isCreating ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Creating...</>
              ) : (
                <>Create Actor & Generate Voice</>
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default CreateActorDialog;
