import { useAppState, useAppDispatch } from '../context/AppContext';

export default function ScanCopySettings() {
  const state = useAppState();
  const dispatch = useAppDispatch();

  return (
    <div className="bg-[var(--color-surface-alt)] border border-[var(--color-border)] rounded-xl p-5 space-y-4">
      <h3 className="text-sm font-semibold text-[var(--color-text)] tracking-wide uppercase">
        Scan Copy Settings
      </h3>

      {/* DPI */}
      <div>
        <label className="text-sm font-medium text-[var(--color-text-muted)] mb-1.5 block">
          DPI
        </label>
        <select
          value={state.dpi}
          onChange={(e) =>
            dispatch({ type: 'UPDATE_SETTINGS', payload: { dpi: Number(e.target.value) } })
          }
          className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-[var(--color-text)] focus:outline-none focus:border-[var(--color-primary)]"
        >
          <option value={150}>150</option>
          <option value={300}>300</option>
          <option value={600}>600</option>
        </select>
      </div>

      {/* Color Mode */}
      <div>
        <label className="text-sm font-medium text-[var(--color-text-muted)] mb-1.5 block">
          Color Mode
        </label>
        <select
          value={state.colorMode}
          onChange={(e) =>
            dispatch({
              type: 'UPDATE_SETTINGS',
              payload: { colorMode: e.target.value as 'color' | 'grayscale' | 'bw' },
            })
          }
          className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-[var(--color-text)] focus:outline-none focus:border-[var(--color-primary)]"
        >
          <option value="color">Color</option>
          <option value="grayscale">Grayscale</option>
          <option value="bw">Black &amp; White</option>
        </select>
      </div>

      {/* Quality */}
      <div>
        <label className="text-sm font-medium text-[var(--color-text-muted)] mb-1.5 block">
          Quality
          <span className="ml-2 text-[var(--color-text)] font-semibold">{state.quality}</span>
        </label>
        <input
          type="range"
          min={1}
          max={100}
          value={state.quality}
          onChange={(e) =>
            dispatch({ type: 'UPDATE_SETTINGS', payload: { quality: Number(e.target.value) } })
          }
          className="w-full accent-[var(--color-primary)]"
        />
        <div className="flex justify-between text-xs text-[var(--color-text-muted)] mt-1">
          <span>1 (Smallest)</span>
          <span>100 (Best)</span>
        </div>
      </div>
    </div>
  );
}
