/**
 * Zustand Store - Workflow State Management
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";
import type {
  TopicItem,
  GenerateResponse,
  MediaResult,
  VoiceOption,
  ModelOption,
  PersonaCategory,
} from "@/lib/api";

// ========== Types ==========

export type WorkflowMode = "image" | "video";
export type WorkflowStep = "topic" | "persona" | "preview" | "studio";

export interface WorkflowState {
  // Mode & Navigation
  mode: WorkflowMode;
  currentStep: WorkflowStep;

  // Config
  selectedModel: string;
  imageProvider: "replicate" | "volcengine";
  animeModel: "anything-v4" | "flux-anime";
  ttsProvider: "edge" | "volcengine";
  selectedVoice: string;

  // Step 1: Topic Selection
  keyword: string;
  topics: TopicItem[];
  topicsSource: string;
  selectedTopic: TopicItem | null;

  // Step 2: Persona Config
  selectedCategory: string;
  selectedPersona: string;
  customPersona: string;
  referenceUrl: string;

  // Step 3: Content Preview
  generatedContent: GenerateResponse | null;
  selectedTitleIndex: number;

  // Step 4: Media Studio
  imageResults: MediaResult[];
  audioResults: MediaResult[];
  videoPath: string | null;
  videoUrl: string | null;
  srtPath: string | null;
  selectedBgm: string | null;
  bgmVolume: number;

  // Loading States
  isAnalyzing: boolean;
  isGenerating: boolean;
  isGeneratingImages: boolean;
  isGeneratingAudio: boolean;
  isCreatingVideo: boolean;

  // Config Data (from API)
  availableModels: ModelOption[];
  availableVoices: { edge: VoiceOption[]; volcengine: VoiceOption[] };
  availablePersonas: PersonaCategory[];
  availableBgm: Array<{ name: string; filename: string; path: string }>;
}

export interface WorkflowActions {
  // Mode & Navigation
  setMode: (mode: WorkflowMode) => void;
  setStep: (step: WorkflowStep) => void;

  // Config
  setSelectedModel: (model: string) => void;
  setImageProvider: (provider: "replicate" | "volcengine") => void;
  setAnimeModel: (model: "anything-v4" | "flux-anime") => void;
  setTtsProvider: (provider: "edge" | "volcengine") => void;
  setSelectedVoice: (voice: string) => void;

  // Step 1
  setKeyword: (keyword: string) => void;
  setTopics: (topics: TopicItem[], source: string) => void;
  selectTopic: (topic: TopicItem | null) => void;

  // Step 2
  setSelectedCategory: (category: string) => void;
  setSelectedPersona: (persona: string) => void;
  setCustomPersona: (persona: string) => void;
  setReferenceUrl: (url: string) => void;

  // Step 3
  setGeneratedContent: (content: GenerateResponse | null) => void;
  setSelectedTitleIndex: (index: number) => void;

  // Step 4
  setImageResults: (results: MediaResult[]) => void;
  updateImageResult: (index: number, result: MediaResult) => void;
  setAudioResults: (results: MediaResult[]) => void;
  updateAudioResult: (index: number, result: MediaResult) => void;
  setVideoResult: (path: string | null, url: string | null, srtPath: string | null) => void;
  setSelectedBgm: (bgm: string | null) => void;
  setBgmVolume: (volume: number) => void;

  // Loading States
  setIsAnalyzing: (value: boolean) => void;
  setIsGenerating: (value: boolean) => void;
  setIsGeneratingImages: (value: boolean) => void;
  setIsGeneratingAudio: (value: boolean) => void;
  setIsCreatingVideo: (value: boolean) => void;

  // Config Data
  setAvailableModels: (models: ModelOption[]) => void;
  setAvailableVoices: (voices: { edge: VoiceOption[]; volcengine: VoiceOption[] }) => void;
  setAvailablePersonas: (personas: PersonaCategory[]) => void;
  setAvailableBgm: (bgm: Array<{ name: string; filename: string; path: string }>) => void;

  // Utility
  resetDownstream: (fromStep: WorkflowStep) => void;
  resetAll: () => void;
}

// ========== Initial State ==========

const initialState: WorkflowState = {
  mode: "image",
  currentStep: "topic",

  selectedModel: "deepseek/deepseek-chat",
  imageProvider: "replicate",
  animeModel: "anything-v4",
  ttsProvider: "edge",
  selectedVoice: "zh-CN-XiaoxiaoNeural",

  keyword: "",
  topics: [],
  topicsSource: "",
  selectedTopic: null,

  selectedCategory: "",
  selectedPersona: "",
  customPersona: "",
  referenceUrl: "",

  generatedContent: null,
  selectedTitleIndex: 0,

  imageResults: [],
  audioResults: [],
  videoPath: null,
  videoUrl: null,
  srtPath: null,
  selectedBgm: null,
  bgmVolume: 0.12,

  isAnalyzing: false,
  isGenerating: false,
  isGeneratingImages: false,
  isGeneratingAudio: false,
  isCreatingVideo: false,

  availableModels: [],
  availableVoices: { edge: [], volcengine: [] },
  availablePersonas: [],
  availableBgm: [],
};

// ========== Store ==========

export const useWorkflowStore = create<WorkflowState & WorkflowActions>()(
  persist(
    (set, get) => ({
      ...initialState,

      // Mode & Navigation
      setMode: (mode) => {
        set({ mode });
        get().resetDownstream("topic");
      },
      setStep: (step) => set({ currentStep: step }),

      // Config
      setSelectedModel: (model) => set({ selectedModel: model }),
      setImageProvider: (provider) => set({ imageProvider: provider }),
      setAnimeModel: (model) => set({ animeModel: model }),
      setTtsProvider: (provider) => set({ ttsProvider: provider }),
      setSelectedVoice: (voice) => set({ selectedVoice: voice }),

      // Step 1
      setKeyword: (keyword) => set({ keyword }),
      setTopics: (topics, source) => set({ topics, topicsSource: source }),
      selectTopic: (topic) => {
        set({ selectedTopic: topic });
        if (topic) {
          get().resetDownstream("persona");
        }
      },

      // Step 2
      setSelectedCategory: (category) => set({ selectedCategory: category, selectedPersona: "" }),
      setSelectedPersona: (persona) => set({ selectedPersona: persona }),
      setCustomPersona: (persona) => set({ customPersona: persona }),
      setReferenceUrl: (url) => set({ referenceUrl: url }),

      // Step 3
      setGeneratedContent: (content) => {
        set({ generatedContent: content, selectedTitleIndex: 0 });
        if (content) {
          // Initialize media results arrays
          const count = content.visual_scenes?.length || content.image_designs?.length || 0;
          set({
            imageResults: Array(count).fill(null).map((_, i) => ({ index: i, path: null, url: null, error: null })),
            audioResults: Array(count).fill(null).map((_, i) => ({ index: i, path: null, url: null, error: null })),
          });
        }
      },
      setSelectedTitleIndex: (index) => set({ selectedTitleIndex: index }),

      // Step 4
      setImageResults: (results) => set({ imageResults: results }),
      updateImageResult: (index, result) =>
        set((state) => ({
          imageResults: state.imageResults.map((r, i) => (i === index ? result : r)),
        })),
      setAudioResults: (results) => set({ audioResults: results }),
      updateAudioResult: (index, result) =>
        set((state) => ({
          audioResults: state.audioResults.map((r, i) => (i === index ? result : r)),
        })),
      setVideoResult: (path, url, srtPath) =>
        set({ videoPath: path, videoUrl: url, srtPath }),
      setSelectedBgm: (bgm) => set({ selectedBgm: bgm }),
      setBgmVolume: (volume) => set({ bgmVolume: volume }),

      // Loading States
      setIsAnalyzing: (value) => set({ isAnalyzing: value }),
      setIsGenerating: (value) => set({ isGenerating: value }),
      setIsGeneratingImages: (value) => set({ isGeneratingImages: value }),
      setIsGeneratingAudio: (value) => set({ isGeneratingAudio: value }),
      setIsCreatingVideo: (value) => set({ isCreatingVideo: value }),

      // Config Data
      setAvailableModels: (models) => set({ availableModels: models }),
      setAvailableVoices: (voices) => set({ availableVoices: voices }),
      setAvailablePersonas: (personas) => set({ availablePersonas: personas }),
      setAvailableBgm: (bgm) => set({ availableBgm: bgm }),

      // Utility
      resetDownstream: (fromStep) => {
        const steps: WorkflowStep[] = ["topic", "persona", "preview", "studio"];
        const idx = steps.indexOf(fromStep);

        if (idx <= 0) {
          // Reset from topic - clear everything
          set({
            selectedTopic: null,
            generatedContent: null,
            imageResults: [],
            audioResults: [],
            videoPath: null,
            videoUrl: null,
            srtPath: null,
          });
        } else if (idx <= 1) {
          // Reset from persona - clear content and media
          set({
            generatedContent: null,
            imageResults: [],
            audioResults: [],
            videoPath: null,
            videoUrl: null,
            srtPath: null,
          });
        } else if (idx <= 2) {
          // Reset from preview - clear media
          set({
            imageResults: [],
            audioResults: [],
            videoPath: null,
            videoUrl: null,
            srtPath: null,
          });
        }
      },
      resetAll: () => set(initialState),
    }),
    {
      name: "workflow-storage",
      partialize: (state) => ({
        // Only persist user selections, not loading states
        mode: state.mode,
        selectedModel: state.selectedModel,
        imageProvider: state.imageProvider,
        animeModel: state.animeModel,
        ttsProvider: state.ttsProvider,
        selectedVoice: state.selectedVoice,
        keyword: state.keyword,
        topics: state.topics,
        selectedTopic: state.selectedTopic,
        selectedCategory: state.selectedCategory,
        selectedPersona: state.selectedPersona,
        generatedContent: state.generatedContent,
        bgmVolume: state.bgmVolume,
      }),
    }
  )
);

