import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowLeft, TrendingUp, Users, Image, Calendar } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface AnalyticsData {
  totalPortraits: number;
  totalActors: number;
  bwCount: number;
  colorCount: number;
  avgAge: number;
  avgWeathering: number;
  avgDetailLevel: number;
  avgClothingStyle: number;
  mostGeneratedActor: { name: string; count: number } | null;
  recentGenerations: Array<{
    date: string;
    count: number;
  }>;
}

const PortraitAnalytics = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [analytics, setAnalytics] = useState<AnalyticsData>({
    totalPortraits: 0,
    totalActors: 0,
    bwCount: 0,
    colorCount: 0,
    avgAge: 0,
    avgWeathering: 0,
    avgDetailLevel: 0,
    avgClothingStyle: 0,
    mostGeneratedActor: null,
    recentGenerations: [],
  });

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);

      // Get total portraits
      const { data: portraits, error: portraitsError } = await supabase
        .from('actor_portrait_history')
        .select('*');

      if (portraitsError) throw portraitsError;

      // Get actors
      const { data: actors, error: actorsError } = await supabase
        .from('actors')
        .select('id, full_name');

      if (actorsError) throw actorsError;

      // Calculate stats
      const totalPortraits = portraits?.length || 0;
      const totalActors = actors?.length || 0;
      const bwCount = portraits?.filter(p => p.color_mode === 'bw').length || 0;
      const colorCount = portraits?.filter(p => p.color_mode === 'color').length || 0;

      // Calculate averages from generation params
      const paramsWithData = portraits?.filter(p => {
        const params = p.generation_params as any;
        return params?.age;
      }) || [];
      const avgAge = paramsWithData.length > 0
        ? paramsWithData.reduce((sum, p) => {
            const params = p.generation_params as any;
            return sum + (params?.age || 0);
          }, 0) / paramsWithData.length
        : 0;
      const avgWeathering = paramsWithData.length > 0
        ? paramsWithData.reduce((sum, p) => {
            const params = p.generation_params as any;
            return sum + (params?.weathering || 0);
          }, 0) / paramsWithData.length
        : 0;
      const avgDetailLevel = paramsWithData.length > 0
        ? paramsWithData.reduce((sum, p) => {
            const params = p.generation_params as any;
            return sum + (params?.detailLevel || 0);
          }, 0) / paramsWithData.length
        : 0;
      const avgClothingStyle = paramsWithData.length > 0
        ? paramsWithData.reduce((sum, p) => {
            const params = p.generation_params as any;
            return sum + (params?.clothingStyle || 0);
          }, 0) / paramsWithData.length
        : 0;

      // Find most generated actor
      const actorCounts: Record<string, number> = {};
      portraits?.forEach(p => {
        actorCounts[p.actor_id] = (actorCounts[p.actor_id] || 0) + 1;
      });
      const topActorId = Object.entries(actorCounts).sort((a, b) => b[1] - a[1])[0];
      const topActor = topActorId ? actors?.find(a => a.id === topActorId[0]) : null;
      const mostGeneratedActor = topActor ? { name: topActor.full_name || 'Unknown', count: topActorId[1] } : null;

      // Generate timeline data (last 7 days)
      const now = new Date();
      const recentGenerations = [];
      for (let i = 6; i >= 0; i--) {
        const date = new Date(now);
        date.setDate(date.getDate() - i);
        const dateStr = date.toISOString().split('T')[0];
        const count = portraits?.filter(p => {
          const pDate = new Date(p.created_at).toISOString().split('T')[0];
          return pDate === dateStr;
        }).length || 0;
        recentGenerations.push({
          date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
          count,
        });
      }

      setAnalytics({
        totalPortraits,
        totalActors,
        bwCount,
        colorCount,
        avgAge: Math.round(avgAge),
        avgWeathering: Math.round(avgWeathering),
        avgDetailLevel: Math.round(avgDetailLevel),
        avgClothingStyle: Math.round(avgClothingStyle),
        mostGeneratedActor,
        recentGenerations,
      });

    } catch (error: any) {
      toast({
        title: "Error",
        description: "Failed to load analytics",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="bg-card border-b border-border sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/portrait-gallery')}
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Gallery
            </Button>
            <h1 className="font-western text-2xl text-foreground">Portrait Analytics</h1>
          </div>
        </div>
      </div>

      {/* Analytics Content */}
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Total Portraits */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Portraits</CardTitle>
              <Image className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{analytics.totalPortraits}</div>
              <p className="text-xs text-muted-foreground">
                {analytics.bwCount} B&W, {analytics.colorCount} Color
              </p>
            </CardContent>
          </Card>

          {/* Total Actors */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Characters</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{analytics.totalActors}</div>
              <p className="text-xs text-muted-foreground">
                Unique characters created
              </p>
            </CardContent>
          </Card>

          {/* Most Generated */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Most Generated</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {analytics.mostGeneratedActor?.count || 0}x
              </div>
              <p className="text-xs text-muted-foreground truncate">
                {analytics.mostGeneratedActor?.name || 'N/A'}
              </p>
            </CardContent>
          </Card>

          {/* Avg Age */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Age Setting</CardTitle>
              <Calendar className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{analytics.avgAge} yrs</div>
              <p className="text-xs text-muted-foreground">
                Average customization
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Customization Averages */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Average Customization Settings</CardTitle>
            <CardDescription>
              Average values across all custom portrait generations
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div>
                <div className="text-sm font-medium text-muted-foreground mb-2">Age</div>
                <div className="text-3xl font-bold">{analytics.avgAge}</div>
                <div className="text-xs text-muted-foreground">years old</div>
              </div>
              <div>
                <div className="text-sm font-medium text-muted-foreground mb-2">Weathering</div>
                <div className="text-3xl font-bold">{analytics.avgWeathering}%</div>
                <div className="text-xs text-muted-foreground">photo aging</div>
              </div>
              <div>
                <div className="text-sm font-medium text-muted-foreground mb-2">Detail Level</div>
                <div className="text-3xl font-bold">{analytics.avgDetailLevel}%</div>
                <div className="text-xs text-muted-foreground">sharpness</div>
              </div>
              <div>
                <div className="text-sm font-medium text-muted-foreground mb-2">Clothing Formality</div>
                <div className="text-3xl font-bold">{analytics.avgClothingStyle}%</div>
                <div className="text-xs text-muted-foreground">formality level</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Generation Timeline */}
        <Card>
          <CardHeader>
            <CardTitle>Generation Timeline (Last 7 Days)</CardTitle>
            <CardDescription>
              Daily portrait generation activity
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {analytics.recentGenerations.map((day, index) => (
                <div key={index} className="flex items-center gap-4">
                  <div className="w-20 text-sm text-muted-foreground">{day.date}</div>
                  <div className="flex-1 bg-muted rounded-full h-8 relative overflow-hidden">
                    <div 
                      className="bg-gradient-western h-full flex items-center justify-end pr-2 text-xs font-medium text-white"
                      style={{ 
                        width: `${Math.max((day.count / Math.max(...analytics.recentGenerations.map(d => d.count))) * 100, 5)}%` 
                      }}
                    >
                      {day.count > 0 && day.count}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default PortraitAnalytics;
