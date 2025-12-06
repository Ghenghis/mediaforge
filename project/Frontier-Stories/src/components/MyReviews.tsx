import { useState } from "react";
import { supabase } from "@/integrations/supabase/client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Star, Edit2, Trash2, Save, X } from "lucide-react";
import { toast } from "sonner";
import { ScrollArea } from "@/components/ui/scroll-area";

export const MyReviews = () => {
  const queryClient = useQueryClient();
  const [editingReviewId, setEditingReviewId] = useState<string | null>(null);
  const [editRating, setEditRating] = useState(5);
  const [editText, setEditText] = useState("");

  const { data: reviews, isLoading } = useQuery({
    queryKey: ["my-reviews"],
    queryFn: async () => {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return [];

      const { data, error } = await supabase
        .from("portrait_preset_reviews")
        .select(`
          *,
          preset:portrait_presets(name, id)
        `)
        .eq("user_id", user.id)
        .order("created_at", { ascending: false });

      if (error) throw error;
      return data;
    },
  });

  const updateMutation = useMutation({
    mutationFn: async ({ id, rating, text }: any) => {
      const { error } = await supabase
        .from("portrait_preset_reviews")
        .update({ rating, review_text: text })
        .eq("id", id);

      if (error) throw error;

      // Recalculate average rating for the preset
      const review = reviews?.find(r => r.id === id);
      if (review) {
        const { data: allReviews } = await supabase
          .from("portrait_preset_reviews")
          .select("rating")
          .eq("preset_id", review.preset_id);

        if (allReviews) {
          const avgRating = allReviews.reduce((sum, r) => sum + r.rating, 0) / allReviews.length;
          await supabase
            .from("portrait_presets")
            .update({ average_rating: avgRating })
            .eq("id", review.preset_id);
        }
      }
    },
    onSuccess: () => {
      toast.success("Review updated!");
      setEditingReviewId(null);
      queryClient.invalidateQueries({ queryKey: ["my-reviews"] });
      queryClient.invalidateQueries({ queryKey: ["portrait-presets"] });
    },
    onError: () => {
      toast.error("Failed to update review");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      const review = reviews?.find(r => r.id === id);
      
      const { error } = await supabase
        .from("portrait_preset_reviews")
        .delete()
        .eq("id", id);

      if (error) throw error;

      // Recalculate average rating for the preset
      if (review) {
        const { data: remainingReviews } = await supabase
          .from("portrait_preset_reviews")
          .select("rating")
          .eq("preset_id", review.preset_id);

        if (remainingReviews && remainingReviews.length > 0) {
          const avgRating = remainingReviews.reduce((sum, r) => sum + r.rating, 0) / remainingReviews.length;
          await supabase
            .from("portrait_presets")
            .update({ 
              average_rating: avgRating,
              review_count: remainingReviews.length 
            })
            .eq("id", review.preset_id);
        } else {
          await supabase
            .from("portrait_presets")
            .update({ 
              average_rating: 0,
              review_count: 0 
            })
            .eq("id", review.preset_id);
        }
      }
    },
    onSuccess: () => {
      toast.success("Review deleted!");
      queryClient.invalidateQueries({ queryKey: ["my-reviews"] });
      queryClient.invalidateQueries({ queryKey: ["portrait-presets"] });
    },
    onError: () => {
      toast.error("Failed to delete review");
    },
  });

  const handleEdit = (review: any) => {
    setEditingReviewId(review.id);
    setEditRating(review.rating);
    setEditText(review.review_text || "");
  };

  const handleSave = (id: string) => {
    updateMutation.mutate({ id, rating: editRating, text: editText });
  };

  const handleCancel = () => {
    setEditingReviewId(null);
    setEditRating(5);
    setEditText("");
  };

  if (isLoading) {
    return <div className="text-center py-8 text-muted-foreground">Loading your reviews...</div>;
  }

  if (!reviews || reviews.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>My Reviews</CardTitle>
          <CardDescription>You haven't submitted any reviews yet</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>My Reviews</CardTitle>
        <CardDescription>Manage your preset reviews</CardDescription>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[400px] pr-4">
          <div className="space-y-4">
            {reviews.map((review: any) => (
              <Card key={review.id}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-base">{review.preset?.name}</CardTitle>
                      <CardDescription>
                        {new Date(review.created_at).toLocaleDateString()}
                      </CardDescription>
                    </div>
                    {editingReviewId !== review.id && (
                      <div className="flex gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleEdit(review)}
                        >
                          <Edit2 className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => deleteMutation.mutate(review.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {editingReviewId === review.id ? (
                    <>
                      <div className="space-y-2">
                        <Label>Rating</Label>
                        <div className="flex gap-1">
                          {[1, 2, 3, 4, 5].map((star) => (
                            <Button
                              key={star}
                              variant="ghost"
                              size="sm"
                              onClick={() => setEditRating(star)}
                            >
                              <Star
                                className={`h-6 w-6 ${
                                  star <= editRating
                                    ? "fill-yellow-400 text-yellow-400"
                                    : "text-muted-foreground"
                                }`}
                              />
                            </Button>
                          ))}
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label>Review</Label>
                        <Textarea
                          value={editText}
                          onChange={(e) => setEditText(e.target.value)}
                          rows={4}
                        />
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          onClick={handleCancel}
                          disabled={updateMutation.isPending}
                        >
                          <X className="h-4 w-4 mr-2" />
                          Cancel
                        </Button>
                        <Button
                          onClick={() => handleSave(review.id)}
                          disabled={updateMutation.isPending}
                        >
                          <Save className="h-4 w-4 mr-2" />
                          Save
                        </Button>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="flex gap-1">
                        {[1, 2, 3, 4, 5].map((star) => (
                          <Star
                            key={star}
                            className={`h-4 w-4 ${
                              star <= review.rating
                                ? "fill-yellow-400 text-yellow-400"
                                : "text-muted-foreground"
                            }`}
                          />
                        ))}
                      </div>
                      {review.review_text && (
                        <p className="text-sm text-muted-foreground">{review.review_text}</p>
                      )}
                    </>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
};
