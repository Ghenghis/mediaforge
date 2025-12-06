import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Search, Plus, Play, User, Calendar, Tag, Settings, Loader2, BookOpen, Image } from "lucide-react";
import { useNavigate } from "react-router-dom";
import ActorCard from "@/components/ActorCard";
import CreateActorDialog from "@/components/CreateActorDialog";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/hooks/use-toast";
import woodTexture from "@/assets/wood-texture.jpg";
import parchmentTexture from "@/assets/parchment-texture.jpg";

interface Actor {
  id: string;
  first_name: string;
  last_name: string;
  full_name: string | null;
  role: string;
  era: string;
  bio: string;
  voice_id: string | null;
  tags: string[] | null;
  image_url: string | null;
}

const Index = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [actors, setActors] = useState<Actor[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Load actors from database
  const loadActors = async () => {
    setIsLoading(true);
    try {
      const { data, error } = await supabase
        .from('actors')
        .select('*')
        .order('created_at', { ascending: false });

      if (error) throw error;

      setActors(data || []);
    } catch (error) {
      console.error('Error loading actors:', error);
      toast({
        title: "Error",
        description: "Failed to load actors",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Set up real-time subscription
  useEffect(() => {
    loadActors();

    const channel = supabase
      .channel('actors-changes')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'actors'
        },
        (payload) => {
          console.log('Actor change detected:', payload);
          loadActors(); // Reload actors on any change
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  const allTags = Array.from(
    new Set(actors.flatMap((actor) => actor.tags || []))
  );

  const filteredActors = actors.filter((actor) => {
    const fullName = actor.full_name || `${actor.first_name} ${actor.last_name}`;
    const matchesSearch =
      fullName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      actor.role.toLowerCase().includes(searchQuery.toLowerCase()) ||
      actor.bio.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesTag = !selectedTag || (actor.tags && actor.tags.includes(selectedTag));

    return matchesSearch && matchesTag;
  });

  // Transform actors to match ActorCard interface
  const transformedActors = filteredActors.map(actor => ({
    id: actor.id,
    firstName: actor.first_name,
    lastName: actor.last_name,
    fullName: actor.full_name || `${actor.first_name} ${actor.last_name}`,
    role: actor.role,
    era: actor.era,
    bio: actor.bio,
    voiceId: actor.voice_id || '',
    tags: actor.tags || [],
    imageUrl: actor.image_url || '',
  }));

  return (
    <div className="min-h-screen relative">
      {/* Weathered Wood Background */}
      <div 
        className="fixed inset-0 pointer-events-none opacity-40" 
        style={{ 
          backgroundImage: `url(${woodTexture})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundAttachment: 'fixed'
        }} 
      />
      {/* Parchment Overlay */}
      <div 
        className="fixed inset-0 pointer-events-none opacity-60 mix-blend-multiply" 
        style={{ 
          backgroundImage: `url(${parchmentTexture})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundAttachment: 'fixed'
        }} 
      />
      {/* Additional texture overlay */}
      <div className="fixed inset-0 bg-texture-paper pointer-events-none opacity-20" />
      
      {/* Header */}
      <header className="border-b-4 border-primary/70 backdrop-blur-sm sticky top-0 z-10 shadow-lifted relative" style={{ 
        backgroundImage: `linear-gradient(to bottom, rgba(30, 20, 10, 0.95), rgba(30, 20, 10, 0.85)), url(${woodTexture})`,
        backgroundSize: 'cover'
      }}>
        <div className="absolute inset-0 bg-texture-paper opacity-10 pointer-events-none" />
        <div className="container mx-auto px-4 py-8 relative">
          <div className="flex items-center justify-between mb-8">
            <div className="space-y-2">
              <h1 className="text-6xl font-western font-bold text-primary-foreground drop-shadow-[0_6px_12px_rgba(0,0,0,0.9)] animate-fade-in tracking-wider [text-shadow:_2px_2px_4px_rgb(0_0_0_/_80%),_-1px_-1px_2px_rgb(139_69_19_/_30%)]">
                Stories of the West
              </h1>
              <p className="text-xl font-body text-primary-foreground/90 italic animate-fade-in border-l-4 border-secondary pl-4 drop-shadow-lg" style={{ animationDelay: "0.1s" }}>
                Actor Voice Library • Native American & Cowboys Heritage
              </p>
            </div>
            <div className="flex gap-3">
              <Button
                onClick={() => navigate('/story-templates')}
                variant="outline"
                size="lg"
                className="animate-fade-in shadow-photo hover:shadow-lifted transition-all duration-300 font-body text-lg px-6 py-6 border-2 border-primary/40 hover:scale-105 bg-background/80"
                style={{ animationDelay: "0.05s" }}
              >
                <BookOpen className="mr-2 h-6 w-6" />
                Story Templates
              </Button>
              <Button
                onClick={() => navigate('/story-library')}
                variant="outline"
                size="lg"
                className="animate-fade-in shadow-photo hover:shadow-lifted transition-all duration-300 font-body text-lg px-6 py-6 border-2 border-primary/40 hover:scale-105 bg-background/80"
                style={{ animationDelay: "0.1s" }}
              >
                <BookOpen className="mr-2 h-6 w-6" />
                Story Library
              </Button>
              <Button
                onClick={() => navigate('/story-creation')}
                variant="outline"
                size="lg"
                className="animate-fade-in shadow-photo hover:shadow-lifted transition-all duration-300 font-body text-lg px-6 py-6 border-2 border-primary/40 hover:scale-105 bg-background/80"
                style={{ animationDelay: "0.15s" }}
              >
                <Play className="mr-2 h-6 w-6" />
                Create Story
              </Button>
              <Button
                onClick={() => navigate('/voice-library')}
                variant="outline"
                size="lg"
                className="animate-fade-in shadow-photo hover:shadow-lifted transition-all duration-300 font-body text-lg px-6 py-6 border-2 border-primary/40 hover:scale-105 bg-background/80"
                style={{ animationDelay: "0.2s" }}
              >
                <Settings className="mr-2 h-6 w-6" />
                Voice Management
              </Button>
              <Button
                onClick={() => navigate('/portrait-gallery')}
                variant="outline"
                size="lg"
                className="animate-fade-in shadow-photo hover:shadow-lifted transition-all duration-300 font-body text-lg px-6 py-6 border-2 border-primary/40 hover:scale-105 bg-background/80"
                style={{ animationDelay: "0.225s" }}
              >
                <Image className="mr-2 h-6 w-6" />
                Portrait Gallery
              </Button>
              <Button
                onClick={() => setIsCreateOpen(true)}
                size="lg"
                className="animate-fade-in shadow-photo hover:shadow-lifted transition-all duration-300 bg-gradient-western text-primary-foreground font-body text-lg px-8 py-6 border-2 border-primary/20 hover:scale-105"
                style={{ animationDelay: "0.25s" }}
              >
                <Plus className="mr-2 h-6 w-6" />
                Create Actor
              </Button>
            </div>
          </div>

          {/* Search */}
          <div className="relative animate-fade-in" style={{ animationDelay: "0.3s" }}>
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-foreground h-6 w-6" />
            <Input
              type="text"
              placeholder="Search by name, role, or heritage..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-14 py-7 text-lg font-body shadow-inset bg-background/95 backdrop-blur border-3 border-primary/40 focus:border-primary focus:shadow-warm transition-all text-foreground placeholder:text-muted-foreground"
            />
          </div>

          {/* Filters */}
          <div className="flex flex-wrap gap-3 animate-fade-in mt-6" style={{ animationDelay: "0.4s" }}>
            <Button
              variant={selectedTag === null ? "default" : "outline"}
              onClick={() => setSelectedTag(null)}
              className="shadow-photo hover:shadow-warm transition-all font-body text-base px-5 py-2 border-3 border-primary/60 bg-gradient-western hover:scale-105 text-primary-foreground"
            >
              All Actors
            </Button>
            {allTags.map((tag, index) => (
              <Button
                key={tag}
                variant={selectedTag === tag ? "default" : "outline"}
                onClick={() => setSelectedTag(tag)}
                className="shadow-sm hover:shadow-warm transition-all font-body text-base px-5 py-2 border-2 border-primary/40 hover:scale-105 hover:bg-gradient-turquoise hover:text-secondary-foreground bg-background/80 text-foreground"
                style={{ animationDelay: `${0.5 + index * 0.05}s` }}
              >
                <Tag className="mr-2 h-4 w-4" />
                {tag}
              </Button>
            ))}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-12 relative">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
          <Card className="shadow-photo hover:shadow-lifted transition-all animate-fade-in border-4 border-primary/50 backdrop-blur relative overflow-hidden group hover:scale-105 duration-300" style={{ 
            animationDelay: "0.5s",
            backgroundImage: `linear-gradient(rgba(0,0,0,0.2), rgba(0,0,0,0.1)), url(${parchmentTexture})`,
            backgroundSize: 'cover'
          }}>
            <div className="absolute inset-0 bg-texture-paper opacity-20 pointer-events-none" />
            <div className="flex items-center justify-between p-8 relative">
              <div>
                <p className="text-base font-body text-foreground/80 mb-2 uppercase tracking-wide font-bold">Total Actors</p>
                <p className="text-5xl font-western font-bold text-primary drop-shadow-lg">{actors.length}</p>
              </div>
              <User className="h-16 w-16 text-primary/40 group-hover:text-primary/60 transition-colors" />
            </div>
          </Card>
          
          <Card className="shadow-photo hover:shadow-lifted transition-all animate-fade-in border-4 border-primary/50 backdrop-blur relative overflow-hidden group hover:scale-105 duration-300" style={{ 
            animationDelay: "0.6s",
            backgroundImage: `linear-gradient(rgba(0,0,0,0.2), rgba(0,0,0,0.1)), url(${parchmentTexture})`,
            backgroundSize: 'cover'
          }}>
            <div className="absolute inset-0 bg-texture-paper opacity-20 pointer-events-none" />
            <div className="flex items-center justify-between p-8 relative">
              <div>
                <p className="text-base font-body text-foreground/80 mb-2 uppercase tracking-wide font-bold">Voice Profiles</p>
                <p className="text-5xl font-western font-bold text-primary drop-shadow-lg">{actors.length}</p>
              </div>
              <Play className="h-16 w-16 text-secondary/40 group-hover:text-secondary/60 transition-colors" />
            </div>
          </Card>
          
          <Card className="shadow-photo hover:shadow-lifted transition-all animate-fade-in border-4 border-primary/50 backdrop-blur relative overflow-hidden group hover:scale-105 duration-300" style={{ 
            animationDelay: "0.7s",
            backgroundImage: `linear-gradient(rgba(0,0,0,0.2), rgba(0,0,0,0.1)), url(${parchmentTexture})`,
            backgroundSize: 'cover'
          }}>
            <div className="absolute inset-0 bg-texture-paper opacity-20 pointer-events-none" />
            <div className="flex items-center justify-between p-8 relative">
              <div>
                <p className="text-base font-body text-foreground/80 mb-2 uppercase tracking-wide font-bold">Time Periods</p>
                <p className="text-5xl font-western font-bold text-primary drop-shadow-lg">5</p>
              </div>
              <Calendar className="h-16 w-16 text-accent/40 group-hover:text-accent/60 transition-colors" />
            </div>
          </Card>
        </div>

        {/* Actors Grid */}
        <div className="mb-8 animate-fade-in border-l-4 border-primary pl-6" style={{ animationDelay: "0.8s" }}>
          <h2 className="text-3xl font-western font-bold text-foreground mb-2 drop-shadow-md">
            Showing <span className="text-primary text-4xl">{filteredActors.length}</span> actor{filteredActors.length !== 1 ? 's' : ''}
          </h2>
        </div>

        {/* Actor Grid */}
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="h-12 w-12 animate-spin text-primary" />
            <p className="ml-4 text-xl font-body text-foreground">Loading actors...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {transformedActors.map((actor, index) => (
              <div
                key={actor.id}
                className="animate-fade-in"
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <ActorCard actor={actor} onUpdate={loadActors} />
              </div>
            ))}
          </div>
        )}

        {/* Empty State */}
        {!isLoading && transformedActors.length === 0 && (
          <div className="text-center py-20">
            <User className="h-20 w-20 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-2xl font-western font-bold text-foreground mb-2">
              No actors found
            </h3>
            <p className="text-muted-foreground mb-6">
              Try adjusting your search or filters
            </p>
            <Button onClick={() => setSearchQuery("")} variant="outline">
              Clear Search
            </Button>
          </div>
        )}
      </main>

      <CreateActorDialog 
        open={isCreateOpen} 
        onOpenChange={setIsCreateOpen}
        onActorCreated={loadActors}
      />
    </div>
  );
};

export default Index;
