import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Wand2, Loader2 } from "lucide-react";
import { generatePortrait } from "@/services/aiService";
import { useToast } from "@/hooks/use-toast";

interface GeneratePortraitButtonProps {
  actorId: string;
  fullName: string;
  role: string;
  era: string;
  onGenerated?: () => void;
  customization?: {
    age?: number;
    weathering?: number;
    detailLevel?: number;
    clothingStyle?: number;
  };
}

const GeneratePortraitButton = ({ 
  actorId, 
  fullName, 
  role, 
  era,
  onGenerated,
  customization
}: GeneratePortraitButtonProps) => {
  const { toast } = useToast();
  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerate = async () => {
    setIsGenerating(true);

    try {
      // Uses aiService which respects cloud/local provider setting
      const result = await generatePortrait({
        actorId,
        fullName,
        role,
        era,
        customization: customization || {},
      });

      if (!result.success) {
        throw new Error(result.error || 'Failed to generate portrait');
      }

      toast({
        title: "Portrait Generated",
        description: `Created authentic ${era} portrait for ${fullName} (${result.provider})`,
      });
      
      if (onGenerated) {
        onGenerated();
      }
    } catch (error: any) {
      console.error('Error generating portrait:', error);
      toast({
        title: "Generation Failed",
        description: error.message || "Failed to generate portrait",
        variant: "destructive",
      });
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <Button
      onClick={handleGenerate}
      disabled={isGenerating}
      size="sm"
      variant="outline"
      className="w-full"
    >
      {isGenerating ? (
        <>
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          Generating...
        </>
      ) : (
        <>
          <Wand2 className="mr-2 h-4 w-4" />
          Generate {era} Portrait
        </>
      )}
    </Button>
  );
};

export default GeneratePortraitButton;