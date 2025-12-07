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
import { GenerateResponse } from "@/lib/api";
import { toast } from "sonner";

// Dual Model Comparison Card Component
function DualModelCard({
  model,
  content,
  version,
  isSelected,
  onSelect,
}: {
  model: string;
  content: GenerateResponse;
  version: 'model1' | 'model2';
  isSelected: boolean;
  onSelect: () => void;
}) {
  const modelName = model.split('/').pop() || model;
  const [copiedType, setCopiedType] = useState<'title' | 'content' | null>(null);

  const copyToClipboard = async (text: string, type: 'title' | 'content') => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedType(type);
      toast.success("已复制到剪贴板");
      setTimeout(() => setCopiedType(null), 2000);
    } catch {
      toast.error("复制失败");
    }
  };
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "relative p-6 rounded-xl border-2 transition-all",
        isSelected
          ? "border-primary bg-primary/5 shadow-lg"
          : "border-border bg-card hover:border-primary/50"
      )}
    >
      {/* Model Badge */}
      <div className="flex items-center justify-between mb-4">
        <Badge variant={isSelected ? "default" : "outline"} className="text-xs">
          {modelName}
        </Badge>
        <Button
          size="sm"
          variant={isSelected ? "default" : "outline"}
          onClick={onSelect}
          className="gap-2"
        >
          {isSelected ? (
            <>
              <Check className="w-3 h-3" />
              已选择
            </>
          ) : (
            "选择此版本"
          )}
        </Button>
      </div>

      {/* Title Preview */}
      <div className="space-y-2 mb-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-muted-foreground">标题预览</h3>
          <Button
            size="sm"
            variant="ghost"
            className="h-6 gap-1"
            onClick={() => copyToClipboard(content.titles[0], 'title')}
          >
            {copiedType === 'title' ? (
              <Check className="w-3 h-3 text-green-500" />
            ) : (
              <Copy className="w-3 h-3" />
            )}
            <span className="text-xs">复制</span>
          </Button>
        </div>
        <p className="text-base font-medium line-clamp-2">{content.titles[0]}</p>
      </div>

      {/* Content Preview */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-muted-foreground">正文预览</h3>
          <Button
            size="sm"
            variant="ghost"
            className="h-6 gap-1"
            onClick={() => copyToClipboard(content.content, 'content')}
          >
            {copiedType === 'content' ? (
              <Check className="w-3 h-3 text-green-500" />
            ) : (
              <Copy className="w-3 h-3" />
            )}
            <span className="text-xs">复制</span>
          </Button>
        </div>
        <ScrollArea className="h-[300px] rounded-lg border p-3 bg-secondary/30">
          <p className="text-sm whitespace-pre-wrap leading-relaxed">
            {content.content}
          </p>
        </ScrollArea>
      </div>

      {/* Stats */}
      <div className="mt-4 pt-4 border-t flex gap-4 text-xs text-muted-foreground">
        <span>{content.titles.length} 个标题</span>
        <span>{content.content.length} 字</span>
        {content.image_designs && <span>{content.image_designs.length} 张配图</span>}
        {content.visual_scenes && <span>{content.visual_scenes.length} 个分镜</span>}
      </div>
    </motion.div>
  );
}

export function ContentPreview() {
  const {
    mode,
    generatedContent,
    selectedTitleIndex,
    setSelectedTitleIndex,
    setStep,
    dualResults,
    selectedVersion,
    setSelectedVersion,
    selectedModel,
    secondModel,
  } = useWorkflowStore();

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
  if (!generatedContent && !dualResults) {
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
  
  // Dual model comparison view
  if (dualResults) {
    return (
      <section className="space-y-6">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary/10">
            <Eye className="w-4 h-4 text-primary" />
          </div>
          <div>
            <h2 className="text-lg font-semibold">双模型对比</h2>
            <p className="text-sm text-muted-foreground">
              选择更优版本继续制作
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-6">
          {/* Model 1 */}
          <DualModelCard
            model={selectedModel}
            content={dualResults.model1}
            version="model1"
            isSelected={selectedVersion === 'model1'}
            onSelect={() => setSelectedVersion('model1')}
          />

          {/* Model 2 */}
          <DualModelCard
            model={secondModel}
            content={dualResults.model2}
            version="model2"
            isSelected={selectedVersion === 'model2'}
            onSelect={() => setSelectedVersion('model2')}
          />
        </div>

        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={() => setStep("persona")}
            className="flex-1"
          >
            重新生成
          </Button>
          <Button
            onClick={() => setStep("studio")}
            className="flex-1 gap-2"
          >
            继续制作 ({selectedVersion === 'model1' ? selectedModel.split('/').pop() : secondModel.split('/').pop()})
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      </section>
    );
  }

  const { titles, content, image_designs, visual_scenes, diagrams } = generatedContent;
  const scenes = mode === "video" ? visual_scenes : mode === "wechat" ? diagrams : image_designs;
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
                : mode === "wechat"
                ? "查看文章正文和架构图设计"
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
            {mode === "video" ? "脚本简介" : mode === "wechat" ? "文章正文" : "正文内容"}
          </TabsTrigger>
          <TabsTrigger value="scenes" className="gap-2">
            {mode === "video" ? (
              <Mic className="w-4 h-4" />
            ) : (
              <ImageIcon className="w-4 h-4" />
            )}
            {mode === "video" 
              ? `分镜 (${visual_scenes?.length || 0})` 
              : mode === "wechat"
              ? `架构图 (${diagrams?.length || 0})`
              : `配图 (${image_designs?.length || 0})`}
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
                const isDiagram = mode === "wechat" && "title" in scene;

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
                            {isDiagram && (scene as any).diagram_type ? (
                              <span className="text-xs">
                                {(scene as any).diagram_type === "architecture" ? "架构" : (scene as any).diagram_type === "flow" ? "流程" : "对比"}
                              </span>
                            ) : (
                              i + 1
                            )}
                          </Badge>
                          <div className="flex-1 text-left min-w-0">
                            {isDiagram ? (
                              <p className="text-sm font-medium text-foreground truncate">
                                {(scene as any).title || (scene as { description: string }).description}
                              </p>
                            ) : isVideoScene ? (
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
                            {/* Diagram Title (Wechat Mode) */}
                            {isDiagram && (scene as any).title && (
                              <div className="space-y-1">
                                <label className="text-xs font-medium text-muted-foreground">
                                  架构图标题
                                </label>
                                <p className="text-sm font-medium text-foreground">
                                  {(scene as any).title}
                                </p>
                              </div>
                            )}

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
                                {isDiagram ? "技术描述" : "画面描述"}
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

