/**
 * Zustand Store - Workflow State Management (Simplified)
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";
import type {
  TopicItem,
  GenerateResponse,
  VoiceOption,
  ModelOption,
  PersonaCategory,
} from "@/lib/api";

// ========== Types ==========

export type WorkflowMode = "image" | "video" | "wechat";

export interface WorkflowState {
  // Mode
  mode: WorkflowMode;

  // Config
  selectedModel: string;
  temperature: number;

  // Persona
  selectedCategory: string;
  selectedPersona: string;

  // Topic (from hot search)
  keyword: string;
  topics: TopicItem[];
  topicsSource: string;
  selectedTopic: TopicItem | null;

  // Generated Content
  generatedContent: GenerateResponse | null;
  selectedTitleIndex: number;

  // Loading States
  isAnalyzing: boolean;

  // Config Data (from API)
  availableModels: ModelOption[];
  availableVoices: { edge: VoiceOption[]; volcengine: VoiceOption[] };
  availablePersonas: PersonaCategory[];
}

export interface WorkflowActions {
  // Mode
  setMode: (mode: WorkflowMode) => void;

  // Config
  setSelectedModel: (model: string) => void;
  setTemperature: (temp: number) => void;

  // Persona
  setSelectedCategory: (category: string) => void;
  setSelectedPersona: (persona: string) => void;

  // Topic
  setKeyword: (keyword: string) => void;
  setTopics: (topics: TopicItem[], source: string) => void;
  selectTopic: (topic: TopicItem | null) => void;

  // Content
  setGeneratedContent: (content: GenerateResponse | null) => void;
  setSelectedTitleIndex: (index: number) => void;

  // Loading States
  setIsAnalyzing: (value: boolean) => void;

  // Config Data
  setAvailableModels: (models: ModelOption[]) => void;
  setAvailableVoices: (voices: { edge: VoiceOption[]; volcengine: VoiceOption[] }) => void;
  setAvailablePersonas: (personas: PersonaCategory[]) => void;

  // Utility
  resetAll: () => void;
}

// ========== Initial State ==========

const initialState: WorkflowState = {
  mode: "image",

  selectedModel: "deepseek/deepseek-chat",
  temperature: 0.7,

  selectedCategory: "职场",
  selectedPersona: "职场清醒女王",

  keyword: "",
  topics: [],
  topicsSource: "",
  selectedTopic: null,

  generatedContent: null,
  selectedTitleIndex: 0,

  isAnalyzing: false,

  availableModels: [],
  availableVoices: { edge: [], volcengine: [] },
  availablePersonas: [],
};

// ========== Store ==========

export const useWorkflowStore = create<WorkflowState & WorkflowActions>()(
  persist(
    (set, get) => ({
      ...initialState,

      // Mode
      setMode: (mode) => {
        set({ mode, generatedContent: null });
        
        // 切换模式时自动调整默认人设
        if (mode === "wechat") {
          set({
            selectedCategory: "硬核技术/AI",
            selectedPersona: "全栈AI架构师",
          });
        } else {
          set({
            selectedCategory: "职场",
            selectedPersona: "职场清醒女王",
          });
        }
      },

      // Config
      setSelectedModel: (model) => set({ selectedModel: model }),
      setTemperature: (temp) => set({ temperature: temp }),

      // Persona
      setSelectedCategory: (category) => set({ selectedCategory: category, selectedPersona: "" }),
      setSelectedPersona: (persona) => set({ selectedPersona: persona }),

      // Topic
      setKeyword: (keyword) => set({ keyword }),
      setTopics: (topics, source) => set({ topics, topicsSource: source }),
      selectTopic: (topic) => set({ selectedTopic: topic }),

      // Content
      setGeneratedContent: (content) => set({ generatedContent: content, selectedTitleIndex: 0 }),
      setSelectedTitleIndex: (index) => set({ selectedTitleIndex: index }),

      // Loading States
      setIsAnalyzing: (value) => set({ isAnalyzing: value }),

      // Config Data
      setAvailableModels: (models) => set({ availableModels: models }),
      setAvailableVoices: (voices) => set({ availableVoices: voices }),
      setAvailablePersonas: (personas) => set({ availablePersonas: personas }),

      // Utility
      resetAll: () => set(initialState),
    }),
    {
      name: "workflow-storage-v2",
      partialize: (state) => ({
        mode: state.mode,
        selectedModel: state.selectedModel,
        temperature: state.temperature,
        selectedCategory: state.selectedCategory,
        selectedPersona: state.selectedPersona,
      }),
    }
  )
);
