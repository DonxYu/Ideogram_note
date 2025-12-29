"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  Sparkles,
  TrendingUp,
  ChevronDown,
  ChevronRight,
  Check,
  Globe,
  AlertCircle,
  Loader2,
  RotateCcw,
  RefreshCw,
  Brain,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { useWorkflowStore } from "@/store/workflow";
import { analyzeTopics } from "@/lib/api";
import { toast } from "sonner";
import { StepProgress, type Step } from "@/components/ui/step-progress";
import { simulateStepProgress, createDefaultSteps } from "@/lib/progress-utils";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.05 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0 },
};

interface TopicRadarProps {
  onTopicSelect?: () => void;
}

export function TopicRadar({ onTopicSelect }: TopicRadarProps = {}) {
  const {
    keyword,
    setKeyword,
    topics,
    setTopics,
    topicsSource,
    selectedTopic,
    selectTopic,
    isAnalyzing,
    setIsAnalyzing,
    resetAll,
  } = useWorkflowStore();

  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);
  const [analysisSteps, setAnalysisSteps] = useState<Step[]>([]);
  const [searchMode, setSearchMode] = useState<"websearch" | "llm">("llm");

  const handleAnalyze = async (mode?: "websearch" | "llm") => {
    const actualMode = mode || searchMode;
    
    if (!keyword.trim()) {
      toast.error("请输入关键词");
      return;
    }

    // 记录当前搜索模式
    setSearchMode(actualMode);

    // 根据模式调整进度步骤
    const steps = actualMode === "llm"
      ? createDefaultSteps([
          { label: "LLM 分析关键词...", time: 3 },
          { label: "推荐热门选题...", time: 5 },
        ])
      : createDefaultSteps([
          { label: "正在分析关键词...", time: 3 },
          { label: "搜索热门话题...", time: 12 },
          { label: "提取大纲要点...", time: 8 },
          { label: "分析火爆原因...", time: 7 },
        ]);
    
    setAnalysisSteps(steps);
    setIsAnalyzing(true);

    const { promise } = simulateStepProgress({
      steps,
      onStepChange: setAnalysisSteps,
      actualTask: async () => {
        const response = await analyzeTopics(keyword.trim(), actualMode);
        setTopics(response.topics, response.source);

        if (response.source === "llm" || response.source.includes("llm")) {
          toast.success("AI 快速推荐完成");
        } else if (response.source === "websearch" || response.source.includes("websearch")) {
          toast.success("已获取实时热点数据");
        } else if (response.source === "fallback") {
          toast.warning("联网搜索失败，使用 AI 推测模式");
        } else {
          toast.error("获取热点失败，请重试");
        }
      },
    });

    try {
      await promise;
    } catch (error) {
      toast.error("分析失败: " + (error as Error).message);
    } finally {
      setIsAnalyzing(false);
      // 清空进度步骤（延迟一秒让用户看到完成状态）
      setTimeout(() => setAnalysisSteps([]), 1000);
    }
  };

  const handleSelectTopic = (topic: typeof topics[0]) => {
    selectTopic(topic);
    toast.success(`已选择: ${topic.title.slice(0, 20)}...`);
    onTopicSelect?.();
  };

  const handleReset = () => {
    resetAll();
    localStorage.removeItem("workflow-storage");
    toast.success("已重置所有数据");
  };

  return (
    <section className="space-y-6">
      {/* Section Header */}
      <div className="flex items-center gap-3">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary/10 text-primary">
          <Search className="w-4 h-4" />
        </div>
        <div>
          <h2 className="text-lg font-semibold">选题雷达</h2>
          <p className="text-sm text-muted-foreground">
            输入关键词，AI 联网搜索热门内容
          </p>
        </div>
      </div>

      {/* Search Input */}
      <div className="flex gap-3">
        <div className="relative flex-1">
          <Input
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="输入关键词：酒局妆容 / 年终奖谈判 ..."
            className="h-11 pl-4 pr-4 text-base bg-secondary/50 border-0 focus-visible:ring-1 focus-visible:ring-primary/50"
            onKeyDown={(e) => e.key === "Enter" && handleAnalyze()}
          />
        </div>
        <Button
          onClick={() => handleAnalyze("llm")}
          disabled={isAnalyzing || !keyword.trim()}
          variant={searchMode === "llm" ? "default" : "secondary"}
          className="h-11 px-6 gap-2"
        >
          {isAnalyzing && searchMode === "llm" ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Brain className="w-4 h-4" />
          )}
          {isAnalyzing && searchMode === "llm" ? "推荐中..." : "AI推荐"}
        </Button>
        <Button
          onClick={() => handleAnalyze("websearch")}
          disabled={isAnalyzing || !keyword.trim()}
          variant={searchMode === "websearch" ? "default" : "secondary"}
          className="h-11 px-6 gap-2"
        >
          {isAnalyzing && searchMode === "websearch" ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Globe className="w-4 h-4" />
          )}
          {isAnalyzing && searchMode === "websearch" ? "搜索中..." : "实时搜索"}
        </Button>
        <Button
          variant="outline"
          onClick={handleReset}
          className="h-11 px-4 gap-2"
          title="重置所有数据"
        >
          <RotateCcw className="w-4 h-4" />
          重置
        </Button>
      </div>

      {/* Analysis Progress */}
      {analysisSteps.length > 0 && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          className="p-6 rounded-xl border bg-card"
        >
          <StepProgress steps={analysisSteps} />
        </motion.div>
      )}

      {/* Topics List */}
      <AnimatePresence mode="wait">
        {topics.length > 0 && (
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            exit="hidden"
            className="space-y-4"
          >
            {/* Source Badge + Refresh */}
            <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Badge
                variant="secondary"
                className={cn(
                  "gap-1",
                  topicsSource === "websearch" && "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300",
                  topicsSource === "fallback" && "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300"
                )}
              >
                {topicsSource === "websearch" ? (
                  <Globe className="w-3 h-3" />
                ) : (
                  <AlertCircle className="w-3 h-3" />
                )}
                  {topicsSource === "websearch" ? "小红书热点" : "AI 推测"}
              </Badge>
              <span className="text-sm text-muted-foreground">
                {topics.length} 个热门话题
              </span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleAnalyze}
                disabled={isAnalyzing}
                className="gap-1.5 text-muted-foreground hover:text-foreground"
              >
                <RefreshCw className={cn("w-3.5 h-3.5", isAnalyzing && "animate-spin")} />
                换一批
              </Button>
            </div>

            {/* Topic Cards */}
            <div className="space-y-2">
              {topics.map((topic, index) => {
                const isSelected = selectedTopic?.title === topic.title;
                const isExpanded = expandedIndex === index;

                return (
                  <motion.div
                    key={topic.title}
                    variants={itemVariants}
                    layoutId={`topic-${index}`}
                  >
                    <Collapsible
                      open={isExpanded}
                      onOpenChange={() =>
                        setExpandedIndex(isExpanded ? null : index)
                      }
                    >
                      <div
                        className={cn(
                          "group relative rounded-lg border transition-all duration-200",
                          "hover:border-primary/30 hover:shadow-sm",
                          isSelected
                            ? "border-primary bg-primary/5"
                            : "border-border bg-card"
                        )}
                      >
                        {/* Main Row */}
                        <div className="flex items-center gap-3 p-4">
                          {/* Select Button */}
                          <Button
                            variant={isSelected ? "default" : "outline"}
                            size="icon"
                            className={cn(
                              "h-8 w-8 shrink-0 transition-all",
                              !isSelected && "opacity-0 group-hover:opacity-100"
                            )}
                            onClick={() => handleSelectTopic(topic)}
                          >
                            <Check className="w-4 h-4" />
                          </Button>

                          {/* Content */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <h3 className="font-medium text-foreground truncate">
                                {topic.title}
                              </h3>
                              {topic.source && (
                                <Badge variant="secondary" className="shrink-0 text-xs">
                                  {topic.source}
                                </Badge>
                              )}
                            </div>
                            {topic.summary && (
                              <p className="mt-1 text-sm text-muted-foreground line-clamp-1">
                                {topic.summary}
                              </p>
                            )}
                          </div>

                          {/* Expand Toggle */}
                          <CollapsibleTrigger asChild>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 shrink-0"
                            >
                              {isExpanded ? (
                                <ChevronDown className="w-4 h-4" />
                              ) : (
                                <ChevronRight className="w-4 h-4" />
                              )}
                            </Button>
                          </CollapsibleTrigger>
                        </div>

                        {/* Expanded Content */}
                        <CollapsibleContent>
                          <div className="px-4 pb-4 pt-0 border-t border-border/50">
                            <div className="pt-4 space-y-3">
                              {/* Outline */}
                              {topic.outline.length > 0 && (
                                <div>
                                  <h4 className="text-xs font-medium text-muted-foreground mb-2">
                                    内容大纲
                                  </h4>
                                  <ul className="space-y-1">
                                    {topic.outline.map((point, i) => (
                                      <li
                                        key={i}
                                        className="text-sm text-foreground flex items-start gap-2"
                                      >
                                        <span className="text-primary shrink-0">
                                          {i + 1}.
                                        </span>
                                        {point}
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}

                              {/* Why Hot */}
                              {topic.why_hot && (
                                <div className="flex items-start gap-2 p-3 rounded-md bg-secondary/50">
                                  <TrendingUp className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                                  <div>
                                    <span className="text-xs font-medium text-muted-foreground">
                                      火爆原因
                                    </span>
                                    <p className="text-sm text-foreground mt-0.5">
                                      {topic.why_hot}
                                    </p>
                                  </div>
                                </div>
                              )}

                              {/* Select Button */}
                              <Button
                                onClick={() => handleSelectTopic(topic)}
                                className="w-full gap-2"
                                variant={isSelected ? "secondary" : "default"}
                              >
                                <Check className="w-4 h-4" />
                                {isSelected ? "已选择此话题" : "选择此话题"}
                              </Button>
                            </div>
                          </div>
                        </CollapsibleContent>
                      </div>
                    </Collapsible>
                  </motion.div>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Empty State */}
      {!isAnalyzing && topics.length === 0 && (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div className="w-12 h-12 rounded-full bg-secondary flex items-center justify-center mb-4">
            <Search className="w-6 h-6 text-muted-foreground" />
          </div>
          <h3 className="font-medium text-foreground mb-1">输入关键词开始</h3>
          <p className="text-sm text-muted-foreground max-w-sm">
            AI 将联网搜索小红书热门笔记，为你提供爆款选题建议
          </p>
        </div>
      )}
    </section>
  );
}

