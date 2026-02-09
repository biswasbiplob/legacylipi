import { useCallback } from 'react';
import { useAppState, useAppDispatch } from '../context/AppContext';
import { startScanCopy, startConvert, startTranslate } from '../lib/api';
import type { ScanCopyRequest, ConvertRequest, TranslateRequest } from '../lib/types';
import { useProgress } from './useProgress';

export function useProcessing() {
  const state = useAppState();
  const dispatch = useAppDispatch();
  const { startListening } = useProgress();

  const startProcessing = useCallback(async (): Promise<void> => {
    const { sessionId } = state;
    if (!sessionId) {
      dispatch({
        type: 'SET_STATUS',
        payload: { status: 'error', errorMessage: 'No active session. Please upload a file first.' },
      });
      return;
    }

    try {
      switch (state.workflowMode) {
        case 'scan_copy': {
          const config: ScanCopyRequest = {
            dpi: state.dpi,
            color_mode: state.colorMode,
            quality: state.quality,
          };
          await startScanCopy(sessionId, config);
          break;
        }

        case 'convert': {
          const config: ConvertRequest = {
            ocr_engine: state.ocrEngine,
            ocr_lang: state.ocrLang,
            ocr_dpi: state.ocrDpi,
            output_format: state.outputFormat,
          };
          await startConvert(sessionId, config);
          break;
        }

        case 'translate': {
          const config: TranslateRequest = {
            target_lang: state.targetLang,
            output_format: state.outputFormat,
            translation_mode: state.translationMode,
            translator: state.translator,
            bilingual: state.bilingual,
            use_ocr: state.useOcr,
            ocr_engine: state.ocrEngine,
            ocr_lang: state.ocrLang,
            ocr_dpi: state.ocrDpi,
            openai_key: state.openaiKey,
            openai_model: state.openaiModel,
            ollama_model: state.ollamaModel,
            ollama_host: state.ollamaHost,
            trans_path: state.transPath,
            gcp_project: state.gcpProject,
          };
          await startTranslate(sessionId, config);
          break;
        }
      }

      dispatch({ type: 'SET_STATUS', payload: { status: 'processing' } });
      startListening(sessionId);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to start processing';
      dispatch({ type: 'SET_STATUS', payload: { status: 'error', errorMessage: message } });
    }
  }, [state, dispatch, startListening]);

  const isProcessing = state.status === 'processing';

  return { startProcessing, isProcessing } as const;
}
