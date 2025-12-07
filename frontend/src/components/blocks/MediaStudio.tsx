"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Clapperboard,
  ChevronRight,
  Image as ImageIcon,
  Mic,
  Video,
  Download,
  RefreshCw,
  Loader2,
  Check,
  X,
  Clock,
  Play,
  Music,
  FileText,
  Copy,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Slider } from "@/components/ui/slider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { useWorkflowStore } from "@/store/workflow";
import {
  generateImages,
  generateAudio,
  generateSingleImage,
  generateSingleAudio,
  createVideo,
  getBgmList,
} from "@/lib/api";
import { toast } from "sonner";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8501";

// 处理 URL：如果是完整 URL 则直接返回，否则拼接 API_BASE
function resolveMediaUrl(url: string | null | undefined): string {
  if (!url) return "";
  if (url.startsWith("http://") || url.startsWith("https://")) {
    return url;
  }
  return `${API_BASE}${url}`;
}

function StatusBadge({ status }: { status: "pending" | "generating" | "success" | "error" }) {
  const config = {
    pending: { icon: Clock, label: "待生成", className: "status-pending" },
    generating: { icon: Loader2, label: "生成中", className: "status-generating" },
    success: { icon: Check, label: "完成", className: "status-success" },
    error: { icon: X, label: "失败", className: "status-error" },
  };
  const { icon: Icon, label, className } = config[status];
  
  return (
    <Badge variant="secondary" className={cn("gap-1 text-xs", className)}>
      <Icon className={cn("w-3 h-3", status === "generating" && "animate-spin")} />
      {label}
    </Badge>
  );
}

