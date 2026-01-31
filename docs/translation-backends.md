# Translation Backends

Detailed setup guides for all LegacyLipi translation backends.

## Quick Comparison

| Backend | Description | Setup Required | Rate Limiting | Best For |
|---------|-------------|----------------|---------------|----------|
| `trans` | translate-shell CLI | Install CLI tool | Built-in delays | General use |
| `google` | Google Translate (free API) | None | Built-in delays | Quick translations |
| `mymemory` | MyMemory API (free) | None | 500 char limit | Small documents |
| `ollama` | Local LLM via Ollama | Ollama server | None (local) | Privacy, offline use |
| `openai` | OpenAI GPT models | API key | API rate limits | High quality |
| `gcp_cloud` | Google Cloud Translation | GCP project + credentials | 500K chars/month free | Production use |
| `mock` | Mock translator | None | N/A | Testing |

---

## translate-shell (Recommended)

translate-shell (`trans`) is a command-line translator that works reliably. LegacyLipi's `trans` backend includes:

- **Rate limiting**: 2 second delay with random jitter between chunks
- **Auto-retry**: Up to 3 retries with exponential backoff for rate-limit errors
- **Adaptive timeout**: Starts at 60s, increases on retry (up to 180s)
- **Smaller chunks**: Text split into 2000-char chunks to avoid API limits

### Installation

**Ubuntu/Debian:**
```bash
sudo apt-get install translate-shell
```

**macOS:**
```bash
brew install translate-shell
```

**Manual install (any platform):**
```bash
wget git.io/trans && chmod +x trans
```

### Usage

```bash
# Default (uses Google Translate engine via trans CLI)
uv run legacylipi translate input.pdf --translator trans

# With custom path to trans executable
uv run legacylipi translate input.pdf --translator trans --trans-path ./trans

# With OCR for scanned documents
uv run legacylipi translate input.pdf --use-ocr --translator trans -o output.pdf --format pdf
```

---

## Ollama (Local LLM)

Run translations locally using Ollama for privacy and offline use.

### Setup

1. Install Ollama from [ollama.ai](https://ollama.ai)
2. Start the Ollama server
3. Pull a model

```bash
# Start Ollama (in another terminal)
ollama serve

# Pull a model
ollama pull llama3.2
```

### Usage

```bash
# Use with LegacyLipi
uv run legacylipi translate input.pdf --translator ollama --model llama3.2
```

### Recommended Models

- `llama3.2` - Good balance of speed and quality
- `mistral` - Fast and capable
- `llama3.1:70b` - Higher quality (requires more RAM)

---

## OpenAI

Use OpenAI's GPT models for high-quality translation.

### Setup

Set your API key as an environment variable:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

### Usage

```bash
# Use with default model (gpt-4o-mini)
uv run legacylipi translate input.pdf --translator openai

# Use with a specific model
uv run legacylipi translate input.pdf --translator openai --model gpt-4o
```

### Available Models

| Model | Description |
|-------|-------------|
| `gpt-4o-mini` | Fast and cost-effective (default) |
| `gpt-4o` | Most capable, best for complex translations |
| `gpt-4-turbo` | High quality with faster response |
| `gpt-4.5-preview` | Latest preview model |

---

## Google Cloud Translation

Use Google Cloud Translation API for production-grade translation with a free tier.

### Setup

1. **Create a GCP project** at [console.cloud.google.com](https://console.cloud.google.com)

2. **Enable Cloud Translation API**
   - Go to APIs & Services → Library
   - Search for "Cloud Translation API"
   - Click Enable

3. **Create a service account**
   - Go to IAM & Admin → Service Accounts
   - Create a new service account
   - Grant "Cloud Translation API User" role
   - Create and download a JSON key

4. **Set credentials**
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
   ```

5. **Set your GCP project ID**
   ```bash
   export GCP_PROJECT_ID="your-project-id"
   ```

### Usage

```bash
# Use GCP Cloud Translation (project ID from env var)
uv run legacylipi translate input.pdf --translator gcp_cloud

# With explicit project ID
uv run legacylipi translate input.pdf --translator gcp_cloud --gcp-project my-project-id

# Force translation even if free tier limit would be exceeded
uv run legacylipi translate input.pdf --translator gcp_cloud --force-translate
```

### Free Tier

- **500,000 characters per month** free
- Monthly limit resets on the 1st of each month
- Charges apply after limit is exceeded

### Check Usage

```bash
# View current monthly usage
uv run legacylipi usage --service gcp_translate
```

### Understanding `--force-translate`

| Flag | Behavior |
|------|----------|
| Without `--force-translate` | Translation fails if it would exceed the free tier limit |
| With `--force-translate` | Translation proceeds regardless of limit (charges may apply) |

---

## Google Translate (Free API)

Uses the free Google Translate web API. No setup required but subject to rate limiting.

### Usage

```bash
uv run legacylipi translate input.pdf --translator google
```

**Note**: This uses an unofficial API and may be rate-limited for large documents. For production use, consider `gcp_cloud` or `trans` backends.

---

## MyMemory

Free translation API with a 500-character limit per request.

### Usage

```bash
uv run legacylipi translate input.pdf --translator mymemory
```

**Note**: Best suited for small documents due to the character limit.

---

## Mock Translator

For testing and development purposes.

### Usage

```bash
uv run legacylipi translate input.pdf --translator mock
```

Returns the input text with a `[MOCK]` prefix, useful for testing the pipeline without actual translation.
