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
  Thermometer,
  GitCompare,
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
import { Slider } from "@/components/ui/slider";
import { useWorkflowStore } from "@/store/workflow";
import { generateContent, getPersonas } from "@/lib/api";
import { toast } from "sonner";
import { StepProgress, type Step } from "@/components/ui/step-progress";
import { simulateStepProgress, createDefaultSteps } from "@/lib/progress-utils";

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
    temperature,
    setTemperature,
    dualModelMode,
    setDualModelMode,
    secondModel,
    setSecondModel,
    setDualResults,
    availableModels,
  } = useWorkflowStore();

  const [showPrompt, setShowPrompt] = useState(false);
  const [generationSteps, setGenerationSteps] = useState<Step[]>([]);

  // Fetch personas on mount
  useEffect(() => {
    if (availablePersonas.length === 0) {
      getPersonas()
        .then((data) => setAvailablePersonas(data.categories))
        .catch(() => {});
    }
  }, [availablePersonas.length, setAvailablePersonas]);

  // 根据 mode 过滤人设分类
  const categories = mode === "wechat"
    ? availablePersonas.filter((c) => c.category === "硬核技术/AI" || c.category === "自定义").map((c) => c.category)
    : availablePersonas.map((c) => c.category);
  
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
    
    if (dualModelMode && !secondModel) {
      toast.error("请选择第二个模型");
      return;
    }

    // 开始生成前先清空旧内容，避免显示缓存数据
    setGeneratedContent(null);
    setDualResults(null);
    setIsGenerating(true);

    // 初始化进度步骤（调整为更接近实际耗时）
    const steps = dualModelMode
      ? createDefaultSteps([
          { label: "准备创作上下文...", time: 3 },
          { label: `${selectedModel.split('/').pop()} 创作中...`, time: 25 },
          { label: `${secondModel.split('/').pop()} 创作中...`, time: 2 }, // 并行，所以时间很短
          { label: "质量检测与对比...", time: 6 },
        ])
      : createDefaultSteps([
          { label: "准备创作上下文...", time: 3 },
          { label: "LLM 深度创作中...", time: 25 },
          { label: "质量检测与优化...", time: 5 },
          { label: "生成配图方案...", time: 4 },
        ]);
    
    setGenerationSteps(steps);
    
    const { promise } = simulateStepProgress({
      steps,
      onStepChange: setGenerationSteps,
      actualTask: async () => {
        const params = {
          topic: selectedTopic.title,
          persona: personaPrompt,
          reference_url: referenceUrl || undefined,
          mode,
          outline: selectedTopic.outline,
          temperature,
        };
        
        if (dualModelMode) {
          // 双模型并行生成
          const [result1, result2] = await Promise.all([
            generateContent({ ...params, model_name: selectedModel }),
            generateContent({ ...params, model_name: secondModel })
          ]);
          
          setDualResults({ model1: result1, model2: result2 });
          setStep("preview");
          toast.success("双模型生成完成，请选择更优版本");
        } else {
          // 单模型生成
          const response = await generateContent({
            ...params,
            model_name: selectedModel,
          });

          setGeneratedContent(response);
          setStep("preview");
          toast.success(mode === "video" ? "视频脚本生成完成" : "图文内容生成完成");
        }
      },
    });

    try {
      await promise;
    } catch (error) {
      // 生成失败时确保清空内容
      setGeneratedContent(null);
      setDualResults(null);
      toast.error("生成失败: " + (error as Error).message);
    } finally {
      setIsGenerating(false);
      setTimeout(() => setGenerationSteps([]), 1000);
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

      {/* Advanced Settings */}
      <div className="space-y-4 p-4 rounded-lg bg-secondary/30 border border-border/50">
        <h3 className="text-sm font-medium text-foreground flex items-center gap-2">
          <Thermometer className="w-4 h-4" />
          高级设置
        </h3>

        {/* Temperature Slider */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-sm text-muted-foreground">
              创意度 (Temperature)
            </label>
            <span className="text-sm font-mono text-foreground">
              {temperature.toFixed(2)}
            </span>
          </div>
          <Slider
            value={[temperature]}
            onValueChange={(v) => setTemperature(v[0])}
            min={0.3}
            max={1.0}
            step={0.05}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>稳定专业 (0.3-0.5)</span>
            <span>平衡模式 (0.6-0.8)</span>
            <span>创意发散 (0.9-1.0)</span>
          </div>
        </div>

        {/* Dual Model Toggle */}
        <div className="space-y-3 pt-3 border-t border-border/50">
          <div className="flex items-center justify-between">
            <label className="text-sm text-muted-foreground flex items-center gap-2">
              <GitCompare className="w-4 h-4" />
              双模型对比生成
            </label>
            <Button
              variant={dualModelMode ? "default" : "outline"}
              size="sm"
              onClick={() => setDualModelMode(!dualModelMode)}
            >
              {dualModelMode ? "已启用" : "已禁用"}
            </Button>
          </div>
          
          {dualModelMode && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="space-y-3"
            >
              <div className="flex items-center gap-2 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0" />
                <p className="text-xs text-amber-600 dark:text-amber-400">
                  双模型模式将消耗双倍 API 额度
                </p>
              </div>
              
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <label className="text-xs text-muted-foreground">模型 A</label>
                  <div className="p-2 rounded bg-primary/10 border border-primary/20">
                    <p className="text-xs font-medium truncate">{selectedModel}</p>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <label className="text-xs text-muted-foreground">模型 B</label>
                  <Select 
                    value={secondModel} 
                    onValueChange={setSecondModel}
                    disabled={availableModels.length === 0}
                  >
                    <SelectTrigger className="h-9 text-xs bg-secondary/50 border-0">
                      <SelectValue placeholder={
                        availableModels.length === 0 
                          ? "加载模型列表..." 
                          : "选择第二个模型"
                      } />
                    </SelectTrigger>
                    <SelectContent>
                      {availableModels.length === 0 ? (
                        <SelectItem value="__loading__" disabled>
                          加载中...
                        </SelectItem>
                      ) : availableModels.filter((m) => m.value !== selectedModel).length === 0 ? (
                        <SelectItem value="__no_options__" disabled>
                          无可用模型
                        </SelectItem>
                      ) : (
                        availableModels
                          .filter((m) => m.value !== selectedModel)
                          .map((model) => (
                            <SelectItem key={model.value} value={model.value}>
                              {model.label}
                            </SelectItem>
                          ))
                      )}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </motion.div>
          )}
        </div>
      </div>

      {/* Generation Progress */}
      {generationSteps.length > 0 && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          className="p-6 rounded-xl border bg-card"
        >
          <StepProgress steps={generationSteps} />
        </motion.div>
      )}

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
