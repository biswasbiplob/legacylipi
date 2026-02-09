import { useCallback, useEffect, useRef } from 'react';
import { useAppDispatch } from '../context/AppContext';
import type { ProgressEvent } from '../lib/types';

export function useProgress() {
  const dispatch = useAppDispatch();
  const sourceRef = useRef<EventSource | null>(null);

  const stopListening = useCallback(() => {
    if (sourceRef.current) {
      sourceRef.current.close();
      sourceRef.current = null;
    }
  }, []);

  const startListening = useCallback(
    (sessionId: string) => {
      // Close any existing connection before opening a new one
      stopListening();

      const es = new EventSource(`/api/v1/sessions/${sessionId}/progress`);
      sourceRef.current = es;

      es.onmessage = (event: MessageEvent) => {
        let data: ProgressEvent;
        try {
          data = JSON.parse(event.data) as ProgressEvent;
        } catch {
          return; // Ignore malformed messages
        }

        dispatch({ type: 'SET_PROGRESS', payload: data });

        if (data.status === 'complete') {
          dispatch({ type: 'SET_STATUS', payload: { status: 'complete' } });
          if (data.filename && data.file_size != null) {
            dispatch({
              type: 'SET_RESULT',
              payload: {
                filename: data.filename,
                fileSize: data.file_size,
              },
            });
          }
          stopListening();
        } else if (data.status === 'error') {
          dispatch({
            type: 'SET_STATUS',
            payload: { status: 'error', errorMessage: data.message },
          });
          stopListening();
        }
      };

      es.onerror = () => {
        dispatch({
          type: 'SET_STATUS',
          payload: { status: 'error', errorMessage: 'Lost connection to progress stream' },
        });
        stopListening();
      };
    },
    [dispatch, stopListening],
  );

  // Clean up the EventSource when the component unmounts
  useEffect(() => {
    return () => {
      stopListening();
    };
  }, [stopListening]);

  return { startListening, stopListening } as const;
}
