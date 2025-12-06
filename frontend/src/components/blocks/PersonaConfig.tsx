"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  User,
  Link2,
  Loader2,
  Sparkles,
  ChevronRight,
  AlertTriangle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { useWorkflowStore } from "@/store/workflow";
import { generateContent, getPersonas } from "@/lib/api";
import { toast } from "sonner";

export function PersonaConfig() {
  const {
    mode,
    selectedTopic,
    selectedCategory,
    setSelectedCategory,
    selectedPersona,
    setSelectedPersona,
    customPersona,
    setCustomPersona,
    referenceUrl,
    setReferenceUrl,
    selectedModel,
    generatedContent,
    setGeneratedContent,
    isGenerating,
    setIsGenerating,
    availablePersonas,
    setAvailablePersonas,
    setStep,
  } = useWorkflowStore();

  const [showPrompt, setShowPrompt] = useState(false);

  // Fetch personas on mount
  useEffect(() => {
    if (availablePersonas.length === 0) {
      getPersonas()
        .then((data) => setAvailablePersonas(data.categories))
        .catch(() => {});
    }
  }, [availablePersonas.length, setAvailablePersonas]);

  const categories = availablePersonas.map((c) => c.category);
  const currentPersonas =
    availablePersonas.find((c) => c.category === selectedCategory)?.personas || [];
  const selectedPersonaData = currentPersonas.find((p) => p.name === selectedPersona);

  const getPersonaPrompt = () => {
    if (selectedCategory === "自定义") {
      return customPersona;
    }
    return selectedPersonaData?.prompt || "";
  };

  const handleGenerate = async () => {
    const personaPrompt = getPersonaPrompt();
    if (!personaPrompt) {
      toast.error("请先选择或输入人设");
      return;
    }

    if (!selectedTopic) {
      toast.error("请先选择话题");
      return;
    }

    // 开始生成前先清空旧内容，避免显示缓存数据
    setGeneratedContent(null);
    setIsGenerating(true);
    
    try {
      const response = await generateContent({
        topic: selectedTopic.title,
        persona: personaPrompt,
        reference_url: referenceUrl || undefined,
        mode,
        model_name: selectedModel,
        outline: selectedTopic.outline,
      });

      // 验证响应有效性
      if (!response.titles || response.titles.length === 0 || !response.content) {
        throw new Error("生成结果无效，请重试");
      }

      setGeneratedContent(response);
      setStep("preview");
      toast.success(mode === "video" ? "视频脚本生成完成" : "图文内容生成完成");
    } catch (error) {
      // 生成失败时确保清空内容
      setGeneratedContent(null);
      toast.error("生成失败: " + (error as Error).message);
    } finally {
      setIsGenerating(false);
    }
  };

  // Disabled state
  if (!selectedTopic) {
    return (
      <section className="space-y-6 opacity-50">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-muted text-muted-foreground">
            <User className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-lg font-semibold">创作配置</h2>
            <p className="text-sm text-muted-foreground">
              选择人设风格，AI 将基于热点大纲生成内容
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 p-4 rounded-lg bg-secondary/50 text-muted-foreground">
          <ChevronRight className="w-4 h-4" />
          <span className="text-sm">请先在上一步选择话题</span>
        </div>
      </section>
    );
  }

  return (
    <section className="space-y-6">
      {/* Section Header */}
      <div className="flex items-center gap-3">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary/10 text-primary">
          <User className="w-4 h-4" />
        </div>
        <div>
          <h2 className="text-lg font-semibold">创作配置</h2>
          <p className="text-sm text-muted-foreground">
            {mode === "video"
              ? "选择人设风格，AI 将基于热点大纲生成视频脚本"
              : "选择人设风格，AI 将基于热点大纲生成 800 字深度文案"}
          </p>
        </div>
      </div>

      {/* Selected Topic Display */}
      <div className="p-4 rounded-lg bg-primary/5 border border-primary/20">
        <div className="flex items-center justify-between">
          <div>
            <span className="text-xs font-medium text-primary">已选话题</span>
            <h3 className="font-medium text-foreground mt-1">{selectedTopic.title}</h3>
          </div>
          {selectedTopic.outline.length > 0 && (
            <Badge variant="secondary" className="shrink-0">
              {selectedTopic.outline.length} 个大纲点
            </Badge>
          )}
        </div>
        {selectedTopic.outline.length > 0 && (
          <div className="mt-3 pt-3 border-t border-primary/10">
            <p className="text-xs font-medium text-muted-foreground mb-2">
              参考大纲
            </p>
            <ul className="space-y-1">
              {selectedTopic.outline.slice(0, 3).map((point, i) => (
                <li key={i} className="text-sm text-foreground/80 flex items-start gap-2">
                  <span className="text-primary shrink-0">{i + 1}.</span>
                  {point}
                </li>
              ))}
              {selectedTopic.outline.length > 3 && (
                <li className="text-sm text-muted-foreground">
                  ... 还有 {selectedTopic.outline.length - 3} 个
                </li>
              )}
            </ul>
          </div>
        )}
      </div>

      {/* Regenerate Warning */}
      {generatedContent && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-300">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span className="text-sm">重新生成将清除后续步骤的所有素材</span>
        </div>
      )}

      {/* Persona Selection */}
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">赛道</label>
          <Select
            value={selectedCategory}
            onValueChange={(v) => {
              setSelectedCategory(v);
              setSelectedPersona("");
            }}
          >
            <SelectTrigger className="h-10 bg-secondary/50 border-0">
              <SelectValue placeholder="选择赛道" />
            </SelectTrigger>
            <SelectContent>
              {categories.map((cat) => (
                <SelectItem key={cat} value={cat}>
                  {cat}
                </SelectItem>
              ))}
              <SelectItem value="自定义">自定义</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {selectedCategory !== "自定义" ? (
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">人设</label>
            <Select value={selectedPersona} onValueChange={setSelectedPersona}>
              <SelectTrigger className="h-10 bg-secondary/50 border-0">
                <SelectValue placeholder="选择人设" />
              </SelectTrigger>
              <SelectContent>
                {currentPersonas.map((p) => (
                  <SelectItem key={p.name} value={p.name}>
                    {p.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        ) : (
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">人设风格</label>
            <Input
              value={customPersona}
              onChange={(e) => setCustomPersona(e.target.value)}
              placeholder="治愈系姐姐 / 毒舌闺蜜 ..."
              className="h-10 bg-secondary/50 border-0"
            />
          </div>
        )}
      </div>

      {/* Show Persona Prompt */}
      {selectedPersonaData && (
        <Collapsible open={showPrompt} onOpenChange={setShowPrompt}>
          <CollapsibleTrigger asChild>
            <Button variant="ghost" size="sm" className="gap-1 text-muted-foreground">
              <ChevronRight
                className={cn(
                  "w-4 h-4 transition-transform",
                  showPrompt && "rotate-90"
                )}
              />
              查看人设 Prompt
            </Button>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-2 p-3 rounded-lg bg-secondary/50"
            >
              <pre className="text-xs text-muted-foreground whitespace-pre-wrap font-mono">
                {selectedPersonaData.prompt}
              </pre>
            </motion.div>
          </CollapsibleContent>
        </Collapsible>
      )}

      {/* Reference URL */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-foreground flex items-center gap-2">
          <Link2 className="w-4 h-4" />
          参考链接（可选）
        </label>
        <Input
          value={referenceUrl}
          onChange={(e) => setReferenceUrl(e.target.value)}
          placeholder="https://xiaohongshu.com/..."
          className="h-10 bg-secondary/50 border-0"
        />
        <p className="text-xs text-muted-foreground">
          输入小红书笔记链接，AI 将参考其风格进行创作
        </p>
      </div>

      {/* Generate Button */}
      <Button
        onClick={handleGenerate}
        disabled={isGenerating || !getPersonaPrompt()}
        size="lg"
        className="w-full gap-2"
      >
        {isGenerating ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            {mode === "video" ? "生成视频脚本中..." : "生成图文内容中..."}
          </>
        ) : (
          <>
            <Sparkles className="w-4 h-4" />
            开始生成
          </>
        )}
      </Button>
    </section>
  );
}

