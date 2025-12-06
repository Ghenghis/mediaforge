import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Save, Sparkles } from "lucide-react";
import { toast } from "sonner";

interface ABTestingComparisonProps {
  onGenerateA: (settings: any) => void;
  onGenerateB: (settings: any) => void;
  onSavePreferred: (settings: any) => void;
  imageA?: string;
  imageB?: string;
}

export const ABTestingComparison = ({
  onGenerateA,
  onGenerateB,
  onSavePreferred,
  imageA,
  imageB,
}: ABTestingComparisonProps) => {
  const [settingsA, setSettingsA] = useState({
    age: 35,
    coverage: 60,
    fit: "regular",
    styleProfile: "casual",
    rating: "general",
  });

  const [settingsB, setSettingsB] = useState({
    age: 35,
    coverage: 40,
    fit: "form_fitting",
    styleProfile: "nightlife",
    rating: "adult_21_plus",
  });

  const SettingsPanel = ({ 
    settings, 
    onChange, 
    label 
  }: { 
    settings: any; 
    onChange: (settings: any) => void; 
    label: string;
  }) => (
    <div className="space-y-4">
      <h3 className="font-semibold text-lg">{label}</h3>
      
      <div className="space-y-2">
        <Label>Age: {settings.age}</Label>
        <Slider
          value={[settings.age]}
          onValueChange={([age]) => onChange({ ...settings, age })}
          min={21}
          max={80}
          step={1}
        />
      </div>

      <div className="space-y-2">
        <Label>Coverage: {settings.coverage}%</Label>
        <Slider
          value={[settings.coverage]}
          onValueChange={([coverage]) => onChange({ ...settings, coverage })}
          min={0}
          max={100}
          step={1}
        />
      </div>

      <div className="space-y-2">
        <Label>Fit</Label>
        <Select value={settings.fit} onValueChange={(fit) => onChange({ ...settings, fit })}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="relaxed">Relaxed</SelectItem>
            <SelectItem value="regular">Regular</SelectItem>
            <SelectItem value="tailored">Tailored</SelectItem>
            <SelectItem value="form_fitting">Form-Fitting</SelectItem>
            <SelectItem value="compression">Compression</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label>Style Profile</Label>
        <Select 
          value={settings.styleProfile} 
          onValueChange={(styleProfile) => onChange({ ...settings, styleProfile })}
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="professional">Professional</SelectItem>
            <SelectItem value="casual">Casual</SelectItem>
            <SelectItem value="athletic">Athletic</SelectItem>
            <SelectItem value="traditional">Traditional</SelectItem>
            <SelectItem value="nightlife">Nightlife</SelectItem>
            <SelectItem value="editorial">Fashion Editorial</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label>Rating</Label>
        <Select 
          value={settings.rating} 
          onValueChange={(rating) => onChange({ ...settings, rating })}
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="general">General</SelectItem>
            <SelectItem value="teen_plus">Teen+</SelectItem>
            <SelectItem value="adult_21_plus">Adult 21+</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Settings A */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              Version A
              <Button onClick={() => onGenerateA(settingsA)} size="sm">
                <Sparkles className="h-4 w-4 mr-2" />
                Generate
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <SettingsPanel 
              settings={settingsA} 
              onChange={setSettingsA} 
              label="Configure A"
            />
          </CardContent>
        </Card>

        {/* Settings B */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              Version B
              <Button onClick={() => onGenerateB(settingsB)} size="sm">
                <Sparkles className="h-4 w-4 mr-2" />
                Generate
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <SettingsPanel 
              settings={settingsB} 
              onChange={setSettingsB} 
              label="Configure B"
            />
          </CardContent>
        </Card>
      </div>

      <Separator />

      {/* Comparison View */}
      <div>
        <h3 className="font-semibold text-lg mb-4">Side-by-Side Comparison</h3>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-center">Version A Result</CardTitle>
            </CardHeader>
            <CardContent>
              {imageA ? (
                <div className="space-y-4">
                  <img 
                    src={imageA} 
                    alt="Version A" 
                    className="w-full aspect-square object-cover rounded-lg"
                  />
                  <Button 
                    className="w-full" 
                    onClick={() => {
                      onSavePreferred(settingsA);
                      toast.success("Settings A saved as preferred!");
                    }}
                  >
                    <Save className="h-4 w-4 mr-2" />
                    Save A as Preferred
                  </Button>
                </div>
              ) : (
                <div className="w-full aspect-square bg-muted rounded-lg flex items-center justify-center text-muted-foreground">
                  Generate Version A
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-center">Version B Result</CardTitle>
            </CardHeader>
            <CardContent>
              {imageB ? (
                <div className="space-y-4">
                  <img 
                    src={imageB} 
                    alt="Version B" 
                    className="w-full aspect-square object-cover rounded-lg"
                  />
                  <Button 
                    className="w-full" 
                    onClick={() => {
                      onSavePreferred(settingsB);
                      toast.success("Settings B saved as preferred!");
                    }}
                  >
                    <Save className="h-4 w-4 mr-2" />
                    Save B as Preferred
                  </Button>
                </div>
              ) : (
                <div className="w-full aspect-square bg-muted rounded-lg flex items-center justify-center text-muted-foreground">
                  Generate Version B
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};