import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { generatePortrait } from "@/services/aiService";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ArrowLeft, RefreshCw, Loader2, History, Palette, Settings, SlidersHorizontal, Sparkles, Download, BarChart3, Store, FlaskConical, CheckSquare, Square } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import PortraitCustomizationDialog, { PortraitCustomization } from "@/components/PortraitCustomizationDialog";
import ImageComparisonDialog from "@/components/ImageComparisonDialog";
import { PresetMarketplace } from "@/components/PresetMarketplace";
import { SavePresetDialog } from "@/components/SavePresetDialog";
import { ABTestingComparison } from "@/components/ABTestingComparison";
import { MyReviews } from "@/components/MyReviews";
import { PresetCollections } from "@/components/PresetCollections";
import { PresetRecommendations } from "@/components/PresetRecommendations";
import { FavoritePresets } from "@/components/FavoritePresets";
import JSZip from "jszip";

interface Actor {
  id: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: string;
  era: string;
  image_url: string | null;
}

interface PortraitHistory {
  id: string;
  image_url: string;
  color_mode: string;
  generation_params: any;
  created_at: string;
  is_current: boolean;
}

const PortraitGallery = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();
  const [actors, setActors] = useState<Actor[]>([]);
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState<Record<string, boolean>>({});
  const [colorMode, setColorMode] = useState<Record<string, 'bw' | 'color'>>({});
  const [batchGenerating, setBatchGenerating] = useState(false);
  const [selectedActorHistory, setSelectedActorHistory] = useState<string | null>(null);
  const [portraitHistory, setPortraitHistory] = useState<PortraitHistory[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [customizationActor, setCustomizationActor] = useState<Actor | null>(null);
  const [colorizing, setColorizing] = useState<Record<string, boolean>>({});
  const [bulkColorizing, setBulkColorizing] = useState(false);
  const [comparisonActor, setComparisonActor] = useState<Actor | null>(null);
  const [comparisonImages, setComparisonImages] = useState<{ bw: string; color: string } | null>(null);
  const [stylingActors, setStylingActors] = useState<Record<string, boolean>>({});
  const [exporting, setExporting] = useState(false);
  const [batchProgress, setBatchProgress] = useState({ current: 0, total: 0 });
  const [filterEra, setFilterEra] = useState<string>("all");
  const [filterRole, setFilterRole] = useState<string>("all");
  const [filterStyleProfile, setFilterStyleProfile] = useState<string>("all");
  const [filterCharacterType, setFilterCharacterType] = useState<string>("all");
  const [selectedActors, setSelectedActors] = useState<Set<string>>(new Set());
  const [batchEditOpen, setBatchEditOpen] = useState(false);
  const [savePresetOpen, setSavePresetOpen] = useState(false);
  const [currentCustomization, setCurrentCustomization] = useState<any>(null);
  const [abTestImageA, setAbTestImageA] = useState<string>();
  const [abTestImageB, setAbTestImageB] = useState<string>();

  useEffect(() => {
    fetchActors();
  }, []);

  // Handle preset deep-linking
  useEffect(() => {
    const presetId = searchParams.get("preset");
    if (presetId) {
      loadPresetById(presetId);
    }
  }, [searchParams]);

  const loadPresetById = async (presetId: string) => {
    try {
      const { data, error } = await supabase
        .from("portrait_presets")
        .select("*")
        .eq("id", presetId)
        .maybeSingle();

      if (error) throw error;

      if (data) {
        const customization = {
          age: data.age,
          weathering: data.weathering,
          detailLevel: data.detail_level,
          clothingFormality: data.clothing_formality,
          coverage: data.coverage,
          fit: data.fit,
          styleProfile: data.style_profile,
          accentFocus: data.accent_focus,
          textureDetail: data.texture_detail,
          contrast: data.contrast,
          rating: data.rating,
        };
        setCurrentCustomization(customization);
        toast({
          title: "Preset Loaded",
          description: `Loaded preset: ${data.name}`,
        });
      } else {
        toast({
          title: "Preset Not Found",
          description: "The requested preset could not be found",
          variant: "destructive",
        });
      }
    } catch (error: any) {
      console.error("Error loading preset:", error);
      toast({
        title: "Error",
        description: "Failed to load preset",
        variant: "destructive",
      });
    }
  };

  const fetchActors = async () => {
    setLoading(true);
    const { data, error } = await supabase
      .from('actors')
      .select('*')
      .order('created_at', { ascending: false });

    if (error) {
      toast({
        title: "Error",
        description: "Failed to load actors",
        variant: "destructive",
      });
    } else {
      setActors(data || []);
      const initialColorMode: Record<string, 'bw' | 'color'> = {};
      data?.forEach(actor => {
        initialColorMode[actor.id] = 'bw';
      });
      setColorMode(initialColorMode);
    }
    setLoading(false);
  };

  const fetchPortraitHistory = async (actorId: string) => {
    setLoadingHistory(true);
    const { data, error } = await supabase
      .from('actor_portrait_history')
      .select('*')
      .eq('actor_id', actorId)
      .order('created_at', { ascending: false });

    if (error) {
      toast({
        title: "Error",
        description: "Failed to load portrait history",
        variant: "destructive",
      });
    } else {
      setPortraitHistory(data || []);
    }
    setLoadingHistory(false);
  };

  const handleViewHistory = (actorId: string) => {
    setSelectedActorHistory(actorId);
    fetchPortraitHistory(actorId);
  };

  const handleRestorePortrait = async (actor: Actor, historyItem: PortraitHistory) => {
    try {
      // Update actor with historical portrait
      const { error } = await supabase
        .from('actors')
        .update({ image_url: historyItem.image_url })
        .eq('id', actor.id);

      if (error) throw error;

      // Mark this portrait as current in history
      await supabase
        .from('actor_portrait_history')
        .update({ is_current: false })
        .eq('actor_id', actor.id);

      await supabase
        .from('actor_portrait_history')
        .update({ is_current: true })
        .eq('id', historyItem.id);

      toast({
        title: "Portrait Restored",
        description: `Restored portrait from ${new Date(historyItem.created_at).toLocaleDateString()}`,
      });

      await fetchActors();
      setSelectedActorHistory(null);
    } catch (error: any) {
      toast({
        title: "Restore Failed",
        description: error.message || "Failed to restore portrait",
        variant: "destructive",
      });
    }
  };

  const handleCustomGenerate = async (actor: Actor, customization: PortraitCustomization) => {
    setRegenerating({ ...regenerating, [actor.id]: true });

    try {
      const result = await generatePortrait({
        actorId: actor.id,
        fullName: actor.full_name,
        role: actor.role,
        era: actor.era,
        colorMode: colorMode[actor.id] || 'bw',
        customization,
      });

      if (!result.success) throw new Error(result.error);

      toast({
        title: "Custom Portrait Generated",
        description: `Created customized ${colorMode[actor.id] === 'color' ? 'color' : 'B&W'} portrait (${result.provider})`,
      });
      await fetchActors();
    } catch (error: any) {
      toast({
        title: "Generation Failed",
        description: error.message || "Failed to generate portrait",
        variant: "destructive",
      });
    } finally {
      setRegenerating({ ...regenerating, [actor.id]: false });
    }
  };

  const regeneratePortrait = async (actor: Actor) => {
    setRegenerating({ ...regenerating, [actor.id]: true });

    try {
      const result = await generatePortrait({
        actorId: actor.id,
        fullName: actor.full_name,
        role: actor.role,
        era: actor.era,
        colorMode: colorMode[actor.id] || 'bw',
      });

      if (!result.success) throw new Error(result.error);

      toast({
        title: "Portrait Regenerated",
        description: `New ${colorMode[actor.id] === 'color' ? 'color' : 'B&W'} portrait created (${result.provider})`,
      });
      await fetchActors();
    } catch (error: any) {
      toast({
        title: "Generation Failed",
        description: error.message || "Failed to regenerate portrait",
        variant: "destructive",
      });
    } finally {
      setRegenerating({ ...regenerating, [actor.id]: false });
    }
  };

  const handleColorize = async (actor: Actor) => {
    if (!actor.image_url) return;

    setColorizing({ ...colorizing, [actor.id]: true });

    try {
      const { data, error } = await supabase.functions.invoke('colorize-portrait', {
        body: {
          actorId: actor.id,
          imageUrl: actor.image_url,
          era: actor.era,
          fullName: actor.full_name,
          role: actor.role,
        },
      });

      if (error) throw error;

      if (data.success) {
        toast({
          title: "Portrait Colorized",
          description: "AI-powered colorization complete. Check history to view.",
        });
      }
    } catch (error: any) {
      toast({
        title: "Colorization Failed",
        description: error.message || "Failed to colorize portrait",
        variant: "destructive",
      });
    } finally {
      setColorizing({ ...colorizing, [actor.id]: false });
    }
  };

  const batchGenerate = async () => {
    setBatchGenerating(true);
    let successCount = 0;
    let failCount = 0;
    const actorsToGenerate = actors.filter(a => !a.image_url); // Only generate for actors without portraits
    const totalCount = actorsToGenerate.length;

    setBatchProgress({ current: 0, total: totalCount });

    toast({
      title: "Automated Batch Generation Started",
      description: `Generating portraits for ${totalCount} actors automatically...`,
    });

    for (let i = 0; i < actorsToGenerate.length; i++) {
      const actor = actorsToGenerate[i];
      setBatchProgress({ current: i + 1, total: totalCount });

      try {
        const result = await generatePortrait({
          actorId: actor.id,
          fullName: actor.full_name,
          role: actor.role,
          era: actor.era,
          colorMode: 'color', // Generate in 4K color as requested
          customization: {
            age: (actor as any).metadata?.age || 25,
            weathering: 20,
            detailLevel: 95, // Maximum detail for beauty
            clothingStyle: 80, // Beautiful traditional outfits
          },
        });

        if (!result.success) throw new Error(result.error);
        successCount++;
        toast({
          title: `Portrait ${i + 1}/${totalCount}`,
          description: `Generated for ${actor.full_name} (${result.provider})`,
        });
        
        // Rate limiting - wait between requests
        await new Promise(resolve => setTimeout(resolve, 3000));
      } catch (error: any) {
        failCount++;
        console.error(`Failed to generate portrait for ${actor.full_name}:`, error);
      }
    }

    toast({
      title: "Automated Batch Generation Complete! 🎉",
      description: `Successfully generated ${successCount} portraits. ${failCount > 0 ? `${failCount} failed.` : 'All complete!'}`,
    });

    setBatchGenerating(false);
    setBatchProgress({ current: 0, total: 0 });
    await fetchActors();
  };

  const bulkColorize = async () => {
    setBulkColorizing(true);
    let successCount = 0;
    let failCount = 0;

    const bwActors = actors.filter(a => a.image_url);

    for (const actor of bwActors) {
      try {
        const { data, error } = await supabase.functions.invoke('colorize-portrait', {
          body: {
            actorId: actor.id,
            imageUrl: actor.image_url,
            era: actor.era,
            fullName: actor.full_name,
            role: actor.role,
          },
        });

        if (error) throw error;
        if (data.success) successCount++;
        
        await new Promise(resolve => setTimeout(resolve, 2000));
      } catch (error) {
        failCount++;
      }
    }

    toast({
      title: "Bulk Colorization Complete",
      description: `Colorized ${successCount} portraits. ${failCount > 0 ? `${failCount} failed.` : ''}`,
    });

    setBulkColorizing(false);
  };

  const handleCompare = async (actor: Actor) => {
    const { data, error } = await supabase
      .from('actor_portrait_history')
      .select('*')
      .eq('actor_id', actor.id)
      .order('created_at', { ascending: false })
      .limit(10);

    if (error || !data || data.length < 2) {
      toast({
        title: "Not Enough Versions",
        description: "Need at least 2 portrait versions to compare",
        variant: "destructive",
      });
      return;
    }

    // Find first B&W and first color version
    const bwVersion = data.find(p => p.color_mode === 'bw');
    const colorVersion = data.find(p => p.color_mode === 'color');

    if (!bwVersion || !colorVersion) {
      toast({
        title: "Missing Versions",
        description: "Need both B&W and color versions to compare",
        variant: "destructive",
      });
      return;
    }

    setComparisonActor(actor);
    setComparisonImages({
      bw: bwVersion.image_url,
      color: colorVersion.image_url,
    });
  };

  const handleStyleTransfer = async (actor: Actor, style: string) => {
    if (!actor.image_url) return;

    setStylingActors({ ...stylingActors, [actor.id]: true });

    try {
      const { data, error } = await supabase.functions.invoke('style-transfer', {
        body: {
          actorId: actor.id,
          imageUrl: actor.image_url,
          style: style,
          fullName: actor.full_name,
          role: actor.role,
        },
      });

      if (error) throw error;

      if (data.success) {
        toast({
          title: "Style Applied",
          description: `${style.replace('-', ' ')} style created. Check history to view.`,
        });
      }
    } catch (error: any) {
      toast({
        title: "Style Transfer Failed",
        description: error.message || "Failed to apply style",
        variant: "destructive",
      });
    } finally {
      setStylingActors({ ...stylingActors, [actor.id]: false });
    }
  };

  const handleExportAll = async () => {
    setExporting(true);

    try {
      const zip = new JSZip();
      const portraitFolder = zip.folder("portraits");

      // Fetch all portrait history
      const { data: allPortraits, error } = await supabase
        .from('actor_portrait_history')
        .select('*, actors(full_name, role, era)')
        .order('created_at', { ascending: false });

      if (error) throw error;

      if (!allPortraits || allPortraits.length === 0) {
        toast({
          title: "No Portraits",
          description: "No portraits available to export",
          variant: "destructive",
        });
        return;
      }

      // Download and add each image
      for (const portrait of allPortraits) {
        try {
          const response = await fetch(portrait.image_url);
          const blob = await response.blob();
          const actorName = portrait.actors?.full_name?.replace(/\s+/g, '_') || 'unknown';
          const timestamp = new Date(portrait.created_at).getTime();
          const fileName = `${actorName}_${portrait.color_mode}_${timestamp}.png`;
          
          portraitFolder?.file(fileName, blob);

          // Add metadata JSON for each portrait
          const metadata = {
            actor_name: portrait.actors?.full_name,
            role: portrait.actors?.role,
            era: portrait.actors?.era,
            color_mode: portrait.color_mode,
            created_at: portrait.created_at,
            generation_params: portrait.generation_params,
          };
          portraitFolder?.file(`${actorName}_${timestamp}_metadata.json`, JSON.stringify(metadata, null, 2));
        } catch (err) {
          console.error('Failed to fetch portrait:', err);
        }
      }

      // Generate ZIP
      const content = await zip.generateAsync({ type: "blob" });
      
      // Download
      const url = URL.createObjectURL(content);
      const a = document.createElement('a');
      a.href = url;
      a.download = `portrait-collection-${Date.now()}.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast({
        title: "Export Complete",
        description: `Exported ${allPortraits.length} portraits with metadata`,
      });
    } catch (error: any) {
      toast({
        title: "Export Failed",
        description: error.message || "Failed to export portraits",
        variant: "destructive",
      });
    } finally {
      setExporting(false);
    }
  };

  const toggleColorMode = (actorId: string) => {
    setColorMode({
      ...colorMode,
      [actorId]: colorMode[actorId] === 'bw' ? 'color' : 'bw',
    });
  };

  const toggleActorSelection = (actorId: string) => {
    const newSelected = new Set(selectedActors);
    if (newSelected.has(actorId)) {
      newSelected.delete(actorId);
    } else {
      newSelected.add(actorId);
    }
    setSelectedActors(newSelected);
  };

  const selectAllFiltered = () => {
    const filteredIds = new Set(filteredActors.map((a: Actor) => a.id));
    setSelectedActors(filteredIds);
  };

  const clearSelection = () => {
    setSelectedActors(new Set());
  };

  const handleBatchEdit = async (customization: any) => {
    if (selectedActors.size === 0) {
      toast({
        title: "No Selection",
        description: "No actors selected for batch editing",
        variant: "destructive",
      });
      return;
    }

    let successCount = 0;

    for (const actorId of selectedActors) {
      try {
        const actor = actors?.find(a => a.id === actorId);
        if (!actor) continue;

        const result = await generatePortrait({
          actorId: actor.id,
          fullName: actor.full_name,
          role: actor.role,
          era: actor.era,
          colorMode: "color",
          customization,
        });

        if (!result.success) throw new Error(result.error);
        successCount++;
      } catch (error) {
        console.error(`Failed to generate for actor ${actorId}:`, error);
      }
    }

    toast({
      title: "Batch Edit Complete",
      description: `Generated ${successCount} portraits successfully!`,
    });
    setBatchEditOpen(false);
    clearSelection();
    await fetchActors();
  };

  const handleApplyPreset = (preset: any) => {
    const customization = {
      age: preset.age,
      weathering: preset.weathering,
      detailLevel: preset.detail_level,
      clothingFormality: preset.clothing_formality,
      coverage: preset.coverage,
      fit: preset.fit,
      styleProfile: preset.style_profile,
      accentFocus: preset.accent_focus,
      textureDetail: preset.texture_detail,
      contrast: preset.contrast,
      rating: preset.rating,
    };
    setCurrentCustomization(customization);
    toast({
      title: "Preset Loaded",
      description: "Preset loaded! Open customization to use it.",
    });
  };

  const handleABTestGenerate = async (settings: any, version: 'A' | 'B') => {
    const mockImage = `https://picsum.photos/seed/${Math.random()}/400/400`;
    
    if (version === 'A') {
      setAbTestImageA(mockImage);
    } else {
      setAbTestImageB(mockImage);
    }
    
    toast({
      title: "Generated",
      description: `Version ${version} generated!`,
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  const selectedActor = actors.find(a => a.id === selectedActorHistory);
  
  // Get unique values for filters
  const uniqueEras = ['all', ...Array.from(new Set(actors.map(a => a.era)))];
  const uniqueRoles = ['all', ...Array.from(new Set(actors.map(a => a.role)))];
  
  // Apply filters
  const filteredActors = actors.filter(actor => {
    if (filterEra !== 'all' && actor.era !== filterEra) return false;
    if (filterRole !== 'all' && actor.role !== filterRole) return false;
    if (filterCharacterType !== 'all') {
      // Check metadata for character type or the character_type column
      const actorType = (actor as any).character_type || (actor as any).metadata?.character_type;
      if (actorType !== filterCharacterType) return false;
    }
    return true;
  });

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="bg-card border-b border-border sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/')}
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back
              </Button>
              <h1 className="font-western text-2xl text-foreground">Portrait Gallery</h1>
            </div>
            <div className="flex gap-2">
              <Button
                onClick={() => navigate('/portrait-analytics')}
                variant="outline"
              >
                <BarChart3 className="mr-2 h-4 w-4" />
                Analytics
              </Button>
              <Button
                onClick={handleExportAll}
                disabled={exporting}
                variant="outline"
              >
                {exporting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Exporting...
                  </>
                ) : (
                  <>
                    <Download className="mr-2 h-4 w-4" />
                    Export All
                  </>
                )}
              </Button>
              <Button
                onClick={bulkColorize}
                disabled={bulkColorizing}
                variant="outline"
              >
                {bulkColorizing ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Colorizing All...
                  </>
                ) : (
                  <>
                    <Palette className="mr-2 h-4 w-4" />
                    Bulk Colorize
                  </>
                )}
              </Button>
              <Button
                onClick={batchGenerate}
                disabled={batchGenerating}
                className="bg-gradient-western"
              >
                {batchGenerating ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating {batchProgress.current}/{batchProgress.total}...
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2 h-4 w-4" />
                    Auto-Generate All 4K Color
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
        
        {/* Filters */}
        <div className="border-t border-border py-3">
          <div className="container mx-auto px-4">
            <div className="flex items-center gap-4 flex-wrap">
              <div className="flex items-center gap-2">
                <Label className="text-sm">Era:</Label>
                <Select value={filterEra} onValueChange={setFilterEra}>
                  <SelectTrigger className="w-[180px] h-9">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-background z-50">
                    {uniqueEras.map(era => (
                      <SelectItem key={era} value={era}>
                        {era === 'all' ? 'All Eras' : era}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div className="flex items-center gap-2">
                <Label className="text-sm">Role:</Label>
                <Select value={filterRole} onValueChange={setFilterRole}>
                  <SelectTrigger className="w-[180px] h-9">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-background z-50">
                    {uniqueRoles.map(role => (
                      <SelectItem key={role} value={role}>
                        {role === 'all' ? 'All Roles' : role}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center gap-2">
                <Label className="text-sm">Character Type:</Label>
                <Select value={filterCharacterType} onValueChange={setFilterCharacterType}>
                  <SelectTrigger className="w-[200px] h-9">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-background z-50 max-h-[300px]">
                    <SelectItem value="all">All Types</SelectItem>
                    <SelectItem value="professional">Professional</SelectItem>
                    <SelectItem value="sexy">Sexy</SelectItem>
                    <SelectItem value="farm-girl">Farm Girl</SelectItem>
                    <SelectItem value="gymnast">Gymnast</SelectItem>
                    <SelectItem value="volleyball-player">Volleyball Player</SelectItem>
                    <SelectItem value="hooters-girl">Hooters Girl</SelectItem>
                    <SelectItem value="dancer">Dancer</SelectItem>
                    <SelectItem value="cheerleader">Cheerleader</SelectItem>
                    <SelectItem value="athlete">Athlete</SelectItem>
                    <SelectItem value="bartender">Bartender</SelectItem>
                    <SelectItem value="secretary">Secretary</SelectItem>
                    <SelectItem value="teacher">Teacher</SelectItem>
                    <SelectItem value="nurse">Nurse</SelectItem>
                    <SelectItem value="cowgirl">Cowgirl</SelectItem>
                    <SelectItem value="model">Model</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="ml-auto">
                <Badge variant="secondary">
                  Showing {filteredActors.length} of {actors.length} actors
                </Badge>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Gallery Grid */}
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredActors.map((actor) => (
            <Card key={actor.id} className="overflow-hidden">
              <CardContent className="p-6">
                {/* Portrait Image */}
                <div className="aspect-square bg-muted rounded-lg overflow-hidden mb-4">
                  {actor.image_url ? (
                    <img
                      src={actor.image_url}
                      alt={actor.full_name}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-muted-foreground">
                      No portrait yet
                    </div>
                  )}
                </div>

                {/* Actor Info */}
                <div className="space-y-3">
                  <div>
                    <h3 className="font-western text-xl text-foreground">
                      {actor.full_name}
                    </h3>
                    <p className="text-sm text-muted-foreground italic">{actor.role}</p>
                    <Badge variant="secondary" className="mt-1">{actor.era}</Badge>
                  </div>

                  {/* Color Mode Toggle */}
                  <div className="flex items-center justify-between py-2 border-t border-border">
                    <Label htmlFor={`color-${actor.id}`} className="text-sm">
                      {colorMode[actor.id] === 'color' ? 'Full Color 4K' : 'B&W 4K'}
                    </Label>
                    <Switch
                      id={`color-${actor.id}`}
                      checked={colorMode[actor.id] === 'color'}
                      onCheckedChange={() => toggleColorMode(actor.id)}
                    />
                  </div>

                  {/* Action Buttons */}
                  <div className="space-y-2">
                    <Button
                      onClick={() => setCustomizationActor(actor)}
                      disabled={regenerating[actor.id]}
                      variant="outline"
                      className="w-full"
                    >
                      <Settings className="mr-2 h-4 w-4" />
                      Custom Generate
                    </Button>

                    <Button
                      onClick={() => regeneratePortrait(actor)}
                      disabled={regenerating[actor.id]}
                      variant="outline"
                      className="w-full"
                    >
                      {regenerating[actor.id] ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Generating...
                        </>
                      ) : (
                        <>
                          <RefreshCw className="mr-2 h-4 w-4" />
                          Quick Regenerate
                        </>
                      )}
                    </Button>

                    <Button
                      onClick={() => handleColorize(actor)}
                      disabled={colorizing[actor.id] || !actor.image_url}
                      variant="outline"
                      className="w-full"
                    >
                      {colorizing[actor.id] ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Colorizing...
                        </>
                      ) : (
                        <>
                          <Palette className="mr-2 h-4 w-4" />
                          AI Colorize
                        </>
                      )}
                    </Button>

                    {/* Style Transfer Dropdown */}
                    <div className="w-full">
                      <Select
                        onValueChange={(style) => handleStyleTransfer(actor, style)}
                        disabled={stylingActors[actor.id] || !actor.image_url}
                      >
                        <SelectTrigger className="w-full">
                          {stylingActors[actor.id] ? (
                            <>
                              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              Styling...
                            </>
                          ) : (
                            <>
                              <Sparkles className="mr-2 h-4 w-4" />
                              <SelectValue placeholder="Apply Style" />
                            </>
                          )}
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="oil-painting">Oil Painting</SelectItem>
                          <SelectItem value="charcoal-sketch">Charcoal Sketch</SelectItem>
                          <SelectItem value="daguerreotype">Daguerreotype</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="grid grid-cols-2 gap-2">
                      <Button
                        onClick={() => handleViewHistory(actor.id)}
                        variant="secondary"
                        className="w-full"
                      >
                        <History className="mr-2 h-4 w-4" />
                        View History
                      </Button>
                      <Button
                        onClick={() => handleCompare(actor)}
                        variant="secondary"
                        className="w-full"
                      >
                        <SlidersHorizontal className="mr-2 h-4 w-4" />
                        Compare
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Preset Marketplace & Collections & A/B Testing */}
      <div className="border-t border-border bg-muted/40">
        <div className="container mx-auto px-4 py-8 space-y-10">
          <section>
            <h2 className="text-2xl font-semibold mb-4">Smart Recommendations</h2>
            <PresetRecommendations onApplyPreset={handleApplyPreset} />
          </section>

          <section>
            <FavoritePresets onApplyPreset={handleApplyPreset} />
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">Preset Collections</h2>
            <PresetCollections onApplyCollection={(presets) => {
              if (presets.length > 0) {
                handleApplyPreset(presets[0]);
              }
            }} />
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">Preset Marketplace</h2>
            <PresetMarketplace onApplyPreset={handleApplyPreset} />
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">My Reviews</h2>
            <MyReviews />
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">A/B Testing Lab</h2>
            <ABTestingComparison
              onGenerateA={(settings) => handleABTestGenerate(settings, 'A')}
              onGenerateB={(settings) => handleABTestGenerate(settings, 'B')}
              onSavePreferred={(settings) => {
                setCurrentCustomization(settings);
                setSavePresetOpen(true);
              }}
              imageA={abTestImageA}
              imageB={abTestImageB}
            />
          </section>
        </div>
      </div>

      {/* History Dialog */}
      <Dialog open={!!selectedActorHistory} onOpenChange={() => setSelectedActorHistory(null)}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-western text-2xl">
              Portrait History - {selectedActor?.full_name}
            </DialogTitle>
          </DialogHeader>

          {loadingHistory ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 py-4">
              {portraitHistory.map((item) => (
                <Card key={item.id} className="overflow-hidden">
                  <CardContent className="p-4">
                    <div className="aspect-square bg-muted rounded-lg overflow-hidden mb-3">
                      <img
                        src={item.image_url}
                        alt="Historical portrait"
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Badge variant={item.is_current ? "default" : "secondary"}>
                          {item.is_current ? "Current" : item.color_mode === 'color' ? 'Color' : 'B&W'}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {new Date(item.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      {!item.is_current && selectedActor && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="w-full"
                          onClick={() => handleRestorePortrait(selectedActor, item)}
                        >
                          Restore
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}

              {portraitHistory.length === 0 && (
                <div className="col-span-full text-center py-8 text-muted-foreground">
                  No portrait history yet
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Customization Dialog */}
      <PortraitCustomizationDialog
        open={!!customizationActor}
        onOpenChange={(open) => {
          if (!open) {
            setCustomizationActor(null);
          }
        }}
        onGenerate={async (customization) => {
          if (customizationActor) {
            await handleCustomGenerate(customizationActor, customization);
          }
        }}
        actorName={customizationActor?.full_name || ""}
      />

      {/* Batch Edit Dialog */}
      {batchEditOpen && (
        <PortraitCustomizationDialog
          open={batchEditOpen}
          onOpenChange={setBatchEditOpen}
          onGenerate={handleBatchEdit}
          actorName={`${selectedActors.size} selected actors`}
        />
      )}

      {/* Save Preset Dialog */}
      <SavePresetDialog
        open={savePresetOpen}
        onOpenChange={setSavePresetOpen}
        currentSettings={currentCustomization || {}}
      />

      {/* Comparison Dialog */}
      {comparisonActor && comparisonImages && (
        <ImageComparisonDialog
          open={!!comparisonActor}
          onOpenChange={(open) => {
            if (!open) {
              setComparisonActor(null);
              setComparisonImages(null);
            }
          }}
          bwImageUrl={comparisonImages.bw}
          colorImageUrl={comparisonImages.color}
          actorName={comparisonActor.full_name}
        />
      )}
    </div>
  );
};

export default PortraitGallery;
