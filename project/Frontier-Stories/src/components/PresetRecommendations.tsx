import { useState, useEffect } from "react";
import { supabase } from "@/integrations/supabase/client";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Sparkles, TrendingUp, Download, Star } from "lucide-react";
import { toast } from "sonner";

interface PresetRecommendationsProps {
  onApplyPreset: (preset: any) => void;
}

export const PresetRecommendations = ({ onApplyPreset }: PresetRecommendationsProps) => {
  const [userId, setUserId] = useState<string | null>(null);

  useEffect(() => {
    const getUser = async () => {
      const { data: { user } } = await supabase.auth.getUser();
      setUserId(user?.id || null);
    };
    getUser();
  }, []);

  const { data: recommendations, isLoading } = useQuery({
    queryKey: ["preset-recommendations", userId],
    queryFn: async () => {
      if (!userId) return { trending: [], personalized: [] };

      // Get user's review history
      const { data: userReviews } = await supabase
        .from("portrait_preset_reviews")
        .select("preset_id, rating, portrait_presets(tags, style_profile)")
        .eq("user_id", userId)
        .gte("rating", 4); // Only high-rated presets

      // Analyze user preferences from reviews
      const preferredTags = new Set<string>();
      const preferredStyles = new Set<string>();
      
      userReviews?.forEach((review: any) => {
        review.portrait_presets?.tags?.forEach((tag: string) => preferredTags.add(tag));
        if (review.portrait_presets?.style_profile) {
          preferredStyles.add(review.portrait_presets.style_profile);
        }
      });

      // Get trending presets (most downloaded recently)
      const { data: trending } = await supabase
        .from("portrait_presets")
        .select("*")
        .eq("is_public", true)
        .order("download_count", { ascending: false })
        .limit(6);

      // Get personalized recommendations based on user preferences
      let personalizedQuery = supabase
        .from("portrait_presets")
        .select("*")
        .eq("is_public", true);

      // Filter by preferred tags if available
      if (preferredTags.size > 0) {
        personalizedQuery = personalizedQuery.overlaps("tags", Array.from(preferredTags));
      }

      const { data: personalized } = await personalizedQuery
        .order("average_rating", { ascending: false })
        .limit(6);

      return {
        trending: trending || [],
        personalized: personalized || [],
      };
    },
    enabled: !!userId,
  });

  const handleApplyPreset = (preset: any) => {
    onApplyPreset(preset);
    toast.success(`Applied preset: ${preset.name}`);
  };

  if (!userId) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            Recommendations
          </CardTitle>
          <CardDescription>Sign in to get personalized preset recommendations</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            Loading Recommendations...
          </CardTitle>
        </CardHeader>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Personalized Recommendations */}
      {recommendations?.personalized && recommendations.personalized.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              Recommended For You
            </CardTitle>
            <CardDescription>Based on your review history and preferences</CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[300px]">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pr-4">
                {recommendations.personalized.map((preset: any) => (
                  <Card key={preset.id} className="hover:border-primary transition-colors">
                    <CardHeader>
                      <CardTitle className="text-base">{preset.name}</CardTitle>
                      {preset.creator_name && (
                        <CardDescription className="text-xs">by {preset.creator_name}</CardDescription>
                      )}
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {preset.description && (
                        <p className="text-xs text-muted-foreground line-clamp-2">{preset.description}</p>
                      )}
                      
                      <div className="flex flex-wrap gap-1">
                        {preset.tags?.slice(0, 3).map((tag: string) => (
                          <Badge key={tag} variant="secondary" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                      </div>

                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                          {preset.average_rating?.toFixed(1) || "0.0"}
                        </span>
                        <span className="flex items-center gap-1">
                          <Download className="h-3 w-3" />
                          {preset.download_count}
                        </span>
                      </div>

                      <Button
                        size="sm"
                        className="w-full"
                        onClick={() => handleApplyPreset(preset)}
                      >
                        Apply
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      )}

      {/* Trending Presets */}
      {recommendations?.trending && recommendations.trending.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-primary" />
              Trending Presets
            </CardTitle>
            <CardDescription>Most popular presets right now</CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[300px]">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pr-4">
                {recommendations.trending.map((preset: any) => (
                  <Card key={preset.id} className="hover:border-primary transition-colors">
                    <CardHeader>
                      <CardTitle className="text-base">{preset.name}</CardTitle>
                      {preset.creator_name && (
                        <CardDescription className="text-xs">by {preset.creator_name}</CardDescription>
                      )}
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {preset.description && (
                        <p className="text-xs text-muted-foreground line-clamp-2">{preset.description}</p>
                      )}
                      
                      <div className="flex flex-wrap gap-1">
                        {preset.tags?.slice(0, 3).map((tag: string) => (
                          <Badge key={tag} variant="secondary" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                      </div>

                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                          {preset.average_rating?.toFixed(1) || "0.0"}
                        </span>
                        <span className="flex items-center gap-1">
                          <Download className="h-3 w-3" />
                          {preset.download_count}
                        </span>
                      </div>

                      <Button
                        size="sm"
                        className="w-full"
                        onClick={() => handleApplyPreset(preset)}
                      >
                        Apply
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
