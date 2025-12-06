import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, BookOpen, Heart, Mountain, Users, Wand2, Loader2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/hooks/use-toast";
import woodTexture from "@/assets/wood-texture.jpg";
import parchmentTexture from "@/assets/parchment-texture.jpg";

interface StoryTemplate {
  id: string;
  title: string;
  description: string;
  genre: string;
  era: string;
  icon: React.ReactNode;
  lines: Array<{
    actorRole: string;
    text: string;
    actorFirstName: string;
    actorLastName: string;
  }>;
}

interface DbTemplate {
  id: string;
  title: string;
  description: string;
  genre: string;
  era: string;
  icon_name: string;
}

interface DbTemplateLine {
  line_number: number;
  actor_role: string;
  actor_first_name: string;
  actor_last_name: string;
  text: string;
}

const getIconComponent = (iconName: string) => {
  switch (iconName) {
    case 'Mountain': return <Mountain className="h-8 w-8" />;
    case 'Users': return <Users className="h-8 w-8" />;
    case 'BookOpen': return <BookOpen className="h-8 w-8" />;
    case 'Heart':
    default: return <Heart className="h-8 w-8" />;
  }
};

const StoryTemplates = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [templates, setTemplates] = useState<StoryTemplate[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    setIsLoading(true);
    try {
      // Load templates from database
      const { data: dbTemplates, error: templatesError } = await supabase
        .from('story_templates')
        .select('*')
        .eq('is_active', true)
        .order('created_at', { ascending: false });

      if (templatesError) throw templatesError;

      if (!dbTemplates || dbTemplates.length === 0) {
        // No templates in DB, show fallback templates
        setTemplates(getFallbackTemplates());
        setIsLoading(false);
        return;
      }

      // Load template lines
      const { data: dbLines, error: linesError } = await supabase
        .from('story_template_lines')
        .select('*')
        .in('template_id', dbTemplates.map(t => t.id))
        .order('line_number', { ascending: true });

      if (linesError) throw linesError;

      // Combine templates with their lines
      const combinedTemplates: StoryTemplate[] = dbTemplates.map((template: DbTemplate) => {
        const templateLines = (dbLines || []).filter((line: any) => line.template_id === template.id);
        
        return {
          id: template.id,
          title: template.title,
          description: template.description || '',
          genre: template.genre,
          era: template.era,
          icon: getIconComponent(template.icon_name),
          lines: templateLines.map((line: DbTemplateLine) => ({
            actorRole: line.actor_role,
            actorFirstName: line.actor_first_name,
            actorLastName: line.actor_last_name,
            text: line.text,
          })),
        };
      });

      setTemplates(combinedTemplates);
    } catch (error) {
      console.error('Error loading templates:', error);
      toast({
        title: "Error",
        description: "Failed to load templates. Showing fallback templates.",
        variant: "destructive",
      });
      setTemplates(getFallbackTemplates());
    } finally {
      setIsLoading(false);
    }
  };

  const getFallbackTemplates = (): StoryTemplate[] => [
    {
      id: "apache-romance",
      title: "Apache Romance",
      description: "A forbidden love story between a settler and Apache warrior in the Old West",
      genre: "Historical Romance",
      era: "1870s",
      icon: <Heart className="h-8 w-8" />,
      lines: [
        {
          actorRole: "Narrator",
          actorFirstName: "Samuel",
          actorLastName: "Rivers",
          text: "In the shadow of the Arizona mountains, where two worlds collided, an unexpected love was about to bloom."
        },
        {
          actorRole: "Apache Warrior",
          actorFirstName: "Running",
          actorLastName: "Bear",
          text: "You should not be here. These lands are dangerous for your kind."
        },
        {
          actorRole: "Settler Woman",
          actorFirstName: "Sarah",
          actorLastName: "McCoy",
          text: "I know the risks, but something drew me here. Perhaps it was fate."
        },
        {
          actorRole: "Apache Warrior",
          actorFirstName: "Running",
          actorLastName: "Bear",
          text: "Fate is a cruel mistress. Our peoples are at war."
        },
        {
          actorRole: "Settler Woman",
          actorFirstName: "Sarah",
          actorLastName: "McCoy",
          text: "Then let us be the bridge between them. Love knows no boundaries."
        }
      ]
    },
    {
      id: "lakota-arranged-marriage",
      title: "Lakota Arranged Marriage",
      description: "A tale of arranged marriage turning into true love in a Lakota community",
      genre: "Historical Romance",
      era: "1870s",
      icon: <Users className="h-8 w-8" />,
      lines: [
        {
          actorRole: "Narrator",
          actorFirstName: "Samuel",
          actorLastName: "Rivers",
          text: "Among the Lakota people, tradition and duty often guided the heart."
        },
        {
          actorRole: "Lakota Chief",
          actorFirstName: "Black",
          actorLastName: "Hawk",
          text: "This union will strengthen our tribe. You will marry at the next full moon."
        },
        {
          actorRole: "Young Warrior",
          actorFirstName: "Swift",
          actorLastName: "Eagle",
          text: "I will honor my duty to the tribe, though my heart is uncertain."
        },
        {
          actorRole: "Tribal Maiden",
          actorFirstName: "Morning",
          actorLastName: "Star",
          text: "We are strangers bound by tradition. Perhaps in time, we will find something more."
        },
        {
          actorRole: "Narrator",
          actorFirstName: "Samuel",
          actorLastName: "Rivers",
          text: "What began as duty would soon blossom into a love neither expected."
        }
      ]
    },
    {
      id: "frontier-star-crossed",
      title: "Frontier Star-Crossed Lovers",
      description: "Romeo and Juliet set against the backdrop of warring frontier families",
      genre: "Historical Romance",
      era: "1870s",
      icon: <Mountain className="h-8 w-8" />,
      lines: [
        {
          actorRole: "Narrator",
          actorFirstName: "Samuel",
          actorLastName: "Rivers",
          text: "Two families, both alike in dignity, in fair frontier where we lay our scene."
        },
        {
          actorRole: "Rancher's Son",
          actorFirstName: "Jake",
          actorLastName: "Morrison",
          text: "Our fathers' feud means nothing to me. You are all I see."
        },
        {
          actorRole: "Settler's Daughter",
          actorFirstName: "Sarah",
          actorLastName: "McCoy",
          text: "They will never accept us together. Our love is forbidden."
        },
        {
          actorRole: "Rancher's Son",
          actorFirstName: "Jake",
          actorLastName: "Morrison",
          text: "Then we shall forge our own path, away from this blood feud."
        },
        {
          actorRole: "Narrator",
          actorFirstName: "Samuel",
          actorLastName: "Rivers",
          text: "In the untamed West, love would prove stronger than hate."
        }
      ]
    },
    {
      id: "cheyenne-tribal-conflict",
      title: "Cheyenne Tribal Conflict",
      description: "Love blooms amidst tensions between Cheyenne bands",
      genre: "Historical Romance",
      era: "1870s",
      icon: <Heart className="h-8 w-8" />,
      lines: [
        {
          actorRole: "Narrator",
          actorFirstName: "Samuel",
          actorLastName: "Rivers",
          text: "The Northern and Southern Cheyenne had long been divided by distance and different ways."
        },
        {
          actorRole: "Northern Warrior",
          actorFirstName: "Gray",
          actorLastName: "Wolf",
          text: "I come seeking peace between our peoples, and perhaps something more."
        },
        {
          actorRole: "Southern Maiden",
          actorFirstName: "Gentle",
          actorLastName: "Rain",
          text: "Your words are brave, but our elders will not easily forget old grievances."
        },
        {
          actorRole: "Northern Warrior",
          actorFirstName: "Gray",
          actorLastName: "Wolf",
          text: "Then let our union be the first step toward healing."
        },
        {
          actorRole: "Narrator",
          actorFirstName: "Samuel",
          actorLastName: "Rivers",
          text: "Love would become the bridge that reunited a divided people."
        }
      ]
    },
    {
      id: "pioneer-native-alliance",
      title: "Pioneer and Native Alliance",
      description: "Mutual respect and love develop between a pioneer doctor and a Native healer",
      genre: "Historical Romance",
      era: "1870s",
      icon: <Users className="h-8 w-8" />,
      lines: [
        {
          actorRole: "Narrator",
          actorFirstName: "Samuel",
          actorLastName: "Rivers",
          text: "In a time of conflict, two healers found common ground in their desire to save lives."
        },
        {
          actorRole: "Pioneer Doctor",
          actorFirstName: "Elizabeth",
          actorLastName: "Wells",
          text: "I have much to learn from your healing ways. Will you teach me?"
        },
        {
          actorRole: "Native Healer",
          actorFirstName: "Wise",
          actorLastName: "Owl",
          text: "Your medicine is different from ours, yet your heart seeks the same goal. I will teach you."
        },
        {
          actorRole: "Pioneer Doctor",
          actorFirstName: "Elizabeth",
          actorLastName: "Wells",
          text: "Together, we could help so many. Both your people and mine."
        },
        {
          actorRole: "Narrator",
          actorFirstName: "Samuel",
          actorLastName: "Rivers",
          text: "From respect grew friendship, and from friendship bloomed a love that transcended all boundaries."
        }
      ]
    },
    {
      id: "comanche-rescue",
      title: "Comanche Rescue Romance",
      description: "A captivity tale that transforms into an unexpected love story",
      genre: "Historical Romance",
      era: "1870s",
      icon: <Mountain className="h-8 w-8" />,
      lines: [
        {
          actorRole: "Narrator",
          actorFirstName: "Samuel",
          actorLastName: "Rivers",
          text: "Captured during a raid, she expected nothing but fear. Instead, she found understanding."
        },
        {
          actorRole: "Captive Woman",
          actorFirstName: "Mary",
          actorLastName: "Anderson",
          text: "Why spare me? What do you want from me?"
        },
        {
          actorRole: "Comanche Warrior",
          actorFirstName: "Thunder",
          actorLastName: "Cloud",
          text: "I saw courage in your eyes, not hatred. You are different from the others."
        },
        {
          actorRole: "Captive Woman",
          actorFirstName: "Mary",
          actorLastName: "Anderson",
          text: "Your people killed my family. How can there be anything but hate between us?"
        },
        {
          actorRole: "Comanche Warrior",
          actorFirstName: "Thunder",
          actorLastName: "Cloud",
          text: "And your people took our lands. Yet here we stand, two souls seeking peace. Perhaps together we can find it."
        }
      ]
    }
  ];

  const handleUseTemplate = async (template: StoryTemplate) => {
    // Increment use count
    try {
      const { data: currentTemplate } = await supabase
        .from('story_templates')
        .select('use_count')
        .eq('id', template.id)
        .single();

      if (currentTemplate) {
        await supabase
          .from('story_templates')
          .update({ use_count: (currentTemplate.use_count || 0) + 1 })
          .eq('id', template.id);
      }
    } catch (error) {
      console.error('Error updating use count:', error);
    }

    // Encode template data to pass to story creation page
    const templateData = encodeURIComponent(JSON.stringify(template));
    navigate(`/story-creation?template=${templateData}`);
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
          <div className="flex items-center justify-between mb-4">
            <Button
              variant="ghost"
              onClick={() => navigate('/')}
              className="text-foreground hover:text-primary"
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Home
            </Button>
            <Button
              onClick={() => navigate('/template-generator')}
              className="bg-gradient-western"
            >
              <Wand2 className="mr-2 h-4 w-4" />
              AI Template Generator
            </Button>
          </div>
          <div>
            <h1 className="font-western text-5xl text-foreground mb-2 [text-shadow:_2px_2px_4px_rgb(0_0_0_/_40%)]">
              Story Templates
            </h1>
            <p className="font-body text-muted-foreground">
              Start your story with a pre-made template and customize it to your liking
            </p>
          </div>
        </div>

        {/* Templates Grid */}
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="h-12 w-12 animate-spin text-primary" />
            <p className="ml-4 text-xl font-body text-foreground">Loading templates...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {templates.map((template) => (
            <Card
              key={template.id}
              className="bg-card/95 backdrop-blur border-border hover:shadow-lifted transition-all duration-300 hover:scale-105"
            >
              <CardHeader>
                <div className="flex items-start gap-4">
                  <div className="p-3 bg-primary/10 rounded-lg text-primary">
                    {template.icon}
                  </div>
                  <div className="flex-1">
                    <CardTitle className="font-western text-xl mb-2">
                      {template.title}
                    </CardTitle>
                    <div className="flex gap-2 flex-wrap">
                      <Badge variant="secondary">{template.genre}</Badge>
                      <Badge variant="outline">{template.era}</Badge>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <CardDescription className="text-sm">
                  {template.description}
                </CardDescription>
                
                <div className="text-xs text-muted-foreground">
                  <p className="font-semibold mb-1">Includes:</p>
                  <ul className="list-disc list-inside space-y-1">
                    <li>{template.lines.length} pre-written dialogue lines</li>
                    <li>{new Set(template.lines.map(l => l.actorRole)).size} character roles</li>
                    <li>Suggested character names</li>
                  </ul>
                </div>

                <Button
                  onClick={() => handleUseTemplate(template)}
                  className="w-full bg-gradient-western"
                >
                  <BookOpen className="mr-2 h-4 w-4" />
                  Use This Template
                </Button>
              </CardContent>
            </Card>
            ))}
          </div>
        )}

        {/* Info Card */}
        <Card className="mt-8 bg-card/95 backdrop-blur border-border">
          <CardContent className="py-6">
            <div className="flex items-start gap-4">
              <BookOpen className="h-6 w-6 text-primary flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-western text-lg mb-2">How to Use Templates</h3>
                <p className="text-sm text-muted-foreground">
                  Select a template to start with pre-written dialogue and character suggestions. 
                  You can customize everything - edit the dialogue, change character names, add or remove lines, 
                  and adjust audio settings. Templates are just a starting point for your creative vision.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default StoryTemplates;
