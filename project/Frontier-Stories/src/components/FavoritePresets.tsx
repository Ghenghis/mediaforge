import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { supabase } from "@/integrations/supabase/client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Heart, Trash2, Download, Star } from "lucide-react";
import { toast } from "sonner";
import { ScrollArea } from "@/components/ui/scroll-area";

interface FavoritePresetsProps {
  onApplyPreset: (preset: any) => void;
}

export const FavoritePresets = ({ onApplyPreset }: FavoritePresetsProps) => {
  const queryClient = useQueryClient();

  const { data: favorites, isLoading } = useQuery({
    queryKey: ["favorite-presets"],
    queryFn: async () => {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return [];

      const { data, error } = await supabase
        .from("user_favorite_presets")
        .select(`
          *,
          preset:portrait_presets(*)
        `)
        .eq("user_id", user.id)
        .order("created_at", { ascending: false });

      if (error) throw error;
      return data;
    },
  });

  const removeFavoriteMutation = useMutation({
    mutationFn: async (favoriteId: string) => {
      const { error } = await supabase
        .from("user_favorite_presets")
        .delete()
        .eq("id", favoriteId);
      if (error) throw error;
    },
    onSuccess: () => {
      toast.success("Removed from favorites");
      queryClient.invalidateQueries({ queryKey: ["favorite-presets"] });
    },
    onError: () => {
      toast.error("Failed to remove favorite");
    },
  });

  const handleApply = (preset: any) => {
    onApplyPreset(preset);
    toast.success(`Applied preset: ${preset.name}`);
  };

  if (isLoading) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        Loading favorites...
      </div>
    );
  }

  if (!favorites || favorites.length === 0) {
    return (
      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center justify-center py-12">
          <Heart className="h-12 w-12 text-muted-foreground mb-4" />
          <p className="text-muted-foreground text-center">
            No favorite presets yet.<br />
            Bookmark your most-used presets for quick access.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Heart className="h-5 w-5 text-primary" />
          My Favorite Presets
        </h3>
        <p className="text-sm text-muted-foreground">Quick access to your bookmarked presets</p>
      </div>

      <ScrollArea className="h-[500px]">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pr-4">
          {favorites.map((favorite) => {
            const preset = favorite.preset;
            if (!preset) return null;

            return (
              <Card key={favorite.id} className="hover:border-primary transition-colors">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="space-y-1 flex-1">
                      <CardTitle className="text-lg">{preset.name}</CardTitle>
                      {preset.creator_name && (
                        <CardDescription>by {preset.creator_name}</CardDescription>
                      )}
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-destructive hover:text-destructive"
                      onClick={() => removeFavoriteMutation.mutate(favorite.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {preset.description && (
                    <p className="text-sm text-muted-foreground line-clamp-2">
                      {preset.description}
                    </p>
                  )}

                  <div className="flex flex-wrap gap-2">
                    {preset.character_style && (
                      <Badge variant="secondary">{preset.character_style}</Badge>
                    )}
                    {preset.min_age && preset.max_age && (
                      <Badge variant="outline">
                        Age {preset.min_age}-{preset.max_age}
                      </Badge>
                    )}
                    {preset.clothing_type && (
                      <Badge variant="outline">{preset.clothing_type}</Badge>
                    )}
                  </div>

                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    {preset.average_rating > 0 && (
                      <div className="flex items-center gap-1">
                        <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                        <span>{preset.average_rating.toFixed(1)}</span>
                      </div>
                    )}
                    <div className="flex items-center gap-1">
                      <Download className="h-3 w-3" />
                      <span>{preset.download_count}</span>
                    </div>
                  </div>

                  <Button
                    className="w-full"
                    onClick={() => handleApply(preset)}
                  >
                    Apply Preset
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </ScrollArea>
    </div>
  );
};
