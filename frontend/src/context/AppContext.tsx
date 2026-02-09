import {
  createContext,
  useContext,
  useReducer,
  type Dispatch,
  type ReactNode,
} from 'react';

import type {
  WorkflowMode,
  AppStatus,
  ProgressEvent,
  ConfigLanguages,
  ConfigTranslators,
  ConfigOptions,
} from '../lib/types';

import {
  DEFAULT_DPI,
  DEFAULT_QUALITY,
  DEFAULT_COLOR_MODE,
  DEFAULT_OCR_ENGINE,
  DEFAULT_OCR_LANG,
  DEFAULT_OCR_DPI,
  DEFAULT_OUTPUT_FORMAT,
  DEFAULT_TRANSLATION_MODE,
  DEFAULT_TARGET_LANG,
  DEFAULT_TRANSLATOR,
  DEFAULT_OPENAI_MODEL,
  DEFAULT_OLLAMA_MODEL,
  DEFAULT_OLLAMA_HOST,
} from '../lib/constants';

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

export interface AppState {
  // Session
  sessionId: string | null;
  filename: string | null;
  fileSize: number | null;

  // Workflow
  workflowMode: WorkflowMode;

  // Status
  status: AppStatus;
  progress: ProgressEvent | null;
  errorMessage: string | null;

  // Scan-copy settings
  dpi: number;
  colorMode: 'color' | 'grayscale' | 'bw';
  quality: number;

  // OCR settings
  useOcr: boolean;
  ocrEngine: 'easyocr' | 'tesseract';
  ocrLang: string;
  ocrDpi: number;

  // Translation settings
  targetLang: string;
  outputFormat: 'pdf' | 'text' | 'markdown';
  translationMode: 'structure_preserving' | 'flowing';
  translator: string;

  // Backend-specific settings
  openaiKey: string;
  openaiModel: string;
  ollamaModel: string;
  ollamaHost: string;
  transPath: string;
  gcpProject: string;

  // Server config (fetched once)
  config: {
    languages: ConfigLanguages | null;
    translators: ConfigTranslators | null;
    options: ConfigOptions | null;
  };

  // Result
  resultFilename: string | null;
  resultFileSize: number | null;
}

const initialState: AppState = {
  sessionId: null,
  filename: null,
  fileSize: null,

  workflowMode: 'translate',

  status: 'idle',
  progress: null,
  errorMessage: null,

  dpi: DEFAULT_DPI,
  colorMode: DEFAULT_COLOR_MODE,
  quality: DEFAULT_QUALITY,

  useOcr: false,
  ocrEngine: DEFAULT_OCR_ENGINE,
  ocrLang: DEFAULT_OCR_LANG,
  ocrDpi: DEFAULT_OCR_DPI,

  targetLang: DEFAULT_TARGET_LANG,
  outputFormat: DEFAULT_OUTPUT_FORMAT,
  translationMode: DEFAULT_TRANSLATION_MODE,
  translator: DEFAULT_TRANSLATOR,

  openaiKey: '',
  openaiModel: DEFAULT_OPENAI_MODEL,
  ollamaModel: DEFAULT_OLLAMA_MODEL,
  ollamaHost: DEFAULT_OLLAMA_HOST,
  transPath: '',
  gcpProject: '',

  config: {
    languages: null,
    translators: null,
    options: null,
  },

  resultFilename: null,
  resultFileSize: null,
};

// ---------------------------------------------------------------------------
// Actions
// ---------------------------------------------------------------------------

export type AppAction =
  | {
      type: 'SET_SESSION';
      payload: { sessionId: string; filename: string; fileSize: number };
    }
  | { type: 'CLEAR_SESSION' }
  | { type: 'SET_WORKFLOW_MODE'; payload: WorkflowMode }
  | {
      type: 'SET_STATUS';
      payload: { status: AppStatus; errorMessage?: string };
    }
  | { type: 'SET_PROGRESS'; payload: ProgressEvent | null }
  | { type: 'UPDATE_SETTINGS'; payload: Partial<AppState> }
  | { type: 'SET_CONFIG_LANGUAGES'; payload: ConfigLanguages }
  | { type: 'SET_CONFIG_TRANSLATORS'; payload: ConfigTranslators }
  | { type: 'SET_CONFIG_OPTIONS'; payload: ConfigOptions }
  | {
      type: 'SET_RESULT';
      payload: { filename: string; fileSize: number };
    }
  | { type: 'RESET' };

