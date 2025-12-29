"use client";

import { useState, useEffect } from "react";
import { Sidebar, Header } from "@/components/layout";
import { CreatorStudio, TopicRadar } from "@/components/blocks";
import { useWorkflowStore } from "@/store/workflow";
import { checkHealth, getModels, getVoices, getPersonas } from "@/lib/api";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export default function Home() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [hotSearchOpen, setHotSearchOpen] = useState(false);
  const {
    mode,
    setAvailableModels,
    setAvailableVoices,
    setAvailablePersonas,
  } = useWorkflowStore();

  // Hydration fix
  useEffect(() => {
    setMounted(true);
  }, []);

  // Load config data on mount
  useEffect(() => {
    const loadConfig = async () => {
      try {
        // Check health
        const health = await checkHealth();
        if (!health.openrouter) {
          toast.warning("OpenRouter API 未配置，写作功能可能受限");
        }

        // Load models, voices, personas
        const [modelsRes, voicesRes, personasRes] = await Promise.all([
          getModels().catch(() => ({ models: [] })),
          getVoices().catch(() => ({ edge: [], volcengine: [] })),
          getPersonas().catch(() => ({ categories: [] })),
        ]);

        setAvailableModels(modelsRes.models);
        setAvailableVoices(voicesRes);
        setAvailablePersonas(personasRes.categories);
      } catch (error) {
        console.error("Failed to load config:", error);
        toast.error("后端连接失败，请确保服务已启动");
      }
    };

    loadConfig();
  }, [mode, setAvailableModels, setAvailableVoices, setAvailablePersonas]);

  if (!mounted) {
    return null;
  }

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <Sidebar 
        collapsed={sidebarCollapsed} 
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        onOpenHotSearch={() => setHotSearchOpen(true)}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-hidden">
          <CreatorStudio />
        </main>
      </div>

      {/* Hot Search Dialog */}
      <Dialog open={hotSearchOpen} onOpenChange={setHotSearchOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle>热点搜索</DialogTitle>
          </DialogHeader>
          <div className="flex-1 overflow-auto -mx-6 px-6">
            <TopicRadar onTopicSelect={() => setHotSearchOpen(false)} />
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
