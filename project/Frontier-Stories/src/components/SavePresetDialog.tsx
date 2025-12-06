import { useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "sonner";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";

interface SavePresetDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  currentSettings?: any;
}

const CHARACTER_STYLES = [
  "Professional",
  "Sexy", 
  "Trailer Trash",
  "Farm Girl",
  "Gymnast",
  "Volleyball Player",
  "Hooters Girl",
  "Dancer",
  "Business Woman",
  "Teacher",
  "Nurse",
  "Police Officer",
  "Cowgirl",
  "Librarian",
  "Artist",
  "Athlete",
  "Socialite",
  "Student",
  "Model",
  "Bartender",
  "Custom"
];

const CLOTHING_TYPES = [
  "Casual",
  "Formal",
  "Athletic",
  "Business",
  "Western",
  "Vintage",
  "Modern",
  "Revealing",
  "Conservative",
  "Uniform",
  "Party",
  "Beach",
  "Winter",
  "Summer",
  "Custom"
];

const CLOTHING_STYLES = [
  "Tight-Fitting",
  "Loose-Fitting",
  "Elegant",
  "Rugged",
  "Sporty",
  "Bohemian",
  "Gothic",
  "Preppy",
  "Vintage",
  "Modern Chic",
  "Streetwear",
  "Country",
  "Custom"
];

