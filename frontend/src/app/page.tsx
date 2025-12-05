"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { Sidebar, Header } from "@/components/layout";
import {
  TopicRadar,
  PersonaConfig,
  ContentPreview,
  MediaStudio,
} from "@/components/blocks";
import { useWorkflowStore } from "@/store/workflow";
import { checkHealth, getModels, getVoices, getPersonas, getBgmList } from "@/lib/api";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

export default function Home() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mounted, setMounted] = useState(false);
  const {
    mode,
    currentStep,
    setAvailableModels,
    setAvailableVoices,
    setAvailablePersonas,
    setAvailableBgm,
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

        // Load BGM list if in video mode
        if (mode === "video") {
          const bgmRes = await getBgmList().catch(() => ({ bgm_list: [] }));
          setAvailableBgm(bgmRes.bgm_list);
        }
      } catch (error) {
        console.error("Failed to load config:", error);
        toast.error("后端连接失败，请确保服务已启动");
      }
    };

    loadConfig();
  }, [mode, setAvailableModels, setAvailableVoices, setAvailablePersonas, setAvailableBgm]);

  if (!mounted) {
    return null;
  }

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <Sidebar collapsed={sidebarCollapsed} onToggle={() => setSidebarCollapsed(!sidebarCollapsed)} />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />

        <main className="flex-1 overflow-auto">
          <div className="max-w-4xl mx-auto px-6 py-8 space-y-8">
            {/* Step 1: Topic Radar */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              <TopicRadar />
            </motion.div>

            <Separator className="my-8" />

            {/* Step 2: Persona Config */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.1 }}
            >
              <PersonaConfig />
            </motion.div>

            <Separator className="my-8" />

            {/* Step 3: Content Preview */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.2 }}
            >
              <ContentPreview />
            </motion.div>

            <Separator className="my-8" />

            {/* Step 4: Media Studio */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.3 }}
            >
              <MediaStudio />
            </motion.div>

            {/* Footer Padding */}
            <div className="h-16" />
        </div>
      </main>
      </div>
    </div>
  );
}
