import { useAppState, useAppDispatch } from '../context/AppContext';

const DEFAULT_BACKENDS: Record<string, string> = {
  trans: 'Translate-Shell (CLI)',
  google: 'Google Translate',
  mymemory: 'MyMemory',
  ollama: 'Ollama (Local LLM)',
  openai: 'OpenAI',
  gcp_cloud: 'Google Cloud Translation',
};

export default function TranslatorSettings() {
  const state = useAppState();
  const dispatch = useAppDispatch();

  const backends = state.config.translators?.backends ?? DEFAULT_BACKENDS;
  const openaiModels = state.config.translators?.openai_models ?? [];
  const ollamaModels = state.config.translators?.ollama_models ?? [];

  return (
    <div className="bg-[var(--color-surface-alt)] border border-[var(--color-border)] rounded-xl p-5 space-y-4">
      <h3 className="text-sm font-semibold text-[var(--color-text)] tracking-wide uppercase">
        Translator Backend
      </h3>

      {/* Translator select */}
      <div>
        <label className="text-sm font-medium text-[var(--color-text-muted)] mb-1.5 block">
          Translator
        </label>
        <select
          value={state.translator}
          onChange={(e) =>
            dispatch({ type: 'UPDATE_SETTINGS', payload: { translator: e.target.value } })
          }
          className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-[var(--color-text)] focus:outline-none focus:border-[var(--color-primary)]"
        >
          {Object.entries(backends).map(([key, label]) => (
            <option key={key} value={key}>
              {label}
            </option>
          ))}
        </select>
      </div>

      {/* OpenAI settings */}
      {state.translator === 'openai' && (
        <>
          <div>
            <label className="text-sm font-medium text-[var(--color-text-muted)] mb-1.5 block">
              API Key
            </label>
            <input
              type="password"
              value={state.openaiKey}
              onChange={(e) =>
                dispatch({ type: 'UPDATE_SETTINGS', payload: { openaiKey: e.target.value } })
              }
              placeholder="sk-..."
              className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-[var(--color-text)] focus:outline-none focus:border-[var(--color-primary)] placeholder:text-[var(--color-text-muted)]/50"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-[var(--color-text-muted)] mb-1.5 block">
              Model
            </label>
            <select
              value={state.openaiModel}
              onChange={(e) =>
                dispatch({ type: 'UPDATE_SETTINGS', payload: { openaiModel: e.target.value } })
              }
              className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-[var(--color-text)] focus:outline-none focus:border-[var(--color-primary)]"
            >
              {openaiModels.map((model) => (
                <option key={model} value={model}>
                  {model}
                </option>
              ))}
            </select>
          </div>
        </>
      )}

      {/* Ollama settings */}
      {state.translator === 'ollama' && (
        <>
          <div>
            <label className="text-sm font-medium text-[var(--color-text-muted)] mb-1.5 block">
              Model
            </label>
            <select
              value={state.ollamaModel}
              onChange={(e) =>
                dispatch({ type: 'UPDATE_SETTINGS', payload: { ollamaModel: e.target.value } })
              }
              className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-[var(--color-text)] focus:outline-none focus:border-[var(--color-primary)]"
            >
              {ollamaModels.map((model) => (
                <option key={model} value={model}>
                  {model}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-sm font-medium text-[var(--color-text-muted)] mb-1.5 block">
              Host URL
            </label>
            <input
              type="text"
              value={state.ollamaHost}
              onChange={(e) =>
                dispatch({ type: 'UPDATE_SETTINGS', payload: { ollamaHost: e.target.value } })
              }
              placeholder="http://localhost:11434"
              className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-[var(--color-text)] focus:outline-none focus:border-[var(--color-primary)] placeholder:text-[var(--color-text-muted)]/50"
            />
          </div>
        </>
      )}

      {/* Translate-Shell settings */}
      {state.translator === 'trans' && (
        <div>
          <label className="text-sm font-medium text-[var(--color-text-muted)] mb-1.5 block">
            Binary Path
          </label>
          <input
            type="text"
            value={state.transPath}
            onChange={(e) =>
              dispatch({ type: 'UPDATE_SETTINGS', payload: { transPath: e.target.value } })
            }
            placeholder="auto-detect"
            className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-[var(--color-text)] focus:outline-none focus:border-[var(--color-primary)] placeholder:text-[var(--color-text-muted)]/50"
          />
          <p className="text-xs text-[var(--color-text-muted)] mt-1">
            Leave empty to auto-detect the translate-shell binary
          </p>
        </div>
      )}

      {/* GCP Cloud settings */}
      {state.translator === 'gcp_cloud' && (
        <div>
          <label className="text-sm font-medium text-[var(--color-text-muted)] mb-1.5 block">
            GCP Project ID
          </label>
          <input
            type="text"
            value={state.gcpProject}
            onChange={(e) =>
              dispatch({ type: 'UPDATE_SETTINGS', payload: { gcpProject: e.target.value } })
            }
            placeholder="my-gcp-project"
            className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-[var(--color-text)] focus:outline-none focus:border-[var(--color-primary)] placeholder:text-[var(--color-text-muted)]/50"
          />
        </div>
      )}

      {/* Google / MyMemory -- no config needed */}
      {(state.translator === 'google' || state.translator === 'mymemory') && (
        <p className="text-sm text-[var(--color-text-muted)] italic">
          No configuration needed for this translator.
        </p>
      )}
    </div>
  );
}
