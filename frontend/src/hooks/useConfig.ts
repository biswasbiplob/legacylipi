import { useEffect, useState } from 'react';
import { useAppDispatch } from '../context/AppContext';
import { fetchLanguages, fetchTranslators, fetchOptions, fetchSourceLanguages } from '../lib/api';

export function useConfig() {
  const dispatch = useAppDispatch();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadConfig() {
      try {
        const [languages, translators, options, sourceLanguages] = await Promise.all([
          fetchLanguages(),
          fetchTranslators(),
          fetchOptions(),
          fetchSourceLanguages(),
        ]);

        if (cancelled) return;

        dispatch({ type: 'SET_CONFIG_LANGUAGES', payload: languages });
        dispatch({ type: 'SET_CONFIG_TRANSLATORS', payload: translators });
        dispatch({ type: 'SET_CONFIG_OPTIONS', payload: options });
        dispatch({ type: 'SET_CONFIG_SOURCE_LANGUAGES', payload: sourceLanguages });
      } catch (err) {
        if (cancelled) return;
        const message =
          err instanceof Error ? err.message : 'Failed to load configuration';
        setError(message);
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadConfig();

    return () => {
      cancelled = true;
    };
  }, [dispatch]);

  return { loading, error } as const;
}
