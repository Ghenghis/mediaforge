import { useState } from "react";
import { supabase } from "@/integrations/supabase/client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Package, Plus, FolderOpen, Shuffle } from "lucide-react";
import { toast } from "sonner";

interface PresetCollectionsProps {
  onApplyCollection?: (presets: any[]) => void;
}

export const PresetCollections = ({ onApplyCollection }: PresetCollectionsProps) => {
  const queryClient = useQueryClient();
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [collectionName, setCollectionName] = useState("");
  const [collectionDescription, setCollectionDescription] = useState("");
  const [creatorName, setCreatorName] = useState("");
  const [isRandomized, setIsRandomized] = useState(false);
  const [randomAgeMin, setRandomAgeMin] = useState(18);
  const [randomAgeMax, setRandomAgeMax] = useState(100);
  const [randomCharacterStyle, setRandomCharacterStyle] = useState("");

  const { data: collections, isLoading } = useQuery({
    queryKey: ["preset-collections"],
    queryFn: async () => {
      const { data, error } = await supabase
        .from("portrait_preset_collections")
        .select(`
          *,
          presets:portrait_collection_presets(
            preset:portrait_presets(*)
          )
        `)
        .eq("is_public", true)
        .order("created_at", { ascending: false });

      if (error) throw error;
      return data;
    },
  });

  const createMutation = useMutation({
    mutationFn: async (collectionData: any) => {
      const { data, error } = await supabase
        .from("portrait_preset_collections")
        .insert(collectionData)
        .select()
        .single();

      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      toast.success("Collection created!");
      setCreateDialogOpen(false);
      setCollectionName("");
      setCollectionDescription("");
      setCreatorName("");
      queryClient.invalidateQueries({ queryKey: ["preset-collections"] });
    },
    onError: () => {
      toast.error("Failed to create collection");
    },
  });

  const handleCreateCollection = () => {
    if (!collectionName.trim()) {
      toast.error("Please enter a collection name");
      return;
    }

    const randomizationRules = isRandomized ? {
      ageMin: randomAgeMin,
      ageMax: randomAgeMax,
      characterStyle: randomCharacterStyle || null,
    } : {};

    createMutation.mutate({
      name: collectionName,
      description: collectionDescription,
      creator_name: creatorName || "Anonymous",
      is_randomized: isRandomized,
      randomization_rules: randomizationRules,
    });
  };

  const handleApplyCollection = (collection: any) => {
    const presets = collection.presets?.map((p: any) => p.preset).filter(Boolean) || [];
    if (onApplyCollection && presets.length > 0) {
      onApplyCollection(presets);
      toast.success(`Applied ${presets.length} presets from ${collection.name}`);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Preset Collections</h3>
          <p className="text-sm text-muted-foreground">Themed bundles of portrait presets</p>
        </div>
        <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Create Collection
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Collection</DialogTitle>
              <DialogDescription>
                Group related presets together by theme or style
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Collection Name</Label>
                <Input
                  placeholder="e.g., Western Heroes, Victorian Era"
                  value={collectionName}
                  onChange={(e) => setCollectionName(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>Description</Label>
                <Textarea
                  placeholder="Describe this collection..."
                  value={collectionDescription}
                  onChange={(e) => setCollectionDescription(e.target.value)}
                  rows={3}
                />
              </div>
              <div className="space-y-2">
                <Label>Your Name (optional)</Label>
                <Input
                  placeholder="Anonymous"
                  value={creatorName}
                  onChange={(e) => setCreatorName(e.target.value)}
                />
              </div>

              <div className="space-y-4 pt-4 border-t">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Randomized Collection</Label>
                    <p className="text-xs text-muted-foreground">
                      Generate random presets based on criteria
                    </p>
                  </div>
                  <Switch
                    checked={isRandomized}
                    onCheckedChange={setIsRandomized}
                  />
                </div>

                {isRandomized && (
                  <div className="space-y-4 pl-4 border-l-2 border-primary/20">
                    <div className="space-y-2">
                      <Label>Age Range</Label>
                      <div className="grid grid-cols-2 gap-2">
                        <Input
                          type="number"
                          min={18}
                          max={100}
                          placeholder="Min (18)"
                          value={randomAgeMin}
                          onChange={(e) => setRandomAgeMin(Number(e.target.value))}
                        />
                        <Input
                          type="number"
                          min={18}
                          max={100}
                          placeholder="Max (100)"
                          value={randomAgeMax}
                          onChange={(e) => setRandomAgeMax(Number(e.target.value))}
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label>Character Style (optional)</Label>
                      <Select value={randomCharacterStyle} onValueChange={setRandomCharacterStyle}>
                        <SelectTrigger>
                          <SelectValue placeholder="Any style..." />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="">Any Style</SelectItem>
                          <SelectItem value="Professional">Professional</SelectItem>
                          <SelectItem value="Sexy">Sexy</SelectItem>
                          <SelectItem value="Trailer Trash">Trailer Trash</SelectItem>
                          <SelectItem value="Farm Girl">Farm Girl</SelectItem>
                          <SelectItem value="Gymnast">Gymnast</SelectItem>
                          <SelectItem value="Volleyball Player">Volleyball Player</SelectItem>
                          <SelectItem value="Dancer">Dancer</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                )}
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => setCreateDialogOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  className="flex-1"
                  onClick={handleCreateCollection}
                  disabled={createMutation.isPending}
                >
                  Create
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <ScrollArea className="h-[400px]">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pr-4">
          {isLoading ? (
            <div className="col-span-full text-center py-12 text-muted-foreground">
              Loading collections...
            </div>
          ) : collections?.length === 0 ? (
            <div className="col-span-full text-center py-12 text-muted-foreground">
              No collections yet
            </div>
          ) : (
            collections?.map((collection) => {
              const presetCount = collection.presets?.length || 0;
              return (
                <Card key={collection.id} className="hover:border-primary transition-colors">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="space-y-1">
                        <CardTitle className="text-lg">{collection.name}</CardTitle>
                        {collection.creator_name && (
                          <CardDescription>by {collection.creator_name}</CardDescription>
                        )}
                      </div>
                      <Package className="h-5 w-5 text-primary" />
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {collection.description && (
                      <p className="text-sm text-muted-foreground">{collection.description}</p>
                    )}

                    <div className="flex items-center gap-2 flex-wrap">
                      <FolderOpen className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm text-muted-foreground">
                        {presetCount} preset{presetCount !== 1 ? 's' : ''}
                      </span>
                      {collection.is_randomized && (
                        <Badge variant="secondary" className="gap-1">
                          <Shuffle className="h-3 w-3" />
                          Randomized
                        </Badge>
                      )}
                    </div>

                    <Button
                      className="w-full"
                      onClick={() => handleApplyCollection(collection)}
                      disabled={presetCount === 0}
                    >
                      Apply Collection
                    </Button>
                  </CardContent>
                </Card>
              );
            })
          )}
        </div>
      </ScrollArea>
    </div>
  );
};
