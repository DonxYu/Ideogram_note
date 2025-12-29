/**
 * Backend API Client
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8501";

// ========== Types ==========

export interface TopicItem {
  title: string;
  source: string;
  summary: string;
  outline: string[];
  why_hot: string;
}

export interface AnalyzeResponse {
  topics: TopicItem[];
  source: "websearch" | "fallback" | "error";
}

export interface ImageDesign {
  index: number;
  description: string;
  prompt: string;
  sentiment?: string;
  cover_text?: string;
}

export interface VisualScene {
  scene_index: number;
  narration: string;
  description: string;
  sentiment: string;
  prompt: string;
}

export interface Diagram {
  index: number;
  title: string;
  description: string;
  diagram_type: "architecture" | "flow" | "comparison";
  prompt: string;
}

export interface GenerateResponse {
  titles: string[];
  content: string;
  image_designs?: ImageDesign[];
  visual_scenes?: VisualScene[];
  diagrams?: Diagram[];
}

export interface MediaResult {
  index: number;
  path: string | null;
  url: string | null;
  error: string | null;
}

export interface BatchMediaResponse {
  results: MediaResult[];
  success_count: number;
  total: number;
}

export interface VoiceOption {
  label: string;
  value: string;
}

export interface ModelOption {
  label: string;
  value: string;
}

export interface PersonaItem {
  name: string;
  prompt: string;
}

export interface PersonaCategory {
  category: string;
  personas: PersonaItem[];
}

export interface HealthResponse {
  status: string;
  openrouter: boolean;
  replicate: boolean;
  ark: boolean;
  volc_tts: boolean;
}

// ========== Step-by-Step Types ==========

export interface OutlineResponse {
  titles: string[];
  outline: string[];
}

export interface ContentResponse {
  content: string;
}

export interface VisualsResponse {
  image_designs: ImageDesign[];
  global_style?: string;
}

// ========== API Functions ==========

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || "API request failed");
  }

  return res.json();
}

// Health Check
export async function checkHealth(): Promise<HealthResponse> {
  return fetchAPI<HealthResponse>("/health");
}

// Topics
export async function analyzeTopics(keyword: string, mode: "websearch" | "llm" = "websearch"): Promise<AnalyzeResponse> {
  return fetchAPI<AnalyzeResponse>("/api/topics/analyze", {
    method: "POST",
    body: JSON.stringify({ keyword, mode }),
  });
}

// Step 1: Create Outline
export async function createOutline(params: {
  topic: string;
  persona?: string;
  search_data?: any;
  model_name?: string;
  temperature?: number;
}): Promise<OutlineResponse> {
  return fetchAPI<OutlineResponse>("/api/content/step/outline", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

// Step 2: Create Content
export async function createContentStep(params: {
  topic: string;
  outline: string[];
  titles: string[];
  persona?: string;
  search_data?: any;
  reference_url?: string;
  model_name?: string;
  temperature?: number;
}): Promise<ContentResponse> {
  return fetchAPI<ContentResponse>("/api/content/step/content", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

// Step 3: Create Visuals
export async function createVisuals(params: {
  topic: string;
  content: string;
  model_name?: string;
  temperature?: number;
  global_style?: string;
}): Promise<VisualsResponse> {
  return fetchAPI<VisualsResponse>("/api/content/step/visuals", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

// Full Generation (Legacy / Video Mode)
export async function generateContent(params: {
  topic: string;
  persona?: string;
  reference_url?: string;
  mode: "image" | "video" | "wechat";
  model_name?: string;
  outline?: string[];
  temperature?: number;
}): Promise<GenerateResponse> {
  // Rename model_name to llm_model for API compatibility
  const { model_name, ...rest } = params;
  return fetchAPI<GenerateResponse>("/api/content/generate", {
    method: "POST",
    body: JSON.stringify({ ...rest, llm_model: model_name }),
  });
}

// Image Generation
export async function generateImages(params: {
  scenes: Array<{ prompt: string; sentiment?: string }>;
  provider?: string;
  topic?: string;
  use_schnell?: boolean;  // true: flux-schnell (快), false: flux-dev (高质量)
}): Promise<BatchMediaResponse> {
  return fetchAPI<BatchMediaResponse>("/api/media/images", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export async function generateSingleImage(params: {
  scene: { prompt: string; sentiment?: string };
  index: number;
  provider?: string;
  topic?: string;
  use_schnell?: boolean;
}): Promise<MediaResult> {
  return fetchAPI<MediaResult>("/api/media/images/single", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

// Audio Generation
export async function generateAudio(params: {
  scenes: Array<{ narration: string }>;
  provider?: string;
  voice?: string;
  topic?: string;
}): Promise<BatchMediaResponse> {
  return fetchAPI<BatchMediaResponse>("/api/media/audio", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export async function generateSingleAudio(params: {
  scene: { narration: string };
  index: number;
  provider?: string;
  voice?: string;
  topic?: string;
}): Promise<MediaResult> {
  return fetchAPI<MediaResult>("/api/media/audio/single", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

// Video
export async function createVideo(params: {
  image_paths: string[];
  audio_paths: string[];
  scenes?: Array<{ narration: string }>;
  bgm_path?: string;
  bgm_volume?: number;
  topic?: string;
}): Promise<{
  video_path: string | null;
  video_url: string | null;
  srt_path: string | null;
  srt_url: string | null;
  duration: number;
  error: string | null;
}> {
  return fetchAPI("/api/video/create", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export async function getBgmList(): Promise<{
  bgm_list: Array<{ name: string; filename: string; path: string }>;
}> {
  return fetchAPI("/api/video/bgm");
}

// Config
export async function getModels(): Promise<{ models: ModelOption[] }> {
  return fetchAPI("/api/config/models");
}

export async function getVoices(): Promise<{
  edge: VoiceOption[];
  volcengine: VoiceOption[];
}> {
  return fetchAPI("/api/config/voices");
}

export async function getPersonas(): Promise<{ categories: PersonaCategory[] }> {
  return fetchAPI("/api/config/personas");
}

// SSE Stream for images
export function streamImages(
  params: {
    scenes: Array<{ prompt: string; sentiment?: string }>;
    provider?: string;
    topic?: string;
    use_schnell?: boolean;
  },
  onProgress: (data: {
    type: "progress" | "result" | "done";
    index?: number;
    total?: number;
    status?: string;
    path?: string;
    url?: string;
    error?: string;
  }) => void
): () => void {
  const controller = new AbortController();

  fetch(`${API_BASE}/api/media/images/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
    signal: controller.signal,
  })
    .then(async (response) => {
      const reader = response.body?.getReader();
      if (!reader) return;

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              onProgress(data);
            } catch {
              // Ignore parse errors
            }
          }
        }
      }
    })
    .catch((err) => {
      if (err.name !== "AbortError") {
        console.error("Stream error:", err);
      }
    });

  return () => controller.abort();
}

// Export Note to Obsidian
export interface ExportResponse {
  success: boolean;
  file_path: string | null;
  error: string | null;
}

export async function exportNote(params: {
  topic: string;
  title: string;
  content: string;
  image_urls?: string[];
  tags?: string[];
}): Promise<ExportResponse> {
  return fetchAPI<ExportResponse>("/api/content/export", {
    method: "POST",
    body: JSON.stringify(params),
  });
}
