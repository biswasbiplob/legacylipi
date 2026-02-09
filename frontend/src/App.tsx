import { AppProvider, useAppState } from './context/AppContext';
import { useConfig } from './hooks/useConfig';
import Header from './components/Header';
import FileUploader from './components/FileUploader';
import WorkflowModeSelector from './components/WorkflowModeSelector';
import ScanCopySettings from './components/ScanCopySettings';
import OcrSettings from './components/OcrSettings';
import OutputFormatSelect from './components/OutputFormatSelect';
import TranslationSettings from './components/TranslationSettings';
import TranslatorSettings from './components/TranslatorSettings';
import ActionButton from './components/ActionButton';
import StatusPanel from './components/StatusPanel';

function AppContent() {
  const { loading, error } = useConfig();
  const state = useAppState();

  if (loading) {
    return (
      <div className="min-h-screen bg-[var(--color-surface)] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <svg
            className="animate-spin w-10 h-10 text-[var(--color-primary)]"
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
          <p className="text-[var(--color-text-muted)] text-sm">Loading configuration...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[var(--color-surface)] flex items-center justify-center">
        <div className="bg-[var(--color-surface-alt)] border border-[var(--color-error)]/30 rounded-xl p-8 max-w-md text-center">
          <svg
            className="w-12 h-12 text-[var(--color-error)] mx-auto mb-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          <h2 className="text-lg font-semibold text-[var(--color-text)] mb-2">
            Failed to Load
          </h2>
          <p className="text-sm text-[var(--color-text-muted)]">{error}</p>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="mt-6 bg-[var(--color-primary)] hover:bg-[var(--color-primary-hover)] text-white font-semibold py-2.5 px-6 rounded-lg transition-colors cursor-pointer"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--color-surface)]">
      <div className="max-w-6xl mx-auto px-4 py-8">
        <Header />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-8">
          {/* Left column -- settings */}
          <div className="lg:col-span-2 space-y-5">
            <FileUploader />

            {state.sessionId && (
              <>
                <WorkflowModeSelector />

                {state.workflowMode === 'scan_copy' && <ScanCopySettings />}

                {state.workflowMode === 'convert' && (
                  <>
                    <OcrSettings />
                    <OutputFormatSelect />
                  </>
                )}

                {state.workflowMode === 'translate' && (
                  <>
                    <TranslationSettings />
                    <TranslatorSettings />
                    <OutputFormatSelect />
                  </>
                )}

                <ActionButton />
              </>
            )}
          </div>

          {/* Right column -- status */}
          <div className="lg:col-span-1">
            <StatusPanel />
          </div>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}
