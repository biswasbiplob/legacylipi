import { useAppState, useAppDispatch } from '../context/AppContext';
import type { WorkflowMode } from '../lib/types';

const DEFAULT_MODES: Record<string, string> = {
  scan_copy: 'Scanned Copy',
  convert: 'Convert to Unicode',
  translate: 'Full Translation',
};

export default function WorkflowModeSelector() {
  const state = useAppState();
  const dispatch = useAppDispatch();

  const modes = state.config.options?.workflow_modes ?? DEFAULT_MODES;

  return (
    <div className="bg-[var(--color-surface-alt)] border border-[var(--color-border)] rounded-xl p-5">
      <label className="text-sm font-medium text-[var(--color-text-muted)] mb-3 block">
        Workflow
      </label>
      <div className="flex gap-2">
        {Object.entries(modes).map(([key, label]) => {
          const isActive = state.workflowMode === key;
          return (
            <button
              key={key}
              type="button"
              onClick={() =>
                dispatch({ type: 'SET_WORKFLOW_MODE', payload: key as WorkflowMode })
              }
              className={`
                flex-1 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors cursor-pointer
                ${isActive
                  ? 'bg-[var(--color-primary)] text-white shadow-md shadow-indigo-500/20'
                  : 'bg-[var(--color-surface)] text-[var(--color-text-muted)] hover:text-[var(--color-text)]'
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
