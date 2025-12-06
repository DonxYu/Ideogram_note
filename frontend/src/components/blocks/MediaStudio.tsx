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
            <Clapperboard className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-lg font-semibold">
              {mode === "video" ? "视频工作室" : "配图生成"}
            </h2>
            <p className="text-sm text-muted-foreground">
              生成素材并合成最终内容
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
          <Clapperboard className="w-4 h-4" />
        </div>
        <div>
          <h2 className="text-lg font-semibold">
            {mode === "video" ? "视频工作室" : "配图生成 & 导出"}
          </h2>
          <p className="text-sm text-muted-foreground">
            {mode === "video"
              ? "生成配图和音频，自动合成视频"
              : "生成配图，导出完整内容"}
          </p>
        </div>
      </div>

      {/* Progress Overview */}
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="p-4 rounded-lg bg-card border border-border">
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
            <ImageIcon className="w-4 h-4" />
            图片进度
          </div>
          <div className="flex items-center justify-between">
            <span className="text-2xl font-semibold">
              {imageSuccessCount}/{scenes.length}
            </span>
            {allImagesReady ? (
              <Badge className="status-success">完成</Badge>
            ) : isGeneratingImages ? (
              <Badge className="status-generating gap-1">
                <Loader2 className="w-3 h-3 animate-spin" />
                生成中
              </Badge>
            ) : (
              <Badge className="status-pending">待生成</Badge>
            )}
          </div>
        </div>

        {mode === "video" && (
          <div className="p-4 rounded-lg bg-card border border-border">
            <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
              <Mic className="w-4 h-4" />
              音频进度
            </div>
            <div className="flex items-center justify-between">
              <span className="text-2xl font-semibold">
                {audioSuccessCount}/{scenes.length}
              </span>
              {allAudioReady ? (
                <Badge className="status-success">完成</Badge>
              ) : isGeneratingAudio ? (
                <Badge className="status-generating gap-1">
                  <Loader2 className="w-3 h-3 animate-spin" />
                  生成中
                </Badge>
              ) : (
                <Badge className="status-pending">待生成</Badge>
              )}
            </div>
          </div>
        )}

        {mode === "video" && (
          <div className="p-4 rounded-lg bg-card border border-border">
            <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
              <Video className="w-4 h-4" />
              视频状态
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">
                {videoPath ? "已生成" : "待合成"}
              </span>
              {videoPath ? (
                <Badge className="status-success">完成</Badge>
              ) : isCreatingVideo ? (
                <Badge className="status-generating gap-1">
                  <Loader2 className="w-3 h-3 animate-spin" />
                  合成中
                </Badge>
              ) : (
                <Badge className="status-pending">待合成</Badge>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex flex-wrap gap-3">
        <Button
          onClick={handleGenerateImages}
          disabled={isGeneratingImages || allImagesReady}
          className="gap-2"
        >
          {isGeneratingImages ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <ImageIcon className="w-4 h-4" />
          )}
          {allImagesReady ? "图片已完成" : "生成所有图片"}
        </Button>

        {mode === "video" && (
          <>
            <Button
              onClick={handleGenerateAudio}
              disabled={isGeneratingAudio || allAudioReady}
              variant="secondary"
              className="gap-2"
            >
              {isGeneratingAudio ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Mic className="w-4 h-4" />
              )}
              {allAudioReady ? "音频已完成" : "生成所有音频"}
            </Button>

            <Button
              onClick={handleCreateVideo}
              disabled={!allImagesReady || !allAudioReady || isCreatingVideo}
              variant={videoPath ? "secondary" : "default"}
              className="gap-2"
            >
              {isCreatingVideo ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Video className="w-4 h-4" />
              )}
              {videoPath ? "重新合成" : "合成视频"}
            </Button>
          </>
        )}
      </div>

      {/* BGM Selection (Video Mode) */}
      {mode === "video" && (
        <div className="p-4 rounded-lg bg-secondary/30 space-y-4">
          <div className="flex items-center gap-2 text-sm font-medium">
            <Music className="w-4 h-4" />
            背景音乐
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <Select value={selectedBgm || ""} onValueChange={(v) => setSelectedBgm(v || null)}>
              <SelectTrigger className="h-10 bg-background">
                <SelectValue placeholder="选择 BGM（可选）" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">无 BGM</SelectItem>
                {availableBgm.map((bgm) => (
                  <SelectItem key={bgm.path} value={bgm.path}>
                    {bgm.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <div className="flex items-center gap-4">
              <span className="text-sm text-muted-foreground shrink-0">音量</span>
              <Slider
                value={[bgmVolume]}
                onValueChange={([v]) => setBgmVolume(v)}
                min={0.05}
                max={0.3}
                step={0.01}
                className="flex-1"
              />
              <span className="text-sm text-muted-foreground w-12">
                {Math.round(bgmVolume * 100)}%
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Media Preview Grid */}
      <div className="space-y-4">
        <h3 className="text-sm font-medium text-foreground">素材预览</h3>
        <ScrollArea className="h-[400px]">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 pr-4">
            {scenes.map((scene, i) => {
              const imageResult = imageResults[i];
              const audioResult = audioResults[i];
              const imageStatus = getSceneStatus(imageResult, isGeneratingImages);
              const audioStatus = mode === "video" ? getSceneStatus(audioResult, isGeneratingAudio) : null;

              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: i * 0.03 }}
                  className="rounded-lg border border-border overflow-hidden bg-card"
                >
                  {/* Image Preview */}
                  <div className="aspect-[3/4] bg-secondary/30 relative">
                    {imageResult?.url ? (
                      <img
                        src={`${API_BASE}${imageResult.url}`}
                        alt={`Scene ${i + 1}`}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="absolute inset-0 flex items-center justify-center">
                        <StatusBadge status={imageStatus} />
                      </div>
                    )}
                    
                    {/* Retry Button */}
                    {imageStatus === "error" && (
                      <Button
                        variant="secondary"
                        size="sm"
                        className="absolute bottom-2 right-2 gap-1"
                        onClick={() => handleRetryImage(i)}
                      >
                        <RefreshCw className="w-3 h-3" />
                        重试
                      </Button>
                    )}
                  </div>

                  {/* Info */}
                  <div className="p-3 space-y-2">
                    <div className="flex items-center justify-between">
                      <Badge variant="outline">场景 {i + 1}</Badge>
                      <div className="flex gap-1">
                        <StatusBadge status={imageStatus} />
                        {audioStatus && <StatusBadge status={audioStatus} />}
                      </div>
                    </div>

                    {/* Audio Player (Video Mode) */}
                    {mode === "video" && audioResult?.url && (
                      <audio
                        src={`${API_BASE}${audioResult.url}`}
                        controls
                        className="w-full h-8"
                      />
                    )}

                    {/* Scene Info */}
                    <p className="text-xs text-muted-foreground line-clamp-2">
                      {mode === "video"
                        ? (scene as { narration: string }).narration
                        : (scene as { description: string }).description}
                    </p>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </ScrollArea>
      </div>

      {/* Video Preview (Video Mode) */}
      {mode === "video" && videoUrl && (
        <div className="space-y-4">
          <h3 className="text-sm font-medium text-foreground">视频预览</h3>
          <div className="rounded-lg overflow-hidden border border-border">
            <video
              src={`${API_BASE}${videoUrl}`}
              controls
              className="w-full max-h-[400px]"
            />
          </div>
          <div className="flex gap-3">
            <Button asChild className="gap-2">
              <a href={`${API_BASE}${videoUrl}`} download>
                <Download className="w-4 h-4" />
                下载视频
              </a>
            </Button>
          </div>
        </div>
      )}
    </section>
  );
}

