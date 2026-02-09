import { useAppState, useAppDispatch } from '../context/AppContext';

const DEFAULT_OCR_ENGINES: Record<string, string> = {
  easyocr: 'EasyOCR',
  tesseract: 'Tesseract',
};

export default function OcrSettings() {
  const state = useAppState();
  const dispatch = useAppDispatch();

  const ocrEngines = state.config.options?.ocr_engines ?? DEFAULT_OCR_ENGINES;
  const ocrLanguages = state.config.languages?.ocr ?? {};

  return (
    <div className="bg-[var(--color-surface-alt)] border border-[var(--color-border)] rounded-xl p-5 space-y-4">
      <h3 className="text-sm font-semibold text-[var(--color-text)] tracking-wide uppercase">
        OCR Settings
      </h3>

      {/* OCR Engine */}
      <div>
        <label className="text-sm font-medium text-[var(--color-text-muted)] mb-1.5 block">
          OCR Engine
        </label>
        <select
          value={state.ocrEngine}
          onChange={(e) =>
            dispatch({
              type: 'UPDATE_SETTINGS',
              payload: { ocrEngine: e.target.value as 'easyocr' | 'tesseract' },
            })
          }
          className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-[var(--color-text)] focus:outline-none focus:border-[var(--color-primary)]"
        >
          {Object.entries(ocrEngines).map(([key, label]) => (
            <option key={key} value={key}>
              {label}
            </option>
          ))}
        </select>
      </div>

      {/* OCR Language */}
      <div>
        <label className="text-sm font-medium text-[var(--color-text-muted)] mb-1.5 block">
          OCR Language
        </label>
        <select
          value={state.ocrLang}
          onChange={(e) =>
            dispatch({ type: 'UPDATE_SETTINGS', payload: { ocrLang: e.target.value } })
          }
          className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-[var(--color-text)] focus:outline-none focus:border-[var(--color-primary)]"
        >
          {Object.entries(ocrLanguages).map(([code, name]) => (
            <option key={code} value={code}>
              {name}
            </option>
          ))}
        </select>
      </div>

      {/* OCR DPI */}
      <div>
        <label className="text-sm font-medium text-[var(--color-text-muted)] mb-1.5 block">
          OCR DPI
        </label>
        <select
          value={state.ocrDpi}
          onChange={(e) =>
            dispatch({ type: 'UPDATE_SETTINGS', payload: { ocrDpi: Number(e.target.value) } })
          }
          className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-[var(--color-text)] focus:outline-none focus:border-[var(--color-primary)]"
        >
          <option value={150}>150</option>
          <option value={300}>300</option>
          <option value={600}>600</option>
        </select>
      </div>
    </div>
  );
}
