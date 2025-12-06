"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  FileText,
  ChevronRight,
  Copy,
  Check,
  Eye,
  Image as ImageIcon,
  Mic,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { useWorkflowStore } from "@/store/workflow";
import { toast } from "sonner";

export function ContentPreview() {
  const { mode, generatedContent, selectedTitleIndex, setSelectedTitleIndex, setStep } =
    useWorkflowStore();

  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [expandedScene, setExpandedScene] = useState<number | null>(0);

  const copyToClipboard = async (text: string, index: number) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedIndex(index);
      toast.success("已复制到剪贴板");
      setTimeout(() => setCopiedIndex(null), 2000);
    } catch {
      toast.error("复制失败");
    }
  };

  // Disabled state
  if (!generatedContent) {
    return (
      <section className="space-y-6 opacity-50">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-muted text-muted-foreground">
            <Eye className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-lg font-semibold">内容预览</h2>
            <p className="text-sm text-muted-foreground">
              查看生成的内容和分镜脚本
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 p-4 rounded-lg bg-secondary/50 text-muted-foreground">
          <ChevronRight className="w-4 h-4" />
          <span className="text-sm">请先在上一步生成内容</span>
        </div>
      </section>
    );
  }

  const { titles, content, image_designs, visual_scenes } = generatedContent;
  const scenes = mode === "video" ? visual_scenes : image_designs;
  const charCount = content.replace(/\s/g, "").length;

  return (
    <section className="space-y-6">
      {/* Section Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary/10 text-primary">
            <Eye className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-lg font-semibold">内容预览</h2>
            <p className="text-sm text-muted-foreground">
              {mode === "video"
                ? "查看视频脚本和分镜设计"
                : "查看图文内容和配图方案"}
            </p>
          </div>
        </div>
        <Button onClick={() => setStep("studio")} className="gap-2">
          下一步
          <ChevronRight className="w-4 h-4" />
        </Button>
      </div>

      <Tabs defaultValue="content" className="w-full">
        <TabsList className="grid w-full grid-cols-2 h-10">
          <TabsTrigger value="content" className="gap-2">
            <FileText className="w-4 h-4" />
            {mode === "video" ? "脚本简介" : "正文内容"}
          </TabsTrigger>
          <TabsTrigger value="scenes" className="gap-2">
            {mode === "video" ? (
              <Mic className="w-4 h-4" />
            ) : (
              <ImageIcon className="w-4 h-4" />
            )}
            {mode === "video" ? `分镜 (${visual_scenes?.length || 0})` : `配图 (${image_designs?.length || 0})`}
          </TabsTrigger>
        </TabsList>

        {/* Content Tab */}
        <TabsContent value="content" className="space-y-4 mt-4">
          {/* Titles */}
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-foreground">备选标题</h3>
            <div className="space-y-2">
              {titles.map((title, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  onClick={() => setSelectedTitleIndex(i)}
                  className={cn(
                    "flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all",
                    "border hover:border-primary/30",
                    selectedTitleIndex === i
                      ? "border-primary bg-primary/5"
                      : "border-border bg-card"
                  )}
                >
                  <Badge
                    variant={selectedTitleIndex === i ? "default" : "secondary"}
                    className="shrink-0"
                  >
                    {i + 1}
                  </Badge>
                  <span className="flex-1 text-sm text-foreground">{title}</span>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 shrink-0"
                    onClick={(e) => {
                      e.stopPropagation();
                      copyToClipboard(title, i);
                    }}
                  >
                    {copiedIndex === i ? (
                      <Check className="w-4 h-4 text-emerald-500" />
                    ) : (
                      <Copy className="w-4 h-4" />
                    )}
                  </Button>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Main Content */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium text-foreground">
                {mode === "video" ? "视频简介" : "正文内容"}
              </h3>
              <span className="text-xs text-muted-foreground">{charCount} 字</span>
            </div>
            <div className="relative">
              <Textarea
                value={content}
                readOnly
                className="min-h-[200px] resize-none bg-secondary/30 border-0"
              />
              <Button
                variant="secondary"
                size="sm"
                className="absolute top-2 right-2 gap-1"
                onClick={() => copyToClipboard(content, -1)}
              >
                {copiedIndex === -1 ? (
                  <Check className="w-3 h-3 text-emerald-500" />
                ) : (
                  <Copy className="w-3 h-3" />
                )}
                复制
              </Button>
            </div>
          </div>
        </TabsContent>

        {/* Scenes Tab */}
        <TabsContent value="scenes" className="mt-4">
          <ScrollArea className="h-[500px] pr-4">
            <div className="space-y-2">
              {scenes?.map((scene, i) => {
                const isExpanded = expandedScene === i;
                const isVideoScene = mode === "video" && "narration" in scene;

                return (
                  <Collapsible
                    key={i}
                    open={isExpanded}
                    onOpenChange={() => setExpandedScene(isExpanded ? null : i)}
                  >
                    <div
                      className={cn(
                        "rounded-lg border transition-all",
                        isExpanded ? "border-primary/30" : "border-border"
                      )}
                    >
                      {/* Header */}
                      <CollapsibleTrigger className="w-full">
                        <div className="flex items-center gap-3 p-3 hover:bg-secondary/30 transition-colors">
                          <Badge variant="outline" className="shrink-0">
                            {i + 1}
                          </Badge>
                          <div className="flex-1 text-left min-w-0">
                            {isVideoScene ? (
                              <p className="text-sm text-foreground truncate">
                                {(scene as { narration: string }).narration}
                              </p>
                            ) : (
                              <p className="text-sm text-foreground truncate">
                                {(scene as { description: string }).description}
                              </p>
                            )}
                          </div>
                          <ChevronRight
                            className={cn(
                              "w-4 h-4 text-muted-foreground transition-transform",
                              isExpanded && "rotate-90"
                            )}
                          />
                        </div>
                      </CollapsibleTrigger>

                      {/* Expanded Content */}
                      <CollapsibleContent>
                        <div className="px-3 pb-3 pt-0 border-t border-border/50">
                          <div className="pt-3 space-y-3">
                            {/* Narration (Video Mode) */}
                            {isVideoScene && (
                              <div className="space-y-1">
                                <label className="text-xs font-medium text-muted-foreground">
                                  口播词
                                </label>
                                <div className="p-2 rounded bg-blue-50 dark:bg-blue-900/20 text-sm text-foreground">
                                  {(scene as { narration: string }).narration}
                                </div>
                              </div>
                            )}

                            {/* Description */}
                            <div className="space-y-1">
                              <label className="text-xs font-medium text-muted-foreground">
                                画面描述
                              </label>
                              <p className="text-sm text-foreground">
                                {(scene as { description: string }).description}
                              </p>
                            </div>

                            {/* Sentiment (Video Mode) */}
                            {isVideoScene && (scene as { sentiment?: string }).sentiment && (
                              <div className="flex items-center gap-2">
                                <span className="text-xs text-muted-foreground">情感基调:</span>
                                <Badge variant="secondary" className="text-xs">
                                  {(scene as { sentiment: string }).sentiment}
                                </Badge>
                              </div>
                            )}

                            {/* Prompt */}
                            <div className="space-y-1">
                              <div className="flex items-center justify-between">
                                <label className="text-xs font-medium text-muted-foreground">
                                  生图提示词
                                </label>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-6 text-xs gap-1"
                                  onClick={() =>
                                    copyToClipboard(
                                      (scene as { prompt: string }).prompt,
                                      100 + i
                                    )
                                  }
                                >
                                  {copiedIndex === 100 + i ? (
                                    <Check className="w-3 h-3 text-emerald-500" />
                                  ) : (
                                    <Copy className="w-3 h-3" />
                                  )}
                                  复制
                                </Button>
                              </div>
                              <pre className="p-2 rounded bg-secondary/50 text-xs text-muted-foreground whitespace-pre-wrap font-mono">
                                {(scene as { prompt: string }).prompt}
                              </pre>
                            </div>
                          </div>
                        </div>
                      </CollapsibleContent>
                    </div>
                  </Collapsible>
                );
              })}
            </div>
          </ScrollArea>
        </TabsContent>
      </Tabs>
    </section>
  );
}

