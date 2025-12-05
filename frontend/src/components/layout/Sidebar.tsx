"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronLeft,
  ChevronRight,
  Sparkles,
  FileText,
  Video,
  Settings,
  Palette,
  Mic2,
  Brain,
  Moon,
  Sun,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
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

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const [isDark, setIsDark] = useState(false);
  const {
    mode,
    setMode,
    selectedModel,
    setSelectedModel,
    imageProvider,
    setImageProvider,
    ttsProvider,
    setTtsProvider,
    selectedVoice,
    setSelectedVoice,
    availableModels,
    availableVoices,
  } = useWorkflowStore();

  const toggleTheme = () => {
    setIsDark(!isDark);
    document.documentElement.classList.toggle("dark");
  };

  const currentVoices = ttsProvider === "edge" ? availableVoices.edge : availableVoices.volcengine;

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

                {/* Image Provider */}
                <div className="space-y-2">
                  <label className="flex items-center gap-2 text-xs font-medium text-sidebar-foreground/70">
                    <Palette className="w-3.5 h-3.5" />
                    生图服务
                  </label>
                  <Select
                    value={imageProvider}
                    onValueChange={(v) => setImageProvider(v as "replicate" | "volcengine")}
                  >
                    <SelectTrigger className="h-8 text-xs bg-sidebar-accent border-0">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="replicate" className="text-xs">
                        Replicate (二次元)
                      </SelectItem>
                      <SelectItem value="volcengine" className="text-xs">
                        火山引擎 (Seedream)
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* TTS Provider - Only in video mode */}
                {mode === "video" && (
                  <>
                    <div className="space-y-2">
                      <label className="flex items-center gap-2 text-xs font-medium text-sidebar-foreground/70">
                        <Mic2 className="w-3.5 h-3.5" />
                        TTS 服务
                      </label>
                      <Select
                        value={ttsProvider}
                        onValueChange={(v) => setTtsProvider(v as "edge" | "volcengine")}
                      >
                        <SelectTrigger className="h-8 text-xs bg-sidebar-accent border-0">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="edge" className="text-xs">
                            Edge TTS (免费)
                          </SelectItem>
                          <SelectItem value="volcengine" className="text-xs">
                            火山引擎 TTS
                          </SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Voice Selection */}
                    <div className="space-y-2">
                      <label className="flex items-center gap-2 text-xs font-medium text-sidebar-foreground/70">
                        语音角色
                      </label>
                      <Select value={selectedVoice} onValueChange={setSelectedVoice}>
                        <SelectTrigger className="h-8 text-xs bg-sidebar-accent border-0">
                          <SelectValue placeholder="选择语音" />
                        </SelectTrigger>
                        <SelectContent>
                          {currentVoices.length > 0 ? (
                            currentVoices.map((v) => (
                              <SelectItem key={v.value} value={v.value} className="text-xs">
                                {v.label}
                              </SelectItem>
                            ))
                          ) : (
                            <>
                              <SelectItem value="zh-CN-XiaoxiaoNeural" className="text-xs">
                                小晓 (女)
                              </SelectItem>
                              <SelectItem value="zh-CN-YunyangNeural" className="text-xs">
                                云扬 (男)
                              </SelectItem>
                            </>
                          )}
                        </SelectContent>
                      </Select>
                    </div>
                  </>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Footer */}
        <div className="mt-auto p-3 border-t border-sidebar-border">
          <div className={cn("flex items-center", collapsed ? "justify-center" : "justify-between")}>
            {!collapsed && (
              <span className="text-xs text-sidebar-foreground/50">v2.0</span>
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

