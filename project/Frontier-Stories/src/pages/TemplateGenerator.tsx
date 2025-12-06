import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ArrowLeft, Wand2, Loader2, Check, AlertCircle, Trash2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/hooks/use-toast";
import woodTexture from "@/assets/wood-texture.jpg";
import parchmentTexture from "@/assets/parchment-texture.jpg";

interface GeneratedTemplate {
  title: string;
  description: string;
  genre: string;
  era: string;
  icon_name: string;
  lines: Array<{
    actor_role: string;
    actor_first_name: string;
    actor_last_name: string;
    text: string;
    line_number?: number;
  }>;
}

const GENRES = [
  'Historical Romance',
  'Western Adventure',
  'Frontier Mystery',
  'Native American Legend',
  'Cowboy Drama',
  'Settler Stories',
  'Tribal Saga',
  'Pioneer Journey'
];

const THEMES = [
  'Forbidden Love',
  'Arranged Marriage',
  'Star-Crossed Lovers',
  'Rescue Romance',
  'Cultural Bridge',
  'Tribal Alliance',
  'Revenge and Redemption',
  'Family Feud',
  'Lost Heritage',
  'Frontier Justice',
  'Spirit Quest',
  'Cattle Drive',
  'Gold Rush',
  'Treaty Negotiations'
];

const ERAS = ['1860s', '1870s', '1880s', '1890s'];

