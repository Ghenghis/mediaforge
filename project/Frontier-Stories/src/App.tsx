import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import VoiceLibrary from "./pages/VoiceLibrary";
import StoryCreation from "./pages/StoryCreation";
import StoryLibrary from "./pages/StoryLibrary";
import StoryTemplates from "./pages/StoryTemplates";
import TemplateGenerator from "./pages/TemplateGenerator";
import PortraitGallery from "./pages/PortraitGallery";
import PortraitAnalytics from "./pages/PortraitAnalytics";
import StoryboardViewer from "./pages/StoryboardViewer";
import Settings from "./pages/Settings";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Index />} />
          <Route path="/voice-library" element={<VoiceLibrary />} />
          <Route path="/story-creation" element={<StoryCreation />} />
          <Route path="/story-library" element={<StoryLibrary />} />
          <Route path="/story-templates" element={<StoryTemplates />} />
          <Route path="/template-generator" element={<TemplateGenerator />} />
          <Route path="/portrait-gallery" element={<PortraitGallery />} />
          <Route path="/portrait-analytics" element={<PortraitAnalytics />} />
          <Route path="/storyboard" element={<StoryboardViewer />} />
          <Route path="/settings" element={<Settings />} />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
