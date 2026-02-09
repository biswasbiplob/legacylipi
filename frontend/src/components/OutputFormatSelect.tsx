import { useAppState, useAppDispatch } from '../context/AppContext';

const DEFAULT_FORMATS: Record<string, string> = {
  pdf: 'PDF',
  text: 'Text',
  markdown: 'Markdown',
};

export default function OutputFormatSelect() {
  const state = useAppState();
  const dispatch = useAppDispatch();

  const formats = state.config.options?.output_formats ?? DEFAULT_FORMATS;

  return (
    <div className="bg-[var(--color-surface-alt)] border border-[var(--color-border)] rounded-xl p-5">
      <label className="text-sm font-medium text-[var(--color-text-muted)] mb-3 block">
        Output Format
      </label>
      <div className="flex gap-2">
        {Object.entries(formats).map(([key, label]) => {
          const isActive = state.outputFormat === key;
          return (
            <button
              key={key}
              type="button"
              onClick={() =>
                dispatch({
                  type: 'UPDATE_SETTINGS',
                  payload: { outputFormat: key as 'pdf' | 'text' | 'markdown' },
                })
              }
              className={`
                flex-1 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors cursor-pointer
                ${isActive
                  ? 'bg-[var(--color-primary)] text-white shadow-md shadow-indigo-500/20'
                  : 'bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-muted)] hover:text-[var(--color-text)]'
                }
              `}
            >
              {label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
