import { useCallback } from 'react';
import { useAppState, useAppDispatch } from '../context/AppContext';
import { uploadFile, deleteSession } from '../lib/api';

export function useFileUpload() {
  const state = useAppState();
  const dispatch = useAppDispatch();

  const upload = useCallback(
    async (file: File): Promise<void> => {
      dispatch({ type: 'SET_STATUS', payload: { status: 'uploading' } });

      try {
        const response = await uploadFile(file);

        dispatch({
          type: 'SET_SESSION',
          payload: {
            sessionId: response.session_id,
            filename: response.filename,
            fileSize: response.file_size,
          },
        });
        dispatch({ type: 'SET_STATUS', payload: { status: 'idle' } });
      } catch (err) {
        const message =
          err instanceof Error ? err.message : 'File upload failed';
        dispatch({ type: 'SET_STATUS', payload: { status: 'error', errorMessage: message } });
      }
    },
    [dispatch],
  );

  const reset = useCallback(async (): Promise<void> => {
    if (state.sessionId) {
      try {
        await deleteSession(state.sessionId);
      } catch {
        // Best-effort cleanup -- ignore errors when deleting the server session
      }
    }

    dispatch({ type: 'RESET' });
  }, [state.sessionId, dispatch]);

  const isUploading = state.status === 'uploading';

  return { upload, reset, isUploading } as const;
}
