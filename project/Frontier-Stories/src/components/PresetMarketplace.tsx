import { useState } from "react";
import { supabase } from "@/integrations/supabase/client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Download, Search, Share2, Sparkles, Star, MessageSquare, TrendingUp, Clock, ChevronLeft, ChevronRight, Heart } from "lucide-react";
import { toast } from "sonner";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";

interface PresetMarketplaceProps {
  onApplyPreset: (preset: any) => void;
}

export const PresetMarketplace = ({ onApplyPreset }: PresetMarketplaceProps) => {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<"downloads" | "rating" | "newest">("downloads");
  const [page, setPage] = useState(1);
  const [reviewDialogOpen, setReviewDialogOpen] = useState(false);
  const [selectedPresetForReview, setSelectedPresetForReview] = useState<any>(null);
  const [reviewRating, setReviewRating] = useState(5);
  const [reviewText, setReviewText] = useState("");
  const [reviewerName, setReviewerName] = useState("");
  const pageSize = 9;

  const { data: presetsData, isLoading, refetch } = useQuery({
    queryKey: ["portrait-presets", searchTerm, selectedTag, sortBy, page],
    queryFn: async () => {
      let query = supabase
        .from("portrait_presets")
        .select("*", { count: "exact" })
        .eq("is_public", true);

      if (searchTerm) {
        query = query.or(`name.ilike.%${searchTerm}%,description.ilike.%${searchTerm}%`);
      }

      if (selectedTag) {
        query = query.contains("tags", [selectedTag]);
      }

      // Apply sorting
      if (sortBy === "downloads") {
        query = query.order("download_count", { ascending: false });
      } else if (sortBy === "rating") {
        query = query.order("average_rating", { ascending: false });
      } else if (sortBy === "newest") {
        query = query.order("created_at", { ascending: false });
      }

      // Apply pagination
      const from = (page - 1) * pageSize;
      const to = from + pageSize - 1;
      query = query.range(from, to);

      const { data, error, count } = await query;
      if (error) throw error;
      return { presets: data, total: count || 0 };
    },
  });

  const presets = presetsData?.presets || [];
  const totalPages = Math.ceil((presetsData?.total || 0) / pageSize);

  const { data: userFavorites } = useQuery({
    queryKey: ["user-favorites"],
    queryFn: async () => {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return [];

      const { data, error } = await supabase
        .from("user_favorite_presets")
        .select("preset_id")
        .eq("user_id", user.id);

      if (error) throw error;
      return data.map(f => f.preset_id);
    },
  });

  const toggleFavoriteMutation = useMutation({
    mutationFn: async ({ presetId, isFavorited }: { presetId: string; isFavorited: boolean }) => {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error("Must be logged in");

      if (isFavorited) {
        const { error } = await supabase
          .from("user_favorite_presets")
          .delete()
          .eq("user_id", user.id)
          .eq("preset_id", presetId);
        if (error) throw error;
      } else {
        const { error } = await supabase
          .from("user_favorite_presets")
          .insert({ user_id: user.id, preset_id: presetId });
        if (error) throw error;
      }
    },
    onSuccess: (_, { isFavorited }) => {
      toast.success(isFavorited ? "Removed from favorites" : "Added to favorites");
      queryClient.invalidateQueries({ queryKey: ["user-favorites"] });
    },
    onError: () => {
      toast.error("Failed to update favorite");
    },
  });

  const submitReviewMutation = useMutation({
    mutationFn: async ({ presetId, rating, text, name }: any) => {
      const { data: { user } } = await supabase.auth.getUser();
      
      const { error } = await supabase.from("portrait_preset_reviews").insert({
        preset_id: presetId,
        rating,
        review_text: text,
        reviewer_name: name,
        user_id: user?.id || null,
      });
      if (error) throw error;

      // Update preset average rating
      const { data: reviews } = await supabase
        .from("portrait_preset_reviews")
        .select("rating")
        .eq("preset_id", presetId);

      if (reviews) {
        const avgRating = reviews.reduce((sum, r) => sum + r.rating, 0) / reviews.length;
        await supabase
          .from("portrait_presets")
          .update({ 
            average_rating: avgRating,
            review_count: reviews.length 
          })
          .eq("id", presetId);
      }
    },
    onSuccess: () => {
      toast.success("Review submitted!");
      setReviewDialogOpen(false);
      setReviewText("");
      setReviewerName("");
      setReviewRating(5);
      queryClient.invalidateQueries({ queryKey: ["portrait-presets"] });
    },
    onError: () => {
      toast.error("Failed to submit review");
    },
  });

  const allTags = Array.from(
    new Set(presets?.flatMap((p) => p.tags || []) || [])
  );

  const handleDownloadPreset = async (preset: any) => {
    await supabase
      .from("portrait_presets")
      .update({ download_count: preset.download_count + 1 })
      .eq("id", preset.id);

    onApplyPreset(preset);
    toast.success(`Applied preset: ${preset.name}`);
    refetch();
  };

  const handleSharePreset = (preset: any) => {
    const url = `${window.location.origin}/portrait-gallery?preset=${preset.id}`;
    navigator.clipboard.writeText(url);
    toast.success("Preset link copied to clipboard!");
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-4">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search presets..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setPage(1);
            }}
            className="pl-9"
          />
        </div>
        <Select value={sortBy} onValueChange={(v: any) => { setSortBy(v); setPage(1); }}>
          <SelectTrigger className="w-[180px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="downloads">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Most Downloaded
              </div>
            </SelectItem>
            <SelectItem value="rating">
              <div className="flex items-center gap-2">
                <Star className="h-4 w-4" />
                Highest Rated
              </div>
            </SelectItem>
            <SelectItem value="newest">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4" />
                Newest First
              </div>
            </SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="flex flex-wrap gap-2">
        <Button
          size="sm"
          variant={selectedTag === null ? "default" : "outline"}
          onClick={() => { setSelectedTag(null); setPage(1); }}
        >
          All
        </Button>
        {allTags.map((tag) => (
          <Button
            key={tag}
            size="sm"
            variant={selectedTag === tag ? "default" : "outline"}
            onClick={() => { setSelectedTag(tag); setPage(1); }}
          >
            {tag}
          </Button>
        ))}
      </div>

      <ScrollArea className="h-[600px]">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pr-4">
          {isLoading ? (
            <div className="col-span-full text-center py-12 text-muted-foreground">
              Loading presets...
            </div>
          ) : presets?.length === 0 ? (
            <div className="col-span-full text-center py-12 text-muted-foreground">
              No presets found
            </div>
          ) : (
            presets?.map((preset) => (
              <Card key={preset.id} className="hover:border-primary transition-colors">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <CardTitle className="text-lg">{preset.name}</CardTitle>
                      {preset.creator_name && (
                        <CardDescription>by {preset.creator_name}</CardDescription>
                      )}
                    </div>
                    <Sparkles className="h-5 w-5 text-primary" />
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {preset.description && (
                    <p className="text-sm text-muted-foreground">{preset.description}</p>
                  )}

                  <div className="flex flex-wrap gap-1">
                    {preset.tags?.map((tag: string) => (
                      <Badge key={tag} variant="secondary" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                    <div>Coverage: {preset.coverage}%</div>
                    <div>Style: {preset.style_profile}</div>
                    <div>Fit: {preset.fit}</div>
                    <div>Rating: {preset.rating}</div>
                  </div>

                  <div className="flex items-center justify-between pt-2">
                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Download className="h-3 w-3" />
                        {preset.download_count}
                      </span>
                      <span className="flex items-center gap-1">
                        <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                        {preset.average_rating?.toFixed(1) || "0.0"} ({preset.review_count || 0})
                      </span>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <Button
                      className="flex-1"
                      onClick={() => handleDownloadPreset(preset)}
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Apply
                    </Button>
                    <Button
                      variant={userFavorites?.includes(preset.id) ? "default" : "outline"}
                      size="icon"
                      onClick={() => toggleFavoriteMutation.mutate({ 
                        presetId: preset.id, 
                        isFavorited: userFavorites?.includes(preset.id) || false 
                      })}
                    >
                      <Heart className={`h-4 w-4 ${userFavorites?.includes(preset.id) ? 'fill-current' : ''}`} />
                    </Button>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => handleSharePreset(preset)}
                    >
                      <Share2 className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => {
                        setSelectedPresetForReview(preset);
                        setReviewDialogOpen(true);
                      }}
                    >
                      <MessageSquare className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
          ))
        )}
      </div>
      </ScrollArea>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 pt-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            <ChevronLeft className="h-4 w-4" />
            Previous
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {page} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
          >
            Next
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}

      {/* Review Dialog */}
      <Dialog open={reviewDialogOpen} onOpenChange={setReviewDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Review Preset</DialogTitle>
            <DialogDescription>
              Share your experience with {selectedPresetForReview?.name}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Your Name (optional)</Label>
              <Input
                placeholder="Anonymous"
                value={reviewerName}
                onChange={(e) => setReviewerName(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label>Rating</Label>
              <div className="flex gap-1">
                {[1, 2, 3, 4, 5].map((star) => (
                  <Button
                    key={star}
                    variant="ghost"
                    size="sm"
                    onClick={() => setReviewRating(star)}
                  >
                    <Star
                      className={`h-6 w-6 ${
                        star <= reviewRating
                          ? "fill-yellow-400 text-yellow-400"
                          : "text-muted-foreground"
                      }`}
                    />
                  </Button>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <Label>Review (optional)</Label>
              <Textarea
                placeholder="Share your thoughts about this preset..."
                value={reviewText}
                onChange={(e) => setReviewText(e.target.value)}
                rows={4}
              />
            </div>

            <div className="flex gap-2">
              <Button
                variant="outline"
                className="flex-1"
                onClick={() => setReviewDialogOpen(false)}
              >
                Cancel
              </Button>
              <Button
                className="flex-1"
                onClick={() =>
                  submitReviewMutation.mutate({
                    presetId: selectedPresetForReview?.id,
                    rating: reviewRating,
                    text: reviewText,
                    name: reviewerName || "Anonymous",
                  })
                }
                disabled={submitReviewMutation.isPending}
              >
                Submit Review
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};