import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";

interface ImageComparisonDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  bwImageUrl: string;
  colorImageUrl: string;
  actorName: string;
}

const ImageComparisonDialog = ({
  open,
  onOpenChange,
  bwImageUrl,
  colorImageUrl,
  actorName,
}: ImageComparisonDialogProps) => {
  const [sliderValue, setSliderValue] = useState([50]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle className="font-western text-2xl">
            Compare B&W vs Color - {actorName}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Comparison Container */}
          <div className="relative aspect-square bg-muted rounded-lg overflow-hidden">
            {/* Color Image (background) */}
            <img
              src={colorImageUrl}
              alt="Color version"
              className="absolute inset-0 w-full h-full object-cover"
            />
            
            {/* B&W Image (foreground with clip) */}
            <div
              className="absolute inset-0"
              style={{
                clipPath: `inset(0 ${100 - sliderValue[0]}% 0 0)`,
              }}
            >
              <img
                src={bwImageUrl}
                alt="Black and white version"
                className="w-full h-full object-cover"
              />
            </div>

            {/* Divider Line */}
            <div
              className="absolute top-0 bottom-0 w-1 bg-white shadow-lg"
              style={{
                left: `${sliderValue[0]}%`,
                transform: 'translateX(-50%)',
              }}
            >
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 bg-white rounded-full shadow-lg flex items-center justify-center">
                <div className="w-0 h-0 border-t-4 border-b-4 border-l-4 border-transparent border-l-foreground -ml-1" />
                <div className="w-0 h-0 border-t-4 border-b-4 border-r-4 border-transparent border-r-foreground -mr-1" />
              </div>
            </div>

            {/* Labels */}
            <div className="absolute top-4 left-4 bg-background/90 px-3 py-1 rounded-full">
              <span className="text-sm font-medium">B&W</span>
            </div>
            <div className="absolute top-4 right-4 bg-background/90 px-3 py-1 rounded-full">
              <span className="text-sm font-medium">Color</span>
            </div>
          </div>

          {/* Slider Control */}
          <div className="space-y-2">
            <Label>Comparison Slider</Label>
            <Slider
              value={sliderValue}
              onValueChange={setSliderValue}
              min={0}
              max={100}
              step={1}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground text-center">
              Drag to compare B&W ({sliderValue[0]}%) vs Color ({100 - sliderValue[0]}%)
            </p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ImageComparisonDialog;
