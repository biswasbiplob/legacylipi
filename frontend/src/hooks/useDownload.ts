import { useCallback } from 'react';
import { useAppState } from '../context/AppContext';
import { getDownloadUrl } from '../lib/api';

export function useDownload() {
  const state = useAppState();

  const canDownload = state.status === 'complete' && state.sessionId !== null;

  const download = useCallback(() => {
    if (!state.sessionId) return;

    const a = document.createElement('a');
    a.href = getDownloadUrl(state.sessionId);
    a.download = '';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }, [state.sessionId]);

  return { download, canDownload } as const;
}
