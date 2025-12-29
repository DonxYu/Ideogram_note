"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronLeft,
  ChevronRight,
  Sparkles,
  FileText,
  Video,
  Settings,
  Brain,
  Moon,
  Sun,
  BookOpen,
  User,
  Thermometer,
  Search,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Slider } from "@/components/ui/slider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useWorkflowStore } from "@/store/workflow";
import { getPersonas } from "@/lib/api";

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  onOpenHotSearch?: () => void;
}

export function Sidebar({ collapsed, onToggle, onOpenHotSearch }: SidebarProps) {
  const [isDark, setIsDark] = useState(false);
  const {
    mode,
    setMode,
    selectedModel,
    setSelectedModel,
    selectedCategory,
    setSelectedCategory,
    selectedPersona,
    setSelectedPersona,
    temperature,
    setTemperature,
    availableModels,
    availablePersonas,
    setAvailablePersonas,
  } = useWorkflowStore();

  // Fetch personas on mount
  useEffect(() => {
    if (availablePersonas.length === 0) {
      getPersonas()
        .then((data) => setAvailablePersonas(data.categories))
        .catch(() => {});
    }
  }, [availablePersonas.length, setAvailablePersonas]);

  const toggleTheme = () => {
    setIsDark(!isDark);
    document.documentElement.classList.toggle("dark");
  };

  // 根据 mode 过滤人设分类
  const categories = mode === "wechat"
    ? availablePersonas.filter((c) => c.category === "硬核技术/AI").map((c) => c.category)
    : availablePersonas.map((c) => c.category);
  
  const currentPersonas =
    availablePersonas.find((c) => c.category === selectedCategory)?.personas || [];

  return (
    <TooltipProvider delayDuration={0}>
      <motion.aside
        initial={false}
        animate={{ width: collapsed ? 64 : 280 }}
        transition={{ duration: 0.2, ease: "easeInOut" }}
        className={cn(
          "relative flex flex-col h-screen bg-sidebar border-r border-sidebar-border",
          "transition-colors duration-200"
        )}
      >
        {/* Header */}
        <div className="flex items-center h-14 px-4 border-b border-sidebar-border">
          <AnimatePresence mode="wait">
            {!collapsed && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex items-center gap-2 flex-1 min-w-0"
              >
                <Sparkles className="w-5 h-5 text-primary shrink-0" />
                <span className="font-semibold text-sidebar-foreground truncate">
                  内容工作流
                </span>
              </motion.div>
            )}
          </AnimatePresence>

          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                onClick={onToggle}
                className={cn(
                  "h-8 w-8 shrink-0 text-sidebar-foreground hover:bg-sidebar-accent",
                  collapsed && "mx-auto"
                )}
              >
                {collapsed ? (
                  <ChevronRight className="w-4 h-4" />
                ) : (
                  <ChevronLeft className="w-4 h-4" />
                )}
              </Button>
            </TooltipTrigger>
            <TooltipContent side="right">
              {collapsed ? "展开" : "收起"}
            </TooltipContent>
          </Tooltip>
        </div>

        {/* Mode Selection */}
        <div className="p-3">
          <div className={cn("flex gap-1", collapsed && "flex-col")}>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant={mode === "image" ? "secondary" : "ghost"}
                  size={collapsed ? "icon" : "sm"}
                  onClick={() => setMode("image")}
                  className={cn(
                    "flex-1 justify-start gap-2",
                    collapsed && "w-10 h-10 justify-center",
                    mode === "image" && "bg-sidebar-accent"
                  )}
                >
                  <FileText className="w-4 h-4 shrink-0" />
                  {!collapsed && <span>图文模式</span>}
                </Button>
              </TooltipTrigger>
              {collapsed && <TooltipContent side="right">图文模式</TooltipContent>}
            </Tooltip>

            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant={mode === "video" ? "secondary" : "ghost"}
                  size={collapsed ? "icon" : "sm"}
                  onClick={() => setMode("video")}
                  className={cn(
                    "flex-1 justify-start gap-2",
                    collapsed && "w-10 h-10 justify-center",
                    mode === "video" && "bg-sidebar-accent"
                  )}
                >
                  <Video className="w-4 h-4 shrink-0" />
                  {!collapsed && <span>视频模式</span>}
                </Button>
              </TooltipTrigger>
              {collapsed && <TooltipContent side="right">视频模式</TooltipContent>}
            </Tooltip>

            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant={mode === "wechat" ? "secondary" : "ghost"}
                  size={collapsed ? "icon" : "sm"}
                  onClick={() => setMode("wechat")}
                  className={cn(
                    "flex-1 justify-start gap-2",
                    collapsed && "w-10 h-10 justify-center",
                    mode === "wechat" && "bg-sidebar-accent"
                  )}
                >
                  <BookOpen className="w-4 h-4 shrink-0" />
                  {!collapsed && <span>公众号</span>}
                </Button>
              </TooltipTrigger>
              {collapsed && <TooltipContent side="right">公众号模式</TooltipContent>}
            </Tooltip>
          </div>
        </div>

        <Separator className="bg-sidebar-border" />

        {/* Settings - Only show when expanded */}
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="flex-1 overflow-auto"
            >
              <div className="p-3 space-y-4">
                {/* Model Selection */}
                <div className="space-y-2">
                  <label className="flex items-center gap-2 text-xs font-medium text-sidebar-foreground/70">
                    <Brain className="w-3.5 h-3.5" />
                    写作模型
                  </label>
                  <Select value={selectedModel} onValueChange={setSelectedModel}>
                    <SelectTrigger className="h-8 text-xs bg-sidebar-accent border-0">
                      <SelectValue placeholder="选择模型" />
                    </SelectTrigger>
                    <SelectContent>
                      {availableModels.length > 0 ? (
                        availableModels.map((m) => (
                          <SelectItem key={m.value} value={m.value} className="text-xs">
                            {m.label}
                          </SelectItem>
                        ))
                      ) : (
                        <>
                          <SelectItem value="deepseek/deepseek-chat" className="text-xs">
                            DeepSeek V3
                          </SelectItem>
                          <SelectItem value="anthropic/claude-3.5-sonnet" className="text-xs">
                            Claude 3.5
                          </SelectItem>
                          <SelectItem value="openai/gpt-4o" className="text-xs">
                            GPT-4o
                          </SelectItem>
                        </>
                      )}
                    </SelectContent>
                  </Select>
                </div>

                <Separator className="bg-sidebar-border" />

                {/* Persona Selection */}
                <div className="space-y-2">
                  <label className="flex items-center gap-2 text-xs font-medium text-sidebar-foreground/70">
                    <User className="w-3.5 h-3.5" />
                    写作人设
                  </label>
                  
                  {/* Category */}
                  <Select
                    value={selectedCategory}
                    onValueChange={(v) => {
                      setSelectedCategory(v);
                    }}
                  >
                    <SelectTrigger className="h-8 text-xs bg-sidebar-accent border-0">
                      <SelectValue placeholder="选择赛道" />
                    </SelectTrigger>
                    <SelectContent>
                      {categories.map((cat) => (
                        <SelectItem key={cat} value={cat} className="text-xs">
                          {cat}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>

                  {/* Persona */}
                  <Select value={selectedPersona} onValueChange={setSelectedPersona}>
                    <SelectTrigger className="h-8 text-xs bg-sidebar-accent border-0">
                      <SelectValue placeholder="选择人设" />
                    </SelectTrigger>
                    <SelectContent>
                      {currentPersonas.map((p) => (
                        <SelectItem key={p.name} value={p.name} className="text-xs">
                          {p.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <Separator className="bg-sidebar-border" />

                {/* Temperature Slider */}
                <div className="space-y-3">
                  <label className="flex items-center gap-2 text-xs font-medium text-sidebar-foreground/70">
                    <Thermometer className="w-3.5 h-3.5" />
                    创意度
                    <span className="ml-auto font-mono">{temperature.toFixed(2)}</span>
                  </label>
                  <Slider
                    value={[temperature]}
                    onValueChange={(v) => setTemperature(v[0])}
                    min={0.3}
                    max={1.0}
                    step={0.05}
                    className="w-full"
                  />
                  <div className="flex justify-between text-[10px] text-sidebar-foreground/50">
                    <span>稳定</span>
                    <span>创意</span>
                  </div>
                </div>

                <Separator className="bg-sidebar-border" />

                {/* Hot Search Button */}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onOpenHotSearch}
                  className="w-full gap-2 text-xs"
                >
                  <Search className="w-3.5 h-3.5" />
                  热点搜索
                </Button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Collapsed Icons */}
        {collapsed && (
          <div className="flex flex-col items-center gap-2 p-2">
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={onOpenHotSearch}
                  className="h-10 w-10 text-sidebar-foreground hover:bg-sidebar-accent"
                >
                  <Search className="w-4 h-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="right">热点搜索</TooltipContent>
            </Tooltip>
          </div>
        )}

        {/* Footer */}
        <div className="mt-auto p-3 border-t border-sidebar-border">
          <div className={cn("flex items-center", collapsed ? "justify-center" : "justify-between")}>
            {!collapsed && (
              <span className="text-xs text-sidebar-foreground/50">v2.1</span>
            )}
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={toggleTheme}
                  className="h-8 w-8 text-sidebar-foreground hover:bg-sidebar-accent"
                >
                  {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
                </Button>
              </TooltipTrigger>
              <TooltipContent side="right">
                {isDark ? "浅色模式" : "深色模式"}
              </TooltipContent>
            </Tooltip>
          </div>
        </div>
      </motion.aside>
    </TooltipProvider>
  );
}
