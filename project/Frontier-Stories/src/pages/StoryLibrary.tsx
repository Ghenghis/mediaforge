import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { 
  ArrowLeft, 
  Play, 
  Edit, 
  Trash2, 
  Search, 
  BookOpen, 
  Loader2,
  Clock,
  User,
  Copy,
  Film
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/hooks/use-toast";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import woodTexture from "@/assets/wood-texture.jpg";
import parchmentTexture from "@/assets/parchment-texture.jpg";

interface Story {
  id: string;
  title: string;
  description: string | null;
  era: string;
  status: string | null;
  created_at: string;
  updated_at: string;
  master_volume: number;
  pause_duration: number;
}

const StoryLibrary = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  
  const [stories, setStories] = useState<Story[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [storyToDelete, setStoryToDelete] = useState<Story | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isDuplicating, setIsDuplicating] = useState<string | null>(null);

  useEffect(() => {
    loadStories();

    // Set up real-time subscription
    const channel = supabase
      .channel('stories-changes')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'stories'
        },
        () => {
          loadStories();
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  const loadStories = async () => {
    setIsLoading(true);
    try {
      const { data, error } = await supabase
        .from('stories')
        .select('*')
        .order('updated_at', { ascending: false });

      if (error) throw error;

      setStories(data || []);
    } catch (error) {
      console.error('Error loading stories:', error);
      toast({
        title: "Error",
        description: "Failed to load stories",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleEditStory = (storyId: string) => {
    navigate(`/story-creation?id=${storyId}`);
  };

  const handleDeleteClick = (story: Story) => {
    setStoryToDelete(story);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!storyToDelete) return;

    setIsDeleting(true);

    try {
      const { error } = await supabase
        .from('stories')
        .delete()
        .eq('id', storyToDelete.id);

      if (error) throw error;

      toast({
        title: "Story Deleted",
        description: `"${storyToDelete.title}" has been removed`,
      });

      setDeleteDialogOpen(false);
      setStoryToDelete(null);
      loadStories();
    } catch (error) {
      console.error('Error deleting story:', error);
      toast({
        title: "Error",
        description: "Failed to delete story",
        variant: "destructive",
      });
    } finally {
      setIsDeleting(false);
    }
  };

  const handleDuplicateStory = async (story: Story) => {
    setIsDuplicating(story.id);

    try {
      // Create new story with duplicated data
      const { data: newStory, error: storyError } = await supabase
        .from('stories')
        .insert({
          title: `${story.title} (Copy)`,
          description: story.description,
          era: story.era,
          status: story.status,
          master_volume: story.master_volume,
          pause_duration: story.pause_duration,
        })
        .select()
        .single();

      if (storyError) throw storyError;

      // Get all story lines from original story
      const { data: lines, error: linesError } = await supabase
        .from('story_lines')
        .select('*')
        .eq('story_id', story.id)
        .order('line_number');

      if (linesError) throw linesError;

      // Duplicate story lines for new story
      if (lines && lines.length > 0) {
        const newLines = lines.map(line => ({
          story_id: newStory.id,
          actor_id: line.actor_id,
          line_number: line.line_number,
          text: line.text,
          volume: line.volume,
          fade_in: line.fade_in,
          fade_out: line.fade_out,
          // Don't copy audio_url as it's specific to the original
        }));

        const { error: insertError } = await supabase
          .from('story_lines')
          .insert(newLines);

        if (insertError) throw insertError;
      }

      toast({
        title: "Story Duplicated",
        description: `Created "${newStory.title}"`,
      });

      loadStories();
    } catch (error) {
      console.error('Error duplicating story:', error);
      toast({
        title: "Error",
        description: "Failed to duplicate story",
        variant: "destructive",
      });
    } finally {
      setIsDuplicating(null);
    }
  };

  const filteredStories = stories.filter((story) =>
    story.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    story.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    story.era.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  return (
    <div className="min-h-screen relative">
      {/* Background */}
      <div 
        className="fixed inset-0 pointer-events-none opacity-40" 
        style={{ 
          backgroundImage: `url(${woodTexture})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundAttachment: 'fixed'
        }} 
      />
      <div 
        className="fixed inset-0 pointer-events-none opacity-30" 
        style={{ 
          backgroundImage: `url(${parchmentTexture})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundAttachment: 'fixed',
          mixBlendMode: 'multiply'
        }} 
      />

      {/* Content */}
      <div className="relative z-10 container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <Button
            variant="ghost"
            onClick={() => navigate('/')}
            className="mb-4 text-foreground hover:text-primary"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Library
          </Button>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="font-western text-5xl text-foreground mb-2 [text-shadow:_2px_2px_4px_rgb(0_0_0_/_40%)]">
                Story Library
              </h1>
              <p className="font-body text-muted-foreground">
                Manage your saved story projects
              </p>
            </div>
            <Button
              onClick={() => navigate('/story-creation')}
              size="lg"
              className="bg-gradient-western"
            >
              <BookOpen className="mr-2 h-5 w-5" />
              Create New Story
            </Button>
          </div>
        </div>

        {/* Search */}
        <div className="mb-6">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-5 w-5" />
            <Input
              type="text"
              placeholder="Search stories..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 bg-background/95 backdrop-blur"
            />
          </div>
        </div>

        {/* Stories Grid */}
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="h-12 w-12 animate-spin text-primary" />
            <p className="ml-4 text-xl font-body text-foreground">Loading stories...</p>
          </div>
        ) : filteredStories.length === 0 ? (
          <Card className="bg-card/95 backdrop-blur border-border">
            <CardContent className="py-20 text-center">
              <BookOpen className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-2xl font-western font-bold text-foreground mb-2">
                {searchQuery ? "No Stories Found" : "No Stories Yet"}
              </h3>
              <p className="text-muted-foreground mb-6">
                {searchQuery 
                  ? "Try adjusting your search criteria"
                  : "Create your first story to get started"}
              </p>
              {!searchQuery && (
                <Button
                  onClick={() => navigate('/story-creation')}
                  className="bg-gradient-western"
                >
                  <BookOpen className="mr-2 h-5 w-5" />
                  Create Story
                </Button>
              )}
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredStories.map((story) => (
              <Card
                key={story.id}
                className="bg-card/95 backdrop-blur border-border hover:shadow-lifted transition-all duration-300 hover:scale-105"
              >
                <CardHeader>
                  <CardTitle className="font-western text-xl line-clamp-2">
                    {story.title}
                  </CardTitle>
                  <div className="flex gap-2 mt-2">
                    <Badge variant="secondary">{story.era}</Badge>
                    {story.status && (
                      <Badge variant="outline">{story.status}</Badge>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {story.description && (
                    <p className="text-sm text-muted-foreground line-clamp-3">
                      {story.description}
                    </p>
                  )}
                  
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {formatDate(story.updated_at)}
                    </div>
                  </div>

                  <div className="flex flex-col gap-2 pt-2">
                    <div className="flex gap-2">
                      <Button
                        onClick={() => handleEditStory(story.id)}
                        size="sm"
                        className="flex-1"
                        variant="outline"
                      >
                        <Edit className="mr-1 h-4 w-4" />
                        Edit
                      </Button>
                      <Button
                        onClick={() => handleDuplicateStory(story)}
                        size="sm"
                        variant="outline"
                        disabled={isDuplicating === story.id}
                      >
                        {isDuplicating === story.id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Copy className="h-4 w-4" />
                        )}
                      </Button>
                      <Button
                        onClick={() => handleDeleteClick(story)}
                        size="sm"
                        variant="outline"
                        className="text-destructive hover:text-destructive"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                    <Button
                      onClick={() => navigate(`/storyboard?storyId=${story.id}`)}
                      size="sm"
                      className="w-full bg-gradient-western"
                    >
                      <Film className="mr-2 h-4 w-4" />
                      View Storyboard
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Story</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{storyToDelete?.title}"? This action cannot be undone.
              All dialogue lines and settings will be permanently removed.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              disabled={isDeleting}
              className="bg-destructive hover:bg-destructive/90"
            >
              {isDeleting ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Deleting...</>
              ) : (
                <>Delete</>
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default StoryLibrary;
