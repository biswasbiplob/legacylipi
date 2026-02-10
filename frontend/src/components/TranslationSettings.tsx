import { useAppState, useAppDispatch } from '../context/AppContext';
import OcrSettings from './OcrSettings';

const DEFAULT_TRANSLATION_MODES: Record<string, string> = {
  structure_preserving: 'Structure Preserving',
  flowing: 'Flowing Text',
};

const SOURCE_LANGUAGE_LABELS: Record<string, string> = {
  mr: 'Marathi',
  hi: 'Hindi',
  ta: 'Tamil',
  te: 'Telugu',
  kn: 'Kannada',
  ml: 'Malayalam',
  bn: 'Bengali',
  gu: 'Gujarati',
  pa: 'Punjabi',
  sa: 'Sanskrit',
};

export default function TranslationSettings() {
  const state = useAppState();
  const dispatch = useAppDispatch();

  const targetLanguages = state.config.languages?.target ?? {};
  const translationModes = state.config.options?.translation_modes ?? DEFAULT_TRANSLATION_MODES;
  const sourceLanguages = state.config.sourceLanguages?.languages ?? {};

  return (
    <div className="bg-[var(--color-surface-alt)] border border-[var(--color-border)] rounded-xl p-5 space-y-4">
      <h3 className="text-sm font-semibold text-[var(--color-text)] tracking-wide uppercase">
        Translation Settings
      </h3>

      {/* Source Language */}
      <div>
        <label className="text-sm font-medium text-[var(--color-text-muted)] mb-1.5 block">
          Source Language
        </label>
        <select
          value={state.sourceLang}
          onChange={(e) =>
            dispatch({ type: 'UPDATE_SETTINGS', payload: { sourceLang: e.target.value } })
          }
          className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-[var(--color-text)] focus:outline-none focus:border-[var(--color-primary)]"
        >
          <option value="">Auto-detect (from encoding)</option>
          {Object.keys(sourceLanguages).map((code) => (
            <option key={code} value={code}>
              {SOURCE_LANGUAGE_LABELS[code] ?? code}
            </option>
          ))}
        </select>
      </div>

      {/* Target Language */}
      <div>
        <label className="text-sm font-medium text-[var(--color-text-muted)] mb-1.5 block">
          Target Language
        </label>
        <select
          value={state.targetLang}
          onChange={(e) =>
            dispatch({ type: 'UPDATE_SETTINGS', payload: { targetLang: e.target.value } })
          }
          className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-[var(--color-text)] focus:outline-none focus:border-[var(--color-primary)]"
        >
          {Object.entries(targetLanguages).map(([code, name]) => (
            <option key={code} value={code}>
              {name}
            </option>
          ))}
        </select>
      </div>

      {/* Translation Mode */}
      <div>
        <label className="text-sm font-medium text-[var(--color-text-muted)] mb-1.5 block">
          Translation Mode
        </label>
        <select
          value={state.translationMode}
          onChange={(e) =>
            dispatch({
              type: 'UPDATE_SETTINGS',
              payload: {
                translationMode: e.target.value as 'structure_preserving' | 'flowing',
              },
            })
          }
          className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-[var(--color-text)] focus:outline-none focus:border-[var(--color-primary)]"
        >
          {Object.entries(translationModes).map(([key, label]) => (
            <option key={key} value={key}>
              {label}
            </option>
          ))}
        </select>
      </div>

      {/* Bilingual output checkbox */}
      <div>
        <label className="flex items-center gap-3 cursor-pointer group">
          <input
            type="checkbox"
            checked={state.bilingual}
            onChange={(e) =>
              dispatch({ type: 'UPDATE_SETTINGS', payload: { bilingual: e.target.checked } })
            }
            className="w-4 h-4 rounded border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-primary)] accent-[var(--color-primary)]"
          />
          <span className="text-sm text-[var(--color-text)] group-hover:text-[var(--color-primary-hover)] transition-colors">
            Bilingual side-by-side output (Markdown)
          </span>
        </label>
      </div>

      {/* Use OCR checkbox */}
      <div>
        <label className="flex items-center gap-3 cursor-pointer group">
          <input
            type="checkbox"
            checked={state.useOcr}
            onChange={(e) =>
              dispatch({ type: 'UPDATE_SETTINGS', payload: { useOcr: e.target.checked } })
            }
            className="w-4 h-4 rounded border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-primary)] accent-[var(--color-primary)]"
          />
          <span className="text-sm text-[var(--color-text)] group-hover:text-[var(--color-primary-hover)] transition-colors">
            Use OCR for scanned documents
          </span>
        </label>
      </div>

      {/* Inline OCR settings when enabled */}
      {state.useOcr && (
        <div className="pl-2 border-l-2 border-[var(--color-border)]">
          <OcrSettings />
        </div>
      )}
    </div>
  );
}
