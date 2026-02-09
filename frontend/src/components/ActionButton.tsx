import { useAppState } from '../context/AppContext';
import { useProcessing } from '../hooks/useProcessing';

const LABELS: Record<string, string> = {
  scan_copy: 'Create Scanned Copy',
  convert: 'Convert to Unicode',
  translate: 'Translate',
};

export default function ActionButton() {
  const state = useAppState();
  const { startProcessing, isProcessing } = useProcessing();

  const label = LABELS[state.workflowMode] ?? 'Process';
  const disabled =
    !state.sessionId || state.status === 'uploading' || state.status === 'processing';

  return (
    <button
      type="button"
      onClick={startProcessing}
      disabled={disabled}
      className="w-full bg-[var(--color-primary)] hover:bg-[var(--color-primary-hover)] text-white font-semibold py-3 px-6 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 cursor-pointer"
    >
      {isProcessing && (
        <svg
          className="animate-spin h-5 w-5 text-white"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
      )}
      {isProcessing ? 'Processing...' : label}
    </button>
  );
}