// ---------------------------------------------------------------------------
// Reducer
// ---------------------------------------------------------------------------

function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'SET_SESSION':
      return {
        ...state,
        sessionId: action.payload.sessionId,
        filename: action.payload.filename,
        fileSize: action.payload.fileSize,
        status: 'idle',
        errorMessage: null,
        progress: null,
        resultFilename: null,
        resultFileSize: null,
      };

    case 'CLEAR_SESSION':
      return {
        ...state,
        sessionId: null,
        filename: null,
        fileSize: null,
        status: 'idle',
        errorMessage: null,
        progress: null,
        resultFilename: null,
        resultFileSize: null,
      };

    case 'SET_WORKFLOW_MODE':
      return { ...state, workflowMode: action.payload };

    case 'SET_STATUS':
      return {
        ...state,
        status: action.payload.status,
        errorMessage: action.payload.errorMessage ?? state.errorMessage,
      };

    case 'SET_PROGRESS':
      return { ...state, progress: action.payload };

    case 'UPDATE_SETTINGS': {
      // Only merge known settings keys -- prevents accidentally overwriting
      // derived state such as sessionId or config.
      const {
        dpi,
        colorMode,
        quality,
        useOcr,
        ocrEngine,
        ocrLang,
        ocrDpi,
        targetLang,
        outputFormat,
        translationMode,
        translator,
        openaiKey,
        openaiModel,
        ollamaModel,
        ollamaHost,
        transPath,
        gcpProject,
      } = action.payload;

      return {
        ...state,
        ...(dpi !== undefined && { dpi }),
        ...(colorMode !== undefined && { colorMode }),
        ...(quality !== undefined && { quality }),
        ...(useOcr !== undefined && { useOcr }),
        ...(ocrEngine !== undefined && { ocrEngine }),
        ...(ocrLang !== undefined && { ocrLang }),
        ...(ocrDpi !== undefined && { ocrDpi }),
        ...(targetLang !== undefined && { targetLang }),
        ...(outputFormat !== undefined && { outputFormat }),
        ...(translationMode !== undefined && { translationMode }),
        ...(translator !== undefined && { translator }),
        ...(openaiKey !== undefined && { openaiKey }),
        ...(openaiModel !== undefined && { openaiModel }),
        ...(ollamaModel !== undefined && { ollamaModel }),
        ...(ollamaHost !== undefined && { ollamaHost }),
        ...(transPath !== undefined && { transPath }),
        ...(gcpProject !== undefined && { gcpProject }),
      };
    }

    case 'SET_CONFIG_LANGUAGES':
      return {
        ...state,
        config: { ...state.config, languages: action.payload },
      };

    case 'SET_CONFIG_TRANSLATORS':
      return {
        ...state,
        config: { ...state.config, translators: action.payload },
      };

    case 'SET_CONFIG_OPTIONS':
      return {
        ...state,
        config: { ...state.config, options: action.payload },
      };

    case 'SET_RESULT':
      return {
        ...state,
        resultFilename: action.payload.filename,
        resultFileSize: action.payload.fileSize,
        status: 'complete',
      };

    case 'RESET':
      return { ...initialState, config: state.config };

    default:
      return state;
  }
}

// ---------------------------------------------------------------------------
// Contexts
// ---------------------------------------------------------------------------

const AppStateContext = createContext<AppState | null>(null);
const AppDispatchContext = createContext<Dispatch<AppAction> | null>(null);

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  return (
    <AppStateContext.Provider value={state}>
      <AppDispatchContext.Provider value={dispatch}>
        {children}
      </AppDispatchContext.Provider>
    </AppStateContext.Provider>
  );
}

// ---------------------------------------------------------------------------
// Hooks
// ---------------------------------------------------------------------------

export function useAppState(): AppState {
  const ctx = useContext(AppStateContext);
  if (ctx === null) {
    throw new Error('useAppState must be used within an AppProvider');
  }
  return ctx;
}

export function useAppDispatch(): Dispatch<AppAction> {
  const ctx = useContext(AppDispatchContext);
  if (ctx === null) {
    throw new Error('useAppDispatch must be used within an AppProvider');
  }
  return ctx;
}