export function MediaStudio() {
  const {
    mode,
    generatedContent,
    selectedTopic,
    imageProvider,
    animeModel,
    ttsProvider,
    selectedVoice,
    imageResults,
    setImageResults,
    updateImageResult,
    audioResults,
    setAudioResults,
    updateAudioResult,
    videoPath,
    videoUrl,
    setVideoResult,
    selectedBgm,
    setSelectedBgm,
    bgmVolume,
    setBgmVolume,
    availableBgm,
    setAvailableBgm,
    isGeneratingImages,
    setIsGeneratingImages,
    isGeneratingAudio,
    setIsGeneratingAudio,
    isCreatingVideo,
    setIsCreatingVideo,
  } = useWorkflowStore();

  // Load BGM list
  useEffect(() => {
    if (mode === "video" && availableBgm.length === 0) {
      getBgmList()
        .then((data) => setAvailableBgm(data.bgm_list))
        .catch(() => {});
    }
  }, [mode, availableBgm.length, setAvailableBgm]);

  const scenes = mode === "video"
    ? generatedContent?.visual_scenes || []
    : mode === "wechat"
    ? generatedContent?.diagrams || []
    : generatedContent?.image_designs || [];

  const getSceneStatus = (result: { path: string | null; error: string | null } | null, isGenerating: boolean) => {
    if (isGenerating) return "generating";
    if (result?.path) return "success";
    if (result?.error) return "error";
    return "pending";
  };

  // Generate all images
  const handleGenerateImages = async () => {
    if (!scenes.length) return;
    
    setIsGeneratingImages(true);
    try {
      const sceneInputs = scenes.map((s) => ({
        prompt: (s as { prompt: string }).prompt,
        sentiment: mode === "video" ? (s as { sentiment?: string }).sentiment : undefined,
      }));

      const response = await generateImages({
        scenes: sceneInputs,
        provider: imageProvider,
        anime_model: animeModel,
        topic: selectedTopic?.title,
        mode: mode,  // 图文模式主图用 Gemini
      });

      setImageResults(response.results);
      toast.success(`图片生成完成: ${response.success_count}/${response.total}`);
    } catch (error) {
      toast.error("图片生成失败: " + (error as Error).message);
    } finally {
      setIsGeneratingImages(false);
    }
  };

  // Generate all audio (video mode only)
  const handleGenerateAudio = async () => {
    if (!scenes.length || mode !== "video") return;

    setIsGeneratingAudio(true);
    try {
      const sceneInputs = scenes.map((s) => ({
        narration: (s as { narration: string }).narration || "",
      }));

      const response = await generateAudio({
        scenes: sceneInputs,
        provider: ttsProvider,
        voice: selectedVoice,
        topic: selectedTopic?.title,
      });

      setAudioResults(response.results);
      toast.success(`音频生成完成: ${response.success_count}/${response.total}`);
    } catch (error) {
      toast.error("音频生成失败: " + (error as Error).message);
    } finally {
      setIsGeneratingAudio(false);
    }
  };

  // Retry single image
  const handleRetryImage = async (index: number) => {
    const scene = scenes[index];
    if (!scene) return;

    updateImageResult(index, { index, path: null, url: null, error: null });
    
    try {
      const result = await generateSingleImage({
        scene: {
          prompt: (scene as { prompt: string }).prompt,
          sentiment: mode === "video" ? (scene as { sentiment?: string }).sentiment : undefined,
        },
        index,
        provider: imageProvider,
        anime_model: animeModel,
        topic: selectedTopic?.title,
      });

      updateImageResult(index, result);
      if (result.path) {
        toast.success(`图片 ${index + 1} 重新生成成功`);
      } else {
        toast.error(`图片 ${index + 1} 重试失败`);
      }
    } catch (error) {
      updateImageResult(index, { index, path: null, url: null, error: (error as Error).message });
    }
  };

  // Create video
  const handleCreateVideo = async () => {
    if (mode !== "video") return;

    const imagePaths = imageResults.map((r) => r?.path).filter(Boolean) as string[];
    const audioPaths = audioResults.map((r) => r?.path).filter(Boolean) as string[];

    if (imagePaths.length !== scenes.length || audioPaths.length !== scenes.length) {
      toast.error("请先完成所有图片和音频的生成");
      return;
    }

    setIsCreatingVideo(true);
    try {
      const response = await createVideo({
        image_paths: imagePaths,
        audio_paths: audioPaths,
        scenes: scenes.map((s) => ({ narration: (s as { narration: string }).narration || "" })),
        bgm_path: selectedBgm || undefined,
        bgm_volume: bgmVolume,
        topic: selectedTopic?.title,
      });

      if (response.video_path) {
        setVideoResult(response.video_path, response.video_url, response.srt_path);
        toast.success("视频合成完成!");
      } else {
        toast.error(response.error || "视频合成失败");
      }
    } catch (error) {
      toast.error("视频合成失败: " + (error as Error).message);
    } finally {
      setIsCreatingVideo(false);
    }
  };

  const imageSuccessCount = imageResults.filter((r) => r?.path).length;
  const audioSuccessCount = audioResults.filter((r) => r?.path).length;
  const allImagesReady = imageSuccessCount === scenes.length;
  const allAudioReady = mode !== "video" || audioSuccessCount === scenes.length;

  // Disabled state
  if (!generatedContent) {
    return (
      <section className="space-y-6 opacity-50">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-muted text-muted-foreground">
            <FileText className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-lg font-semibold">
              生图提示词预览
            </h2>
            <p className="text-sm text-muted-foreground">
              查看和复制各场景的中英文生图提示词
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 p-4 rounded-lg bg-secondary/50 text-muted-foreground">
          <ChevronRight className="w-4 h-4" />
          <span className="text-sm">请先完成前面的步骤</span>
        </div>
      </section>
    );
  }

  return (
    <section className="space-y-6">
      {/* Section Header */}
      <div className="flex items-center gap-3">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary/10 text-primary">
          <FileText className="w-4 h-4" />
        </div>
        <div>
          <h2 className="text-lg font-semibold">
            生图提示词预览
          </h2>
          <p className="text-sm text-muted-foreground">
            查看和复制各场景的中英文生图提示词
          </p>
        </div>
      </div>

      {/* Prompt Preview Grid - 生图功能已隐藏 */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-foreground">生图提示词列表</h3>
          <Badge variant="secondary" className="text-xs">
            {scenes.length} 个场景
          </Badge>
        </div>
        <ScrollArea className="h-[600px]">
          <div className="space-y-3 pr-4">
            {scenes.map((scene, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.03 }}
                className="rounded-lg border border-border bg-card p-4 space-y-3"
              >
                {/* Scene Header */}
                <div className="flex items-center justify-between">
                  <Badge variant="outline">场景 {i + 1}</Badge>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 gap-1 text-xs"
                    onClick={() => {
                      const fullText = `场景${i+1}\n\n【画面描述】\n${
                        mode === "video"
                          ? (scene as { description: string }).description
                          : mode === "wechat"
                          ? (scene as any).title || (scene as { description: string }).description
                          : (scene as { description: string }).description
                      }\n\n【生图提示词】\n${(scene as { prompt: string }).prompt}`;
                      navigator.clipboard.writeText(fullText);
                      toast.success("场景完整信息已复制");
                    }}
                  >
                    <Copy className="w-3 h-3" />
                    复制全部
                  </Button>
                </div>

                {/* 视频模式：口播词 */}
                {mode === "video" && (
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-muted-foreground">
                      口播词
                    </label>
                    <p className="text-sm text-foreground leading-relaxed">
                      {(scene as { narration: string }).narration}
                    </p>
                  </div>
                )}

                {/* 中文描述 */}
                <div className="space-y-1">
                  <label className="text-xs font-medium text-muted-foreground">
                    {mode === "wechat" ? "技术描述" : "画面描述"}
                  </label>
                  <p className="text-sm text-foreground leading-relaxed">
                    {mode === "video"
                      ? (scene as { description: string }).description
                      : mode === "wechat"
                      ? (scene as any).title || (scene as { description: string }).description
                      : (scene as { description: string }).description}
                  </p>
                </div>

                {/* 英文 Prompt */}
                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-medium text-muted-foreground">
                      生图提示词（英文）
                    </label>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 gap-1 text-xs"
                      onClick={() => {
                        navigator.clipboard.writeText((scene as { prompt: string }).prompt);
                        toast.success("Prompt 已复制");
                      }}
                    >
                      <Copy className="w-3 h-3" />
                      复制
                    </Button>
                  </div>
                  <pre className="text-xs bg-secondary/50 p-3 rounded whitespace-pre-wrap font-mono leading-relaxed">
{(scene as { prompt: string }).prompt}
                  </pre>
                </div>
              </motion.div>
            ))}
          </div>
        </ScrollArea>
      </div>
    </section>
  );
}