export const SavePresetDialog = ({ open, onOpenChange, currentSettings }: SavePresetDialogProps) => {
  const queryClient = useQueryClient();
  const [presetName, setPresetName] = useState("");
  const [description, setDescription] = useState("");
  const [creatorName, setCreatorName] = useState("");
  const [characterStyle, setCharacterStyle] = useState<string>("");
  const [customCharacterStyle, setCustomCharacterStyle] = useState("");
  const [clothingType, setClothingType] = useState<string>("");
  const [customClothingType, setCustomClothingType] = useState("");
  const [clothingStyle, setClothingStyle] = useState<string>("");
  const [customClothingStyle, setCustomClothingStyle] = useState("");
  const [minAge, setMinAge] = useState(18);
  const [maxAge, setMaxAge] = useState(45);
  const [tags, setTags] = useState("");
  const [isPublic, setIsPublic] = useState(true);

  const saveMutation = useMutation({
    mutationFn: async (presetData: any) => {
      const { error } = await supabase.from("portrait_presets").insert(presetData);
      if (error) throw error;
    },
    onSuccess: () => {
      toast.success("Preset saved successfully!");
      queryClient.invalidateQueries({ queryKey: ["portrait-presets"] });
      onOpenChange(false);
      resetForm();
    },
    onError: () => {
      toast.error("Failed to save preset");
    },
  });

  const resetForm = () => {
    setPresetName("");
    setDescription("");
    setCreatorName("");
    setCharacterStyle("");
    setCustomCharacterStyle("");
    setClothingType("");
    setCustomClothingType("");
    setClothingStyle("");
    setCustomClothingStyle("");
    setMinAge(18);
    setMaxAge(45);
    setTags("");
    setIsPublic(true);
  };

  const handleSave = () => {
    if (!presetName.trim()) {
      toast.error("Please enter a preset name");
      return;
    }

    const finalCharacterStyle = characterStyle === "Custom" ? customCharacterStyle : characterStyle;
    const finalClothingType = clothingType === "Custom" ? customClothingType : clothingType;
    const finalClothingStyle = clothingStyle === "Custom" ? customClothingStyle : clothingStyle;

    const presetData = {
      name: presetName,
      description,
      creator_name: creatorName || "Anonymous",
      min_age: minAge,
      max_age: maxAge,
      character_style: finalCharacterStyle,
      clothing_type: finalClothingType,
      clothing_style: finalClothingStyle,
      tags: tags ? tags.split(",").map(t => t.trim()) : [],
      is_public: isPublic,
      ...currentSettings,
    };

    saveMutation.mutate(presetData);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Save Preset</DialogTitle>
          <DialogDescription>
            Create a detailed preset with age ranges, character types, and clothing styles
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Basic Info */}
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Preset Name *</Label>
              <Input
                placeholder="e.g., Vintage Farm Girl"
                value={presetName}
                onChange={(e) => setPresetName(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label>Description</Label>
              <Textarea
                placeholder="Describe this preset..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
              />
            </div>

            <div className="space-y-2">
              <Label>Creator Name</Label>
              <Input
                placeholder="Anonymous"
                value={creatorName}
                onChange={(e) => setCreatorName(e.target.value)}
              />
            </div>
          </div>

          {/* Age Range */}
          <div className="space-y-4">
            <Label>Age Range: {minAge} - {maxAge} years</Label>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label className="text-sm text-muted-foreground">Minimum Age: {minAge}</Label>
                <Slider
                  value={[minAge]}
                  onValueChange={([val]) => setMinAge(val)}
                  min={18}
                  max={100}
                  step={1}
                />
              </div>
              <div className="space-y-2">
                <Label className="text-sm text-muted-foreground">Maximum Age: {maxAge}</Label>
                <Slider
                  value={[maxAge]}
                  onValueChange={([val]) => setMaxAge(val)}
                  min={18}
                  max={100}
                  step={1}
                />
              </div>
            </div>
          </div>

          {/* Character Style */}
          <div className="space-y-2">
            <Label>Character Style</Label>
            <Select value={characterStyle} onValueChange={setCharacterStyle}>
              <SelectTrigger>
                <SelectValue placeholder="Select character style..." />
              </SelectTrigger>
              <SelectContent className="max-h-[300px]">
                {CHARACTER_STYLES.map((style) => (
                  <SelectItem key={style} value={style}>
                    {style}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {characterStyle === "Custom" && (
              <Input
                placeholder="Enter custom character style..."
                value={customCharacterStyle}
                onChange={(e) => setCustomCharacterStyle(e.target.value)}
                className="mt-2"
              />
            )}
          </div>

          {/* Clothing Type */}
          <div className="space-y-2">
            <Label>Clothing Type</Label>
            <Select value={clothingType} onValueChange={setClothingType}>
              <SelectTrigger>
                <SelectValue placeholder="Select clothing type..." />
              </SelectTrigger>
              <SelectContent className="max-h-[300px]">
                {CLOTHING_TYPES.map((type) => (
                  <SelectItem key={type} value={type}>
                    {type}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {clothingType === "Custom" && (
              <Input
                placeholder="Enter custom clothing type..."
                value={customClothingType}
                onChange={(e) => setCustomClothingType(e.target.value)}
                className="mt-2"
              />
            )}
          </div>

          {/* Clothing Style */}
          <div className="space-y-2">
            <Label>Clothing Style</Label>
            <Select value={clothingStyle} onValueChange={setClothingStyle}>
              <SelectTrigger>
                <SelectValue placeholder="Select clothing style..." />
              </SelectTrigger>
              <SelectContent className="max-h-[300px]">
                {CLOTHING_STYLES.map((style) => (
                  <SelectItem key={style} value={style}>
                    {style}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {clothingStyle === "Custom" && (
              <Input
                placeholder="Enter custom clothing style..."
                value={customClothingStyle}
                onChange={(e) => setCustomClothingStyle(e.target.value)}
                className="mt-2"
              />
            )}
          </div>

          {/* Tags */}
          <div className="space-y-2">
            <Label>Tags (comma-separated)</Label>
            <Input
              placeholder="e.g., vintage, western, casual"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
            />
          </div>

          {/* Public Toggle */}
          <div className="flex items-center justify-between pt-4 border-t">
            <div className="space-y-0.5">
              <Label>Public Preset</Label>
              <p className="text-xs text-muted-foreground">
                Allow others to discover and use this preset
              </p>
            </div>
            <Switch
              checked={isPublic}
              onCheckedChange={setIsPublic}
            />
          </div>

          {/* Actions */}
          <div className="flex gap-2 pt-4">
            <Button
              variant="outline"
              className="flex-1"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button
              className="flex-1"
              onClick={handleSave}
              disabled={saveMutation.isPending}
            >
              {saveMutation.isPending ? "Saving..." : "Save Preset"}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};