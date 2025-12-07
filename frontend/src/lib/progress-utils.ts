/**
 * Progress simulation utilities
 * 模拟进度条，用于在等待API响应时给用户提供视觉反馈
 */

import type { Step } from "@/components/ui/step-progress";

export interface ProgressConfig {
  steps: Step[];
  onStepChange: (steps: Step[]) => void;
  actualTask: () => Promise<void>;
  onCancel?: () => void;
}

/**
 * 模拟步骤进度
 * 按顺序执行每个步骤，根据 estimatedTime 延迟
 * 如果实际任务提前完成，立即完成所有步骤
 */
export function simulateStepProgress(config: ProgressConfig): {
  promise: Promise<void>;
  cancel: () => void;
} {
  const { steps, onStepChange, actualTask, onCancel } = config;
  
  let cancelled = false;
  let taskCompleted = false;
  let taskError: Error | null = null;

  const cancel = () => {
    cancelled = true;
    onCancel?.();
  };

  const promise = new Promise<void>(async (resolve, reject) => {
    // 启动实际任务（在后台执行）
    const taskPromise = actualTask()
      .then(() => {
        taskCompleted = true;
      })
      .catch((error) => {
        taskError = error;
      });

    // 逐步执行模拟进度
    for (let i = 0; i < steps.length; i++) {
      if (cancelled) {
        // 用户取消
        const updatedSteps = steps.map((s, idx) => ({
          ...s,
          status: idx < i ? ("completed" as const) : ("pending" as const),
        }));
        onStepChange(updatedSteps);
        reject(new Error("User cancelled"));
        return;
      }

      // 更新当前步骤为 loading
      const loadingSteps = steps.map((s, idx) => ({
        ...s,
        status:
          idx < i
            ? ("completed" as const)
            : idx === i
            ? ("loading" as const)
            : ("pending" as const),
      }));
      onStepChange(loadingSteps);

      // 如果任务已完成，立即完成所有剩余步骤
      if (taskCompleted) {
        const completedSteps = steps.map((s) => ({
          ...s,
          status: "completed" as const,
        }));
        onStepChange(completedSteps);
        resolve();
        return;
      }

      // 如果任务出错，标记当前步骤为 error
      if (taskError) {
        const errorSteps = steps.map((s, idx) => ({
          ...s,
          status:
            idx < i
              ? ("completed" as const)
              : idx === i
              ? ("error" as const)
              : ("pending" as const),
        }));
        onStepChange(errorSteps);
        reject(taskError);
        return;
      }

      // 等待该步骤的预估时间
      const delay = steps[i].estimatedTime || 3;
      await sleep(delay * 1000);

      // 完成当前步骤
      const completedSteps = steps.map((s, idx) => ({
        ...s,
        status:
          idx <= i ? ("completed" as const) : ("pending" as const),
      }));
      onStepChange(completedSteps);
    }

    // 所有步骤完成后，等待实际任务完成
    try {
      await taskPromise;
      resolve();
    } catch (error) {
      reject(error);
    }
  });

  return { promise, cancel };
}

/**
 * Sleep helper
 */
function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * 创建默认步骤
 */
export function createDefaultSteps(labels: Array<{ label: string; time?: number }>): Step[] {
  return labels.map((item, index) => ({
    id: `step-${index}`,
    label: item.label,
    status: "pending",
    estimatedTime: item.time || 3,
  }));
}