const TemplateGenerator = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  
  const [genre, setGenre] = useState('');
  const [theme, setTheme] = useState('');
  const [era, setEra] = useState('1870s');
  const [characterCount, setCharacterCount] = useState('3');
  const [batchSize, setBatchSize] = useState('5');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [generatedTemplates, setGeneratedTemplates] = useState<GeneratedTemplate[]>([]);
  const [savedCount, setSavedCount] = useState(0);

  const handleGenerateSingle = async () => {
    if (!genre || !theme) {
      toast({
        title: "Missing Information",
        description: "Please select both genre and theme",
        variant: "destructive",
      });
      return;
    }

    setIsGenerating(true);

    try {
      const { data, error } = await supabase.functions.invoke('generate-template', {
        body: {
          genre,
          theme,
          characterCount: parseInt(characterCount),
          era,
        },
      });

      if (error) throw error;

      if (data.template) {
        setGeneratedTemplates([...generatedTemplates, data.template]);
        toast({
          title: "Template Generated",
          description: "AI has created a new story template",
        });
      }
    } catch (error: any) {
      console.error('Error generating template:', error);
      toast({
        title: "Generation Failed",
        description: error.message || "Failed to generate template",
        variant: "destructive",
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleGenerateBatch = async () => {
    if (!genre || !theme) {
      toast({
        title: "Missing Information",
        description: "Please select both genre and theme",
        variant: "destructive",
      });
      return;
    }

    setIsGenerating(true);
    const count = parseInt(batchSize);
    const newTemplates: GeneratedTemplate[] = [];

    try {
      for (let i = 0; i < count; i++) {
        const { data, error } = await supabase.functions.invoke('generate-template', {
          body: {
            genre,
            theme,
            characterCount: parseInt(characterCount),
            era,
          },
        });

        if (error) {
          console.error(`Error on template ${i + 1}:`, error);
          continue;
        }

        if (data.template) {
          newTemplates.push(data.template);
        }

        // Small delay to avoid rate limiting
        if (i < count - 1) {
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      }

      setGeneratedTemplates([...generatedTemplates, ...newTemplates]);
      toast({
        title: "Batch Complete",
        description: `Generated ${newTemplates.length} templates`,
      });
    } catch (error: any) {
      console.error('Batch generation error:', error);
      toast({
        title: "Batch Generation Error",
        description: error.message || "Some templates failed to generate",
        variant: "destructive",
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSaveAll = async () => {
    if (generatedTemplates.length === 0) {
      toast({
        title: "No Templates",
        description: "Generate some templates first",
        variant: "destructive",
      });
      return;
    }

    setIsSaving(true);
    let saved = 0;

    try {
      for (const template of generatedTemplates) {
        // Insert template
        const { data: templateData, error: templateError } = await supabase
          .from('story_templates')
          .insert({
            title: template.title,
            description: template.description,
            genre: template.genre,
            era: template.era,
            icon_name: template.icon_name,
          })
          .select()
          .single();

        if (templateError) {
          console.error('Error saving template:', templateError);
          continue;
        }

        // Insert template lines
        const lines = template.lines.map((line, index) => ({
          template_id: templateData.id,
          line_number: index + 1,
          actor_role: line.actor_role,
          actor_first_name: line.actor_first_name,
          actor_last_name: line.actor_last_name,
          text: line.text,
        }));

        const { error: linesError } = await supabase
          .from('story_template_lines')
          .insert(lines);

        if (linesError) {
          console.error('Error saving template lines:', linesError);
          continue;
        }

        saved++;
      }

      setSavedCount(savedCount + saved);
      setGeneratedTemplates([]);
      
      toast({
        title: "Templates Saved",
        description: `Successfully saved ${saved} templates to database`,
      });
    } catch (error) {
      console.error('Error saving templates:', error);
      toast({
        title: "Save Failed",
        description: "Failed to save some templates",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleRemoveTemplate = (index: number) => {
    setGeneratedTemplates(generatedTemplates.filter((_, i) => i !== index));
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
      <div className="relative z-10 container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <Button
            variant="ghost"
            onClick={() => navigate('/story-templates')}
            className="mb-4 text-foreground hover:text-primary"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Templates
          </Button>
          <h1 className="font-western text-5xl text-foreground mb-2 [text-shadow:_2px_2px_4px_rgb(0_0_0_/_40%)]">
            Template Generator
          </h1>
          <p className="font-body text-muted-foreground">
            Use AI to automatically create hundreds of story templates
          </p>
          {savedCount > 0 && (
            <Badge variant="secondary" className="mt-2">
              <Check className="mr-1 h-3 w-3" />
              {savedCount} templates saved to database
            </Badge>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Controls */}
          <Card className="lg:col-span-1 bg-card/95 backdrop-blur border-border">
            <CardHeader>
              <CardTitle className="font-western">Generation Settings</CardTitle>
              <CardDescription>Configure template parameters</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Genre</Label>
                <Select value={genre} onValueChange={setGenre}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select genre" />
                  </SelectTrigger>
                  <SelectContent>
                    {GENRES.map((g) => (
                      <SelectItem key={g} value={g}>{g}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Theme</Label>
                <Select value={theme} onValueChange={setTheme}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select theme" />
                  </SelectTrigger>
                  <SelectContent>
                    {THEMES.map((t) => (
                      <SelectItem key={t} value={t}>{t}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Era</Label>
                <Select value={era} onValueChange={setEra}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {ERAS.map((e) => (
                      <SelectItem key={e} value={e}>{e}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Character Count (2-6)</Label>
                <Input
                  type="number"
                  min="2"
                  max="6"
                  value={characterCount}
                  onChange={(e) => setCharacterCount(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label>Batch Size (1-20)</Label>
                <Input
                  type="number"
                  min="1"
                  max="20"
                  value={batchSize}
                  onChange={(e) => setBatchSize(e.target.value)}
                />
                <p className="text-xs text-muted-foreground">
                  Generate multiple templates at once
                </p>
              </div>

              <div className="space-y-2 pt-2">
                <Button
                  onClick={handleGenerateSingle}
                  disabled={isGenerating || !genre || !theme}
                  className="w-full"
                  variant="outline"
                >
                  {isGenerating ? (
                    <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Generating...</>
                  ) : (
                    <><Wand2 className="mr-2 h-4 w-4" />Generate One</>
                  )}
                </Button>

                <Button
                  onClick={handleGenerateBatch}
                  disabled={isGenerating || !genre || !theme}
                  className="w-full bg-gradient-western"
                >
                  {isGenerating ? (
                    <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Generating Batch...</>
                  ) : (
                    <><Wand2 className="mr-2 h-4 w-4" />Generate Batch ({batchSize})</>
                  )}
                </Button>

                <Button
                  onClick={handleSaveAll}
                  disabled={isSaving || generatedTemplates.length === 0}
                  className="w-full"
                  variant="secondary"
                >
                  {isSaving ? (
                    <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Saving...</>
                  ) : (
                    <><Check className="mr-2 h-4 w-4" />Save All to Database ({generatedTemplates.length})</>
                  )}
                </Button>
              </div>

              <div className="pt-4 border-t border-border">
                <div className="flex items-start gap-2 text-xs text-muted-foreground">
                  <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                  <p>
                    AI generation uses Lovable AI credits. Large batches may take several minutes.
                    Rate limiting is built-in to prevent errors.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Generated Templates */}
          <Card className="lg:col-span-2 bg-card/95 backdrop-blur border-border">
            <CardHeader>
              <CardTitle className="font-western">Generated Templates</CardTitle>
              <CardDescription>
                {generatedTemplates.length === 0 
                  ? 'No templates generated yet'
                  : `${generatedTemplates.length} templates ready to save`}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2">
                {generatedTemplates.length === 0 ? (
                  <div className="text-center py-12 text-muted-foreground">
                    <Wand2 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Generate templates to see them here</p>
                  </div>
                ) : (
                  generatedTemplates.map((template, index) => (
                    <Card key={index} className="border-border/50">
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <CardTitle className="text-lg font-western">
                              {template.title}
                            </CardTitle>
                            <CardDescription className="mt-1">
                              {template.description}
                            </CardDescription>
                            <div className="flex gap-2 mt-2">
                              <Badge variant="secondary">{template.genre}</Badge>
                              <Badge variant="outline">{template.era}</Badge>
                              <Badge variant="outline">{template.lines.length} lines</Badge>
                            </div>
                          </div>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleRemoveTemplate(index)}
                            className="text-destructive"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2 text-sm">
                          {template.lines.slice(0, 3).map((line, lineIndex) => (
                            <div key={lineIndex} className="text-xs">
                              <span className="font-semibold text-primary">
                                {line.actor_first_name} {line.actor_last_name}:
                              </span>
                              <span className="ml-2 text-muted-foreground">{line.text}</span>
                            </div>
                          ))}
                          {template.lines.length > 3 && (
                            <p className="text-xs text-muted-foreground italic">
                              +{template.lines.length - 3} more lines...
                            </p>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default TemplateGenerator;