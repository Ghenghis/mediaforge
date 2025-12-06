import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2, Mountain } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/hooks/use-toast";

interface SceneryGeneratorProps {
  storyId?: string;
  era: string;
  onGenerated?: (imageUrl: string) => void;
}

const SceneryGenerator = ({ storyId, era, onGenerated }: SceneryGeneratorProps) => {
  const { toast } = useToast();
  const [isGenerating, setIsGenerating] = useState(false);
  const [sceneryType, setSceneryType] = useState<string>('town');
  const [description, setDescription] = useState('');
  const [generatedImage, setGeneratedImage] = useState<string | null>(null);

  const sceneryTypes = [
    { value: 'town', label: 'Frontier Town' },
    { value: 'landscape', label: 'Western Landscape' },
    { value: 'interior', label: 'Building Interior' },
    { value: 'ranch', label: 'Ranch/Homestead' },
    { value: 'canyon', label: 'Canyon/Desert' },
  ];

  const handleGenerate = async () => {
    setIsGenerating(true);

    try {
      const { data, error } = await supabase.functions.invoke('generate-scenery', {
        body: {
          storyId: storyId || 'preview',
          era,
          sceneryType,
          description,
        },
      });

      if (error) throw error;

      if (data.success) {
        setGeneratedImage(data.imageUrl);
        toast({
          title: "Scenery Generated",
          description: `Created authentic ${era} ${sceneryType} scenery`,
        });
        
        if (onGenerated) {
          onGenerated(data.imageUrl);
        }
      }
    } catch (error: any) {
      console.error('Error generating scenery:', error);
      toast({
        title: "Generation Failed",
        description: error.message || "Failed to generate scenery",
        variant: "destructive",
      });
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 font-western">
          <Mountain className="h-5 w-5" />
          Generate Period Scenery
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label>Scenery Type</Label>
          <Select value={sceneryType} onValueChange={setSceneryType}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {sceneryTypes.map((type) => (
                <SelectItem key={type.value} value={type.value}>
                  {type.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Additional Details (Optional)</Label>
          <Textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe specific details you want in the scene..."
            rows={3}
          />
        </div>

        <Button
          onClick={handleGenerate}
          disabled={isGenerating}
          className="w-full bg-gradient-western"
        >
          {isGenerating ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Generating {era} Scenery...
            </>
          ) : (
            <>
              <Mountain className="mr-2 h-4 w-4" />
              Generate Scenery
            </>
          )}
        </Button>

        {generatedImage && (
          <div className="space-y-2">
            <Label>Generated Scenery</Label>
            <div className="aspect-video bg-muted rounded-lg overflow-hidden border-2 border-border">
              <img
                src={generatedImage}
                alt="Generated scenery"
                className="w-full h-full object-cover"
              />
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default SceneryGenerator;
