// ---------------------------------------------------------------------------
// API Response Types
// ---------------------------------------------------------------------------

export interface UploadResponse {
  session_id: string;
  filename: string;
  file_size: number;
}

export interface JobResponse {
  job_id: string;
}

export interface ProgressEvent {
  status: 'processing' | 'complete' | 'error';
  percent: number;
  step: string;
  message: string;
  filename?: string;
  file_size?: number;
}

export interface HealthResponse {
  status: string;
  version: string;
}

// ---------------------------------------------------------------------------
// API Request Types
// ---------------------------------------------------------------------------

export interface ScanCopyRequest {
  dpi: number;
  color_mode: 'color' | 'grayscale' | 'bw';
  quality: number;
}

export interface ConvertRequest {
  ocr_engine: 'easyocr' | 'tesseract';
  ocr_lang: string;
  ocr_dpi: number;
  output_format: 'pdf' | 'text' | 'markdown';
}

export interface TranslateRequest {
  target_lang: string;
  source_lang?: string;
  output_format: 'pdf' | 'text' | 'markdown';
  translation_mode: 'structure_preserving' | 'flowing';
  translator: string;
  bilingual?: boolean;
  use_ocr: boolean;
  ocr_engine: 'easyocr' | 'tesseract';
  ocr_lang: string;
  ocr_dpi: number;
  openai_key: string;
  openai_model: string;
  ollama_model: string;
  ollama_host: string;
  trans_path: string;
  gcp_project: string;
}

// ---------------------------------------------------------------------------
// Config Types
// ---------------------------------------------------------------------------

export interface ConfigLanguages {
  target: Record<string, string>;
  ocr: Record<string, string>;
}

export interface ConfigTranslators {
  backends: Record<string, string>;
  openai_models: string[];
  ollama_models: string[];
}

export interface ConfigOptions {
  output_formats: Record<string, string>;
  translation_modes: Record<string, string>;
  workflow_modes: Record<string, string>;
  ocr_engines: Record<string, string>;
}

export interface ConfigSourceLanguages {
  languages: Record<string, string[]>;
}

// ---------------------------------------------------------------------------
// App-level Types
// ---------------------------------------------------------------------------

export type WorkflowMode = 'scan_copy' | 'convert' | 'translate';

export type AppStatus = 'idle' | 'uploading' | 'processing' | 'complete' | 'error';
