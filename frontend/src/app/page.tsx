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
import { checkHealth, getModels, getVoices, getPersonas, getBgmList, exportNote } from "@/lib/api";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { Download, Loader2 } from "lucide-react";

export default function Home() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const {
    mode,
    currentStep,
    generatedContent,
    selectedTopic,
    selectedTitleIndex,
    imageResults,
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

  const handleExportNote = async () => {
    if (!generatedContent || !selectedTopic) return;
    
    setIsExporting(true);
    try {
      const title = generatedContent.titles[selectedTitleIndex] || generatedContent.titles[0];
      const imageUrls = imageResults
        .filter((r) => r?.url)
        .map((r) => r.url as string);
      
      const response = await exportNote({
        topic: selectedTopic.title,
        title,
        content: generatedContent.content,
        image_urls: imageUrls.length > 0 ? imageUrls : undefined,
        tags: ["小红书", selectedTopic.source || "自动生成"],
      });
      
      if (response.success) {
        toast.success("笔记已导出到 Obsidian");
      } else {
        toast.error("导出失败: " + (response.error || "未知错误"));
      }
    } catch (error) {
      toast.error("导出失败: " + (error as Error).message);
    } finally {
      setIsExporting(false);
    }
  };

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

            <Separator className="my-8" />

            {/* Export Section - Page Bottom */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.4 }}
              className="flex justify-center pb-8"
            >
              <Button
                size="lg"
                variant="outline"
                onClick={handleExportNote}
                disabled={isExporting || !generatedContent || !selectedTopic}
                className="gap-2 min-w-[200px]"
              >
                {isExporting ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Download className="w-5 h-5" />
                )}
                {isExporting ? "导出中..." : "导出笔记到 Obsidian"}
              </Button>
            </motion.div>

            {/* Footer Padding */}
            <div className="h-8" />
        </div>
      </main>
      </div>
    </div>
  );
}
