import { useCallback, useState, useRef, type DragEvent, type ChangeEvent } from 'react';
import { useFileUpload } from '../hooks/useFileUpload';
import { useAppState } from '../context/AppContext';
import { MAX_FILE_SIZE } from '../lib/constants';

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function FileUploader() {
  const { upload, reset, isUploading } = useFileUpload();
  const state = useAppState();
  const [dragOver, setDragOver] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateAndUpload = useCallback(
    (file: File) => {
      setValidationError(null);

      if (!file.name.toLowerCase().endsWith('.pdf')) {
        setValidationError('Only PDF files are accepted.');
        return;
      }

      if (file.size > MAX_FILE_SIZE) {
        setValidationError(`File too large. Maximum size is ${formatFileSize(MAX_FILE_SIZE)}.`);
        return;
      }

      upload(file);
    },
    [upload],
  );

  const handleDrop = useCallback(
    (e: DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) validateAndUpload(file);
    },
    [validateAndUpload],
  );

  const handleDragOver = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  const handleChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) validateAndUpload(file);
      if (inputRef.current) inputRef.current.value = '';
    },
    [validateAndUpload],
  );

  // File already uploaded -- show info card
  if (state.sessionId && state.filename) {
    return (
      <div className="bg-[var(--color-surface-alt)] border border-[var(--color-border)] rounded-xl p-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 min-w-0">
            <div className="shrink-0 w-10 h-10 rounded-lg bg-[var(--color-primary)]/15 flex items-center justify-center">
              <svg className="w-5 h-5 text-[var(--color-primary)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
            </div>
            <div className="min-w-0">
              <p className="text-[var(--color-text)] font-medium truncate">{state.filename}</p>
              <p className="text-xs text-[var(--color-text-muted)]">
                {state.fileSize != null ? formatFileSize(state.fileSize) : ''}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={reset}
            className="shrink-0 text-sm text-[var(--color-error)] hover:text-red-300 transition-colors cursor-pointer"
          >
            Remove
          </button>
        </div>
      </div>
    );
  }

  // Upload zone
  return (
    <div className="bg-[var(--color-surface-alt)] border border-[var(--color-border)] rounded-xl p-5">
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => inputRef.current?.click()}
        className={`
          relative border-2 border-dashed rounded-lg p-10 text-center cursor-pointer transition-colors
          ${dragOver
            ? 'border-[var(--color-primary)] bg-[var(--color-primary)]/5'
            : 'border-[var(--color-border)] hover:border-[var(--color-text-muted)]'
          }
        `}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf"
          onChange={handleChange}
          className="hidden"
        />

        {isUploading ? (
          <div className="flex flex-col items-center gap-3">
            <svg className="animate-spin w-8 h-8 text-[var(--color-primary)]" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <p className="text-sm text-[var(--color-text-muted)]">Uploading...</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <svg className="w-10 h-10 text-[var(--color-text-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5a4.5 4.5 0 01-1.41-8.775 5.25 5.25 0 0110.338-2.32 3 3 0 013.546 3.052A4.5 4.5 0 0118 19.5H6.75z" />
            </svg>
            <div>
              <p className="text-[var(--color-text)] font-medium">
                Drop your PDF here or <span className="text-[var(--color-primary)]">browse</span>
              </p>
              <p className="text-xs text-[var(--color-text-muted)] mt-1">
                PDF files up to {formatFileSize(MAX_FILE_SIZE)}
              </p>
            </div>
          </div>
        )}
      </div>

      {validationError && (
        <p className="mt-3 text-sm text-[var(--color-error)]">{validationError}</p>
      )}
    </div>
  );
}
