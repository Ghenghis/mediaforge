import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";
import { Loader2, Wand2, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";

interface PortraitCustomizationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onGenerate: (customization: PortraitCustomization) => Promise<void>;
  actorName: string;
}

export interface PortraitCustomization {
  age: number;
  weathering: number;
  detailLevel: number;
  clothingStyle: number;
  coverage: number;
  fit: string;
  styleProfile: string;
  accentFocus: string;
  textureDetail: number;
  contrast: number;
  rating: string;
}

const PortraitCustomizationDialog = ({
  open,
  onOpenChange,
  onGenerate,
  actorName,
}: PortraitCustomizationDialogProps) => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [age, setAge] = useState([50]);
  const [weathering, setWeathering] = useState([50]);
  const [detailLevel, setDetailLevel] = useState([50]);
  const [clothingStyle, setClothingStyle] = useState([50]);
  const [coverage, setCoverage] = useState([60]);
  const [fit, setFit] = useState("regular");
  const [styleProfile, setStyleProfile] = useState("casual");
  const [accentFocus, setAccentFocus] = useState("balanced");
  const [textureDetail, setTextureDetail] = useState([60]);
  const [contrast, setContrast] = useState([55]);
  const [rating, setRating] = useState("general");

  const presets = {
    youngWarrior: { age: 28, weathering: 20, detailLevel: 70, clothingStyle: 30, coverage: 65, fit: "athletic", styleProfile: "traditional", accentFocus: "balanced", textureDetail: 60, contrast: 55, rating: "teen_plus" },
    weatheredElder: { age: 70, weathering: 80, detailLevel: 90, clothingStyle: 50, coverage: 85, fit: "relaxed", styleProfile: "traditional", accentFocus: "balanced", textureDetail: 70, contrast: 50, rating: "general" },
    formalPortrait: { age: 45, weathering: 10, detailLevel: 95, clothingStyle: 90, coverage: 85, fit: "tailored", styleProfile: "professional", accentFocus: "upper", textureDetail: 80, contrast: 60, rating: "general" },
    nightlifeBold: { age: 27, weathering: 10, detailLevel: 80, clothingStyle: 25, coverage: 40, fit: "form_fitting", styleProfile: "nightlife", accentFocus: "balanced", textureDetail: 70, contrast: 60, rating: "adult_21_plus" }
  };

  const applyPreset = (preset: keyof typeof presets) => {
    const values = presets[preset];
    setAge([values.age]);
    setWeathering([values.weathering]);
    setDetailLevel([values.detailLevel]);
    setClothingStyle([values.clothingStyle]);
    setCoverage([values.coverage]);
    setFit(values.fit);
    setStyleProfile(values.styleProfile);
    setAccentFocus(values.accentFocus);
    setTextureDetail([values.textureDetail]);
    setContrast([values.contrast]);
    setRating(values.rating);
  };

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      await onGenerate({
        age: age[0],
        weathering: weathering[0],
        detailLevel: detailLevel[0],
        clothingStyle: clothingStyle[0],
        coverage: coverage[0],
        fit,
        styleProfile,
        accentFocus,
        textureDetail: textureDetail[0],
        contrast: contrast[0],
        rating,
      });
      onOpenChange(false);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh]">
        <DialogHeader>
          <DialogTitle className="font-western text-2xl">Customize Portrait</DialogTitle>
          <DialogDescription>
            Adjust the parameters to create a unique portrait for {actorName}. All portraits remain fully clothed.
          </DialogDescription>
        </DialogHeader>
        
        <ScrollArea className="max-h-[calc(90vh-180px)] pr-4">
        {/* Presets */}
        <div className="space-y-2 pt-4">
          <Label className="flex items-center gap-2">
            <Sparkles className="h-4 w-4" />
            Quick Presets
          </Label>
          <div className="flex gap-2 flex-wrap">
            <Button
              variant="outline"
              size="sm"
              onClick={() => applyPreset('youngWarrior')}
              className="flex-1"
            >
              <Badge variant="secondary" className="mr-2">28</Badge>
              Young Warrior
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => applyPreset('weatheredElder')}
              className="flex-1"
            >
              <Badge variant="secondary" className="mr-2">70</Badge>
              Weathered Elder
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => applyPreset('formalPortrait')}
              className="flex-1"
            >
              <Badge variant="secondary" className="mr-2">45</Badge>
              Formal Portrait
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => applyPreset('nightlifeBold')}
              className="flex-1"
            >
              <Badge variant="secondary" className="mr-2">27</Badge>
              Nightlife Bold
            </Button>
          </div>
        </div>

        <div className="space-y-6 py-4">
          {/* Age */}
          <div className="space-y-2">
            <div className="flex justify-between">
              <Label>Age</Label>
              <span className="text-sm text-muted-foreground">{age[0]} years</span>
            </div>
            <Slider
              value={age}
              onValueChange={setAge}
              min={21}
              max={80}
              step={1}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground">
              {age[0] < 35 ? "Young adult" : age[0] < 55 ? "Middle-aged" : "Elderly"}
            </p>
          </div>

          {/* Weathering */}
          <div className="space-y-2">
            <div className="flex justify-between">
              <Label>Photo Weathering</Label>
              <span className="text-sm text-muted-foreground">{weathering[0]}%</span>
            </div>
            <Slider
              value={weathering}
              onValueChange={setWeathering}
              min={0}
              max={100}
              step={10}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground">
              {weathering[0] < 30
                ? "Minimal wear, relatively clean"
                : weathering[0] < 70
                ? "Moderate aging and damage"
                : "Heavily weathered and faded"}
            </p>
          </div>

          {/* Detail Level */}
          <div className="space-y-2">
            <div className="flex justify-between">
              <Label>Detail Level</Label>
              <span className="text-sm text-muted-foreground">{detailLevel[0]}%</span>
            </div>
            <Slider
              value={detailLevel}
              onValueChange={setDetailLevel}
              min={0}
              max={100}
              step={10}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground">
              {detailLevel[0] < 30
                ? "Soft focus, minimal detail"
                : detailLevel[0] < 70
                ? "Moderate detail and clarity"
                : "Extremely detailed and sharp"}
            </p>
          </div>

          {/* Clothing Formality */}
          <div className="space-y-2">
            <div className="flex justify-between">
              <Label>Clothing Formality</Label>
              <span className="text-sm text-muted-foreground">{clothingStyle[0]}%</span>
            </div>
            <Slider
              value={clothingStyle}
              onValueChange={setClothingStyle}
              min={0}
              max={100}
              step={10}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground">
              {clothingStyle[0] < 30
                ? "Casual, relaxed attire"
                : clothingStyle[0] < 70
                ? "Smart casual styling"
                : "Formal or ceremonial dress"}
            </p>
          </div>

          {/* Coverage Level */}
          <div className="space-y-2">
            <div className="flex justify-between">
              <Label>Coverage Level</Label>
              <span className="text-sm text-muted-foreground">{coverage[0]}%</span>
            </div>
            <Slider
              value={coverage}
              onValueChange={setCoverage}
              min={0}
              max={100}
              step={5}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground">
              {coverage[0] >= 85
                ? "Conservative - Layered, high coverage"
                : coverage[0] >= 60
                ? "Moderate - Standard coverage"
                : coverage[0] >= 40
                ? "Bold - Reduced coverage, still fully clothed"
                : "Very Bold - Minimal coverage, fully clothed (no nudity)"}
            </p>
          </div>

          {/* Clothing Fit */}
          <div className="space-y-2">
            <Label>Clothing Fit</Label>
            <select
              value={fit}
              onChange={(e) => setFit(e.target.value)}
              className="w-full p-2 rounded-md border bg-background"
            >
              <option value="relaxed">Relaxed</option>
              <option value="regular">Regular</option>
              <option value="tailored">Tailored</option>
              <option value="form_fitting">Form-Fitting</option>
              <option value="compression">Compression / Performance</option>
            </select>
            <p className="text-xs text-muted-foreground">
              How closely the clothing follows the body's shape
            </p>
          </div>

          {/* Outfit Style */}
          <div className="space-y-2">
            <Label>Outfit Style</Label>
            <select
              value={styleProfile}
              onChange={(e) => setStyleProfile(e.target.value)}
              className="w-full p-2 rounded-md border bg-background"
            >
              <option value="professional">Professional / Business</option>
              <option value="casual">Casual / Everyday</option>
              <option value="athletic">Athletic / Performance</option>
              <option value="traditional">Traditional / Ceremonial</option>
              <option value="nightlife">Party / Nightlife</option>
              <option value="editorial">Bold Fashion Editorial</option>
            </select>
            <p className="text-xs text-muted-foreground">
              Overall style direction for the outfit
            </p>
          </div>

          {/* Accent Focus */}
          <div className="space-y-2">
            <Label>Outfit Accent Focus</Label>
            <select
              value={accentFocus}
              onChange={(e) => setAccentFocus(e.target.value)}
              className="w-full p-2 rounded-md border bg-background"
            >
              <option value="balanced">Balanced</option>
              <option value="upper">Upper Garments Emphasis</option>
              <option value="lower">Lower Garments Emphasis</option>
              <option value="accessories">Accessories & Details</option>
            </select>
            <p className="text-xs text-muted-foreground">
              Where the outfit places visual emphasis
            </p>
          </div>

          {/* Texture Detail */}
          <div className="space-y-2">
            <div className="flex justify-between">
              <Label>Fabric Texture Detail</Label>
              <span className="text-sm text-muted-foreground">{textureDetail[0]}%</span>
            </div>
            <Slider
              value={textureDetail}
              onValueChange={setTextureDetail}
              min={0}
              max={100}
              step={10}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground">
              Visible fabric weave, seams, and stitching detail
            </p>
          </div>

          {/* Contrast */}
          <div className="space-y-2">
            <div className="flex justify-between">
              <Label>Contrast & Lighting</Label>
              <span className="text-sm text-muted-foreground">{contrast[0]}%</span>
            </div>
            <Slider
              value={contrast}
              onValueChange={setContrast}
              min={0}
              max={100}
              step={5}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground">
              How dramatic the lighting and contrast are
            </p>
          </div>

          {/* Content Rating */}
          <div className="space-y-2">
            <Label>Content Rating</Label>
            <select
              value={rating}
              onChange={(e) => setRating(e.target.value)}
              className="w-full p-2 rounded-md border bg-background"
            >
              <option value="general">General Audience (modest fashion)</option>
              <option value="teen_plus">Teen+ (trendy, slightly revealing)</option>
              <option value="adult_21_plus">Adult 21+ (bold, form-fitting; no nudity)</option>
            </select>
            <p className="text-xs text-muted-foreground">
              All options remain fully clothed with no nudity
            </p>
          </div>
        </div>
        </ScrollArea>

        <Button
          onClick={handleGenerate}
          disabled={isGenerating}
          className="w-full bg-gradient-western"
        >
          {isGenerating ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Generating Portrait...
            </>
          ) : (
            <>
              <Wand2 className="mr-2 h-4 w-4" />
              Generate Custom Portrait
            </>
          )}
        </Button>
      </DialogContent>
    </Dialog>
  );
};

export default PortraitCustomizationDialog;
