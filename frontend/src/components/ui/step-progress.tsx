"use client";

import { motion } from "framer-motion";
import { Check, Loader2, X } from "lucide-react";
import { cn } from "@/lib/utils";

export interface Step {
  id: string;
  label: string;
  status: "pending" | "loading" | "completed" | "error";
  estimatedTime?: number; // seconds
}

interface StepProgressProps {
  steps: Step[];
  className?: string;
}

export function StepProgress({ steps, className }: StepProgressProps) {
  return (
    <div className={cn("space-y-4", className)}>
      {steps.map((step, index) => {
        const isLast = index === steps.length - 1;
        
        return (
          <div key={step.id} className="relative flex items-start gap-4">
            {/* Connecting Line */}
            {!isLast && (
              <div
                className={cn(
                  "absolute left-3 top-8 w-0.5 h-full",
                  step.status === "completed"
                    ? "bg-primary"
                    : "bg-border"
                )}
              />
            )}

            {/* Status Icon */}
            <div className="relative z-10 flex-shrink-0">
              {step.status === "pending" && (
                <div className="w-6 h-6 rounded-full border-2 border-border bg-background flex items-center justify-center">
                  <div className="w-2 h-2 rounded-full bg-muted" />
                </div>
              )}

              {step.status === "loading" && (
                <motion.div
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  className="w-6 h-6 rounded-full border-2 border-primary bg-primary/10 flex items-center justify-center"
                >
                  <Loader2 className="w-3 h-3 text-primary animate-spin" />
                </motion.div>
              )}

              {step.status === "completed" && (
                <motion.div
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  className="w-6 h-6 rounded-full bg-primary flex items-center justify-center"
                >
                  <Check className="w-3 h-3 text-primary-foreground" />
                </motion.div>
              )}

              {step.status === "error" && (
                <motion.div
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  className="w-6 h-6 rounded-full bg-destructive flex items-center justify-center"
                >
                  <X className="w-3 h-3 text-destructive-foreground" />
                </motion.div>
              )}
            </div>

            {/* Step Label */}
            <div className="flex-1 pt-0.5">
              <div className="flex items-center justify-between">
                <span
                  className={cn(
                    "text-sm font-medium",
                    step.status === "pending" && "text-muted-foreground",
                    step.status === "loading" && "text-primary",
                    step.status === "completed" && "text-foreground",
                    step.status === "error" && "text-destructive"
                  )}
                >
                  {step.label}
                </span>
                
                {step.status === "loading" && step.estimatedTime && (
                  <span className="text-xs text-muted-foreground">
                    预计 {step.estimatedTime}s
                  </span>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

