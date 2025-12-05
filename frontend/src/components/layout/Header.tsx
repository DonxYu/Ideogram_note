"use client";

import { useWorkflowStore } from "@/store/workflow";
import { Badge } from "@/components/ui/badge";
import { FileText, Video } from "lucide-react";

export function Header() {
  const { mode, selectedTopic, generatedContent } = useWorkflowStore();

  const getStatusText = () => {
    if (generatedContent) return "内容已生成";
    if (selectedTopic) return "已选话题";
    return "等待选题";
  };

  return (
    <header className="h-14 border-b border-border flex items-center justify-between px-6 bg-background/80 backdrop-blur-sm sticky top-0 z-10">
      <div className="flex items-center gap-3">
        <h1 className="text-lg font-semibold text-foreground">
          {mode === "video" ? "视频脚本工作流" : "图文笔记工作流"}
        </h1>
        <Badge variant="secondary" className="font-normal">
          {mode === "video" ? (
            <Video className="w-3 h-3 mr-1" />
          ) : (
            <FileText className="w-3 h-3 mr-1" />
          )}
          {mode === "video" ? "视频模式" : "图文模式"}
        </Badge>
      </div>

      <div className="flex items-center gap-4">
        <span className="text-sm text-muted-foreground">{getStatusText()}</span>
        {selectedTopic && (
          <Badge variant="outline" className="max-w-[200px] truncate">
            {selectedTopic.title}
          </Badge>
        )}
      </div>
    </header>
  );
}

