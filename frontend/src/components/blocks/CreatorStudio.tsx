"use client";

import { useState, useEffect, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles,
  Loader2,
  Copy,
  Check,
  RefreshCw,
  FileText,
  Image as ImageIcon,
  ChevronDown,
  ChevronUp,
  Lightbulb,
  Shuffle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { useWorkflowStore } from "@/store/workflow";
import { generateContent } from "@/lib/api";
import { toast } from "sonner";

export function CreatorStudio() {
  const {
    mode,
    selectedModel,
    selectedCategory,
    selectedPersona,
    temperature,
    generatedContent,
    setGeneratedContent,
    selectedTitleIndex,
    setSelectedTitleIndex,
    availablePersonas,
    selectedTopic,
    selectTopic,
  } = useWorkflowStore();

  const [topic, setTopic] = useState("");
  const [suggestionSeed, setSuggestionSeed] = useState(0);

  // Sync with selected topic from hot search
  useEffect(() => {
    if (selectedTopic?.title) {
      setTopic(selectedTopic.title);
    }
  }, [selectedTopic]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);
  const [expandedPrompts, setExpandedPrompts] = useState<number[]>([0]);

  // 预设选题库
  const topicSuggestions: Record<string, string[]> = {
    "职场": [
      "领导总把功劳揽走，我该怎么办",
      "35岁要不要转管理岗",
      "跳槽时如何谈出理想薪资",
      "如何让老板主动给你升职",
      "被同事甩锅了怎么优雅反击",
      "大厂和小公司，选哪个更好",
      "工作3年还没晋升，问题出在哪",
      "如何向上管理，让领导成为你的资源",
      "被裁员后，我才明白的职场真相",
      "为什么你的努力老板看不见",
      "30岁还在做执行，是不是废了",
      "高情商拒绝加班的3种话术",
    ],
    "硬核技术/AI": [
      "AI时代，普通人如何不被淘汰",
      "用AI提升工作效率的5个实战技巧",
      "ChatGPT写文案，效果翻倍的提示词",
      "AI会取代哪些岗位？如何提前布局",
      "非技术人员如何用好AI工具",
      "AI时代的个人竞争力怎么建立",
      "用AI做副业，月入过万的真实案例",
      "学会这3个AI技能，效率提升10倍",
    ],
    "生活": [
      "30岁前一定要明白的人生道理",
      "如何摆脱精神内耗",
      "自律的人都在用的时间管理法",
      "如何建立自己的第二曲线",
      "普通人如何打造个人IP",
      "如何在迷茫期找到方向",
      "焦虑的时候，做这3件事最有效",
      "下班后做什么副业最靠谱",
    ],
  };

  // 根据当前赛道获取推荐选题
  const currentSuggestions = useMemo(() => {
    const categoryTopics = topicSuggestions[selectedCategory] || topicSuggestions["职场"];
    // 使用 seed 来决定起始位置，实现"换一批"
    const startIndex = (suggestionSeed * 4) % categoryTopics.length;
    const result: string[] = [];
    for (let i = 0; i < 4; i++) {
      result.push(categoryTopics[(startIndex + i) % categoryTopics.length]);
    }
    return result;
  }, [selectedCategory, suggestionSeed]);

  const handleRefreshSuggestions = () => {
    setSuggestionSeed((prev) => prev + 1);
  };

  // 获取当前人设的 prompt
  const getPersonaPrompt = () => {
    const category = availablePersonas.find((c) => c.category === selectedCategory);
    const persona = category?.personas.find((p) => p.name === selectedPersona);
    return persona?.prompt || selectedPersona;
  };

  const handleGenerate = async () => {
    if (!topic.trim()) {
      toast.error("请输入选题");
      return;
    }

    const personaPrompt = getPersonaPrompt();
    if (!personaPrompt) {
      toast.error("请在侧边栏选择人设");
      return;
    }

    setIsGenerating(true);
    setGeneratedContent(null);

    try {
      const response = await generateContent({
        topic: topic.trim(),
        persona: personaPrompt,
        mode,
        model_name: selectedModel,
        temperature,
      });

      setGeneratedContent(response);
      toast.success("生成完成！");
    } catch (error) {
      toast.error("生成失败: " + (error as Error).message);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopied(key);
    toast.success("已复制");
    setTimeout(() => setCopied(null), 2000);
  };

  const togglePromptExpand = (index: number) => {
    setExpandedPrompts((prev) =>
      prev.includes(index) ? prev.filter((i) => i !== index) : [...prev, index]
    );
  };

  const designs = generatedContent?.image_designs || [];
  const scenes = generatedContent?.visual_scenes || [];
  const diagrams = generatedContent?.diagrams || [];

  // 根据模式选择显示的配图数据
  const visualData = mode === "video" ? scenes : mode === "wechat" ? diagrams : designs;

  return (
    <div className="flex flex-col h-full">
      {/* Input Area */}
      <div className="p-6 border-b bg-background/50 backdrop-blur-sm">
        <div className="max-w-2xl mx-auto space-y-4">
          <div className="flex gap-3">
            <Input
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder={
                mode === "video"
                  ? "输入视频选题，如：AI 时代普通人如何破局"
                  : mode === "wechat"
                  ? "输入技术主题，如：RAG 架构设计最佳实践"
                  : "输入小红书选题，如：30岁裸辞后我才明白的道理"
              }
              className="flex-1 h-12 text-base"
              onKeyDown={(e) => e.key === "Enter" && !isGenerating && handleGenerate()}
              disabled={isGenerating}
            />
            <Button
              onClick={handleGenerate}
              disabled={isGenerating || !topic.trim()}
              size="lg"
              className="h-12 px-6 gap-2"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  生成中...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  一键生成
                </>
              )}
            </Button>
          </div>

          {/* Topic Suggestions */}
          {!generatedContent && !isGenerating && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground flex items-center gap-1">
                  <Lightbulb className="w-3 h-3" />
                  推荐选题（点击使用）
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 text-xs gap-1"
                  onClick={handleRefreshSuggestions}
                >
                  <Shuffle className="w-3 h-3" />
                  换一批
                </Button>
              </div>
              <div className="flex flex-wrap gap-2">
                {currentSuggestions.map((suggestion, i) => (
                  <button
                    key={`${suggestionSeed}-${i}`}
                    onClick={() => setTopic(suggestion)}
                    className="px-3 py-1.5 text-xs rounded-full border border-border bg-secondary/30 hover:bg-secondary/60 hover:border-primary/30 transition-colors text-left"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Current Config Display */}
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Badge variant="secondary" className="text-xs">
              {mode === "video" ? "视频" : mode === "wechat" ? "公众号" : "图文"}
            </Badge>
            <span>·</span>
            <span>{selectedPersona || "未选择人设"}</span>
            <span>·</span>
            <span>温度 {temperature.toFixed(2)}</span>
          </div>
        </div>
      </div>

      {/* Result Area */}
      <div className="flex-1 overflow-hidden">
        <AnimatePresence mode="wait">
          {isGenerating ? (
            <motion.div
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center justify-center h-full gap-4"
            >
              <div className="relative">
                <Loader2 className="w-12 h-12 animate-spin text-primary" />
                <Sparkles className="w-4 h-4 text-primary absolute top-0 right-0 animate-pulse" />
              </div>
              <div className="text-center space-y-1">
                <p className="text-lg font-medium">AI 正在创作中...</p>
                <p className="text-sm text-muted-foreground">
                  {mode === "video"
                    ? "生成视频脚本和分镜设计"
                    : mode === "wechat"
                    ? "生成技术文章和架构图"
                    : "生成爆款文案和配图设计"}
                </p>
              </div>
            </motion.div>
          ) : generatedContent ? (
            <motion.div
              key="result"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="h-full"
            >
              <Tabs defaultValue="content" className="h-full flex flex-col">
                <div className="border-b px-6">
                  <TabsList className="h-12">
                    <TabsTrigger value="content" className="gap-2">
                      <FileText className="w-4 h-4" />
                      正文内容
                    </TabsTrigger>
                    <TabsTrigger value="visuals" className="gap-2">
                      <ImageIcon className="w-4 h-4" />
                      {mode === "video" ? "分镜设计" : mode === "wechat" ? "架构图" : "配图设计"}
                      <Badge variant="secondary" className="ml-1 text-xs">
                        {visualData.length}
                      </Badge>
                    </TabsTrigger>
                  </TabsList>
                </div>

                <TabsContent value="content" className="flex-1 mt-0 overflow-hidden">
                  <ScrollArea className="h-full">
                    <div className="p-6 space-y-6 max-w-3xl mx-auto">
                      {/* Title Selection */}
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <h3 className="text-sm font-medium text-muted-foreground">
                            标题候选 ({generatedContent.titles.length})
                          </h3>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="gap-1 text-xs"
                            onClick={() =>
                              handleCopy(
                                generatedContent.titles[selectedTitleIndex],
                                "title"
                              )
                            }
                          >
                            {copied === "title" ? (
                              <Check className="w-3 h-3" />
                            ) : (
                              <Copy className="w-3 h-3" />
                            )}
                            复制标题
                          </Button>
                        </div>
                        <div className="grid gap-2">
                          {generatedContent.titles.map((title, i) => (
                            <button
                              key={i}
                              onClick={() => setSelectedTitleIndex(i)}
                              className={cn(
                                "w-full text-left p-3 rounded-lg border transition-all",
                                selectedTitleIndex === i
                                  ? "border-primary bg-primary/5 ring-1 ring-primary"
                                  : "border-border hover:border-primary/50"
                              )}
                            >
                              <span className="text-sm">{title}</span>
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Content */}
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <h3 className="text-sm font-medium text-muted-foreground">正文</h3>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="gap-1 text-xs"
                            onClick={() => handleCopy(generatedContent.content, "content")}
                          >
                            {copied === "content" ? (
                              <Check className="w-3 h-3" />
                            ) : (
                              <Copy className="w-3 h-3" />
                            )}
                            复制正文
                          </Button>
                        </div>
                        <div className="prose prose-sm dark:prose-invert max-w-none">
                          <div className="whitespace-pre-wrap text-sm leading-relaxed bg-secondary/30 rounded-lg p-4">
                            {generatedContent.content}
                          </div>
                        </div>
                      </div>
                    </div>
                  </ScrollArea>
                </TabsContent>

                <TabsContent value="visuals" className="flex-1 mt-0 overflow-hidden">
                  <ScrollArea className="h-full">
                    <div className="p-6 space-y-4 max-w-3xl mx-auto">
                      {visualData.map((item: any, i: number) => (
                        <Collapsible
                          key={i}
                          open={expandedPrompts.includes(i)}
                          onOpenChange={() => togglePromptExpand(i)}
                        >
                          <div className="rounded-lg border bg-card overflow-hidden">
                            <CollapsibleTrigger asChild>
                              <button className="w-full flex items-center justify-between p-4 hover:bg-secondary/30 transition-colors">
                                <div className="flex items-center gap-3">
                                  <Badge variant="outline">
                                    {mode === "video" ? `场景 ${i + 1}` : `图片 ${i + 1}`}
                                  </Badge>
                                  <span className="text-sm text-muted-foreground truncate max-w-[300px]">
                                    {item.description || item.title || item.narration}
                                  </span>
                                </div>
                                {expandedPrompts.includes(i) ? (
                                  <ChevronUp className="w-4 h-4 text-muted-foreground" />
                                ) : (
                                  <ChevronDown className="w-4 h-4 text-muted-foreground" />
                                )}
                              </button>
                            </CollapsibleTrigger>
                            <CollapsibleContent>
                              <div className="px-4 pb-4 space-y-3">
                                {/* Description */}
                                <div className="space-y-1">
                                  <label className="text-xs font-medium text-muted-foreground">
                                    {mode === "video" ? "画面描述" : "设计说明"}
                                  </label>
                                  <p className="text-sm">
                                    {item.description || item.title}
                                  </p>
                                </div>

                                {/* Narration (video mode) */}
                                {mode === "video" && item.narration && (
                                  <div className="space-y-1">
                                    <label className="text-xs font-medium text-muted-foreground">
                                      口播词
                                    </label>
                                    <p className="text-sm">{item.narration}</p>
                                  </div>
                                )}

                                {/* Prompt */}
                                <div className="space-y-1">
                                  <div className="flex items-center justify-between">
                                    <label className="text-xs font-medium text-muted-foreground">
                                      生图 Prompt
                                    </label>
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      className="h-6 gap-1 text-xs"
                                      onClick={() => handleCopy(item.prompt, `prompt-${i}`)}
                                    >
                                      {copied === `prompt-${i}` ? (
                                        <Check className="w-3 h-3" />
                                      ) : (
                                        <Copy className="w-3 h-3" />
                                      )}
                                      复制
                                    </Button>
                                  </div>
                                  <pre className="text-xs bg-secondary/50 p-3 rounded whitespace-pre-wrap font-mono">
                                    {item.prompt}
                                  </pre>
                                </div>
                              </div>
                            </CollapsibleContent>
                          </div>
                        </Collapsible>
                      ))}
                    </div>
                  </ScrollArea>
                </TabsContent>
              </Tabs>
            </motion.div>
          ) : (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center justify-center h-full text-center px-4"
            >
              <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center mb-6">
                <Sparkles className="w-10 h-10 text-primary/50" />
              </div>
              <h2 className="text-xl font-semibold mb-2">开始创作</h2>
              <p className="text-muted-foreground max-w-md">
                {mode === "video"
                  ? "输入视频选题，AI 将生成完整的视频脚本和分镜设计"
                  : mode === "wechat"
                  ? "输入技术主题，AI 将生成深度技术文章和架构图设计"
                  : "输入小红书选题，AI 将生成爆款文案和配图设计"}
              </p>
              <div className="flex items-center gap-4 mt-8 text-sm text-muted-foreground">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-green-500" />
                  标题候选
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-blue-500" />
                  正文内容
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-purple-500" />
                  配图 Prompt
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Bottom Action Bar */}
      {generatedContent && !isGenerating && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="border-t p-4 bg-background/80 backdrop-blur-sm"
        >
          <div className="max-w-2xl mx-auto flex items-center justify-between">
            <div className="text-sm text-muted-foreground">
              {generatedContent.titles.length} 个标题 · {generatedContent.content.length} 字 · {visualData.length} 张配图
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                className="gap-2"
                onClick={handleGenerate}
              >
                <RefreshCw className="w-4 h-4" />
                重新生成
              </Button>
              <Button
                size="sm"
                className="gap-2"
                onClick={() => {
                  const title = generatedContent.titles[selectedTitleIndex];
                  const content = generatedContent.content;
                  const prompts = visualData.map((v: any, i: number) => 
                    `【图${i + 1}】\n${v.prompt}`
                  ).join("\n\n");
                  
                  const fullText = `${title}\n\n${content}\n\n---\n配图 Prompt:\n${prompts}`;
                  handleCopy(fullText, "all");
                }}
              >
                {copied === "all" ? (
                  <Check className="w-4 h-4" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
                复制全部
              </Button>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}

