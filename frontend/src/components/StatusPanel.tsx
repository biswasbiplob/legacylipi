import { useAppState, useAppDispatch } from '../context/AppContext';
import { useDownload } from '../hooks/useDownload';

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function StatusPanel() {
  const state = useAppState();
  const dispatch = useAppDispatch();
  const { download, canDownload } = useDownload();

  return (
    <div className="bg-[var(--color-surface-alt)] border border-[var(--color-border)] rounded-xl p-5 sticky top-8">
      <h3 className="text-sm font-semibold text-[var(--color-text)] tracking-wide uppercase mb-4">
        Status
      </h3>

      {/* Idle */}
      {state.status === 'idle' && (
        <div className="flex flex-col items-center text-center py-8">
          <svg className="w-12 h-12 text-[var(--color-text-muted)]/40 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
          <p className="text-sm text-[var(--color-text-muted)]">
            Upload a PDF to get started
          </p>
        </div>
      )}

      {/* Uploading */}
      {state.status === 'uploading' && (
        <div className="flex flex-col items-center text-center py-8">
          <svg className="animate-spin w-10 h-10 text-[var(--color-primary)] mb-3" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <p className="text-sm text-[var(--color-text)]">Uploading...</p>
        </div>
      )}

      {/* Processing */}
      {state.status === 'processing' && state.progress && (
        <div className="space-y-4 py-4">
          <div className="flex items-center gap-2">
            <svg className="animate-spin w-5 h-5 text-[var(--color-primary)] shrink-0" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <p className="text-sm font-medium text-[var(--color-text)]">
              {state.progress.step}
            </p>
          </div>

          {/* Progress bar */}
          <div className="w-full bg-[var(--color-surface)] rounded-full h-2 overflow-hidden">
            <div
              className="h-full bg-[var(--color-primary)] rounded-full transition-all duration-300 ease-out"
              style={{ width: `${Math.max(state.progress.percent, 2)}%` }}
            />
          </div>

          <div className="flex justify-between text-xs text-[var(--color-text-muted)]">
            <span>{state.progress.message}</span>
            <span>{state.progress.percent}%</span>
          </div>
        </div>
      )}

      {/* Processing without progress data */}
      {state.status === 'processing' && !state.progress && (
        <div className="flex flex-col items-center text-center py-8">
          <svg className="animate-spin w-10 h-10 text-[var(--color-primary)] mb-3" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <p className="text-sm text-[var(--color-text)]">Processing...</p>
        </div>
      )}

      {/* Complete */}
      {state.status === 'complete' && (
        <div className="space-y-4 py-4">
          <div className="flex flex-col items-center text-center">
            <div className="w-12 h-12 rounded-full bg-[var(--color-success)]/15 flex items-center justify-center mb-3">
              <svg className="w-6 h-6 text-[var(--color-success)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <p className="text-base font-semibold text-[var(--color-text)]">
              Processing Complete!
            </p>
          </div>

          {/* Result info */}
          {state.resultFilename && (
            <div className="bg-[var(--color-surface)] rounded-lg p-3 space-y-1">
              <p className="text-sm text-[var(--color-text)] font-medium truncate">
                {state.resultFilename}
              </p>
              {state.resultFileSize != null && (
                <p className="text-xs text-[var(--color-text-muted)]">
                  {formatFileSize(state.resultFileSize)}
                </p>
              )}
            </div>
          )}

          {/* Actions */}
          <div className="space-y-2">
            {canDownload && (
              <button
                type="button"
                onClick={download}
                className="w-full bg-[var(--color-success)] hover:bg-green-400 text-white font-semibold py-2.5 px-4 rounded-lg transition-colors flex items-center justify-center gap-2 cursor-pointer"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Download Result
              </button>
            )}
            <button
              type="button"
              onClick={() => dispatch({ type: 'RESET' })}
              className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] font-medium py-2.5 px-4 rounded-lg transition-colors cursor-pointer"
            >
              Start New
            </button>
          </div>
        </div>
      )}

      {/* Error */}
      {state.status === 'error' && (
        <div className="space-y-4 py-4">
          <div className="bg-[var(--color-error)]/10 border border-[var(--color-error)]/30 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <svg className="w-5 h-5 text-[var(--color-error)] shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <p className="text-sm text-[var(--color-error)]">
                {state.errorMessage || 'An unexpected error occurred.'}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => dispatch({ type: 'RESET' })}
            className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] font-medium py-2.5 px-4 rounded-lg transition-colors cursor-pointer"
          >
            Try Again
          </button>
        </div>
      )}
    </div>
  );
}
