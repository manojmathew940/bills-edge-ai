# Bills AI Analyst

This project is a Buffalo Bills-focused AI backend that is intended to combine:

- structured game analytics
- optional retrieval from Bills-related sources
- LLM-powered explanation generation

The goal is to answer questions such as:

- Why did the Bills lose game X?
- Why did they take 8 sacks?
- Would more blitzing have helped?
- What would have helped them win?

The long-term direction is to support a hybrid architecture where:

1. Bills game data is ingested and cleaned into an analysis-ready dataset.
2. An analytics layer computes relevant football metrics and evidence.
3. Retrieval or web search can add supporting context from articles and reports.
4. An LLM synthesizes the evidence into a grounded explanation.

Future extensions may include:

- comparing web search vs. RAG for Bills-specific questions
- adding a Bills draft assistant
- exposing the system through a website and API

## Current Status

The repo is currently an early FastAPI scaffold with a basic application entry point in `app/main.py`.

## Raw Data Ingestion

Download raw Bills play-by-play rows for one season:

```bash
python3 -m app.data_foundation.ingestion 2024
```

This saves the filtered raw source columns to:

```text
data/raw/bills_play_by_play_2024_raw.csv.gz
```

The script also writes a metadata file next to the raw data:

```text
data/raw/bills_play_by_play_2024_raw.metadata.json
```

The raw data is intentionally saved before normalization so the source columns can be inspected before deciding the analysis-ready schema mapping. The ingestion script validates the season range, checks required nflverse columns, limits the compressed source size, and only writes into `data/raw/`.

## Processed Play Data

Create the first curated play-level dataset for a season:

```bash
python3 -m app.data_foundation.cleaning 2024
```

This reads the raw Bills play-by-play file and writes:

```text
data/processed/bills_plays_2024.parquet
```

## Game Metrics

Start the API:

```bash
uvicorn app.main:app --reload
```

Get deterministic game metrics for a Bills game:

```bash
curl http://localhost:8000/games/2024/1/metrics
```

## Ask A Game Question

The first LLM slice answers questions from the deterministic metric packet only. It does not use play-level evidence, web search, injury reports, articles, quotes, or retrieval context.

### OpenAI

By default, the app uses OpenAI with `gpt-5.5`.

Set your OpenAI API key:

```bash
export OPENAI_API_KEY="your_api_key"
```

Or create a local `.env` file:

```text
OPENAI_API_KEY=your_api_key
```

Optionally override the model:

```text
LLM_MODEL=gpt-5.5
```

The internal UI can switch between both providers per request. For that mode,
configure OpenAI and local settings side by side:

```text
OPENAI_API_KEY=your_api_key
OPENAI_LLM_MODEL=gpt-5.5
LOCAL_LLM_BASE_URL=http://127.0.0.1:11434/v1
LOCAL_LLM_MODEL=qwen2.5:7b-instruct
LOCAL_LLM_API_KEY=ollama
```

### Ollama

Install Ollama, download a local model, and start the local server:

```bash
ollama run qwen2.5:7b-instruct
```

Exit the Ollama chat with `/bye`, then make sure the Ollama server is running:

```bash
ollama serve
```

Configure the app to call Ollama's OpenAI-compatible local endpoint:

```text
LLM_BASE_URL=http://127.0.0.1:11434/v1
LLM_MODEL=qwen2.5:7b-instruct
LLM_API_KEY=ollama
```

The older `LLM_*` variables still work as a single-provider configuration, but
the provider toggle prefers the `OPENAI_*` and `LOCAL_LLM_*` variables above so
both providers can stay configured at once.

`LLM_API_KEY` is a placeholder for Ollama. The local server does not require a real API key, but the OpenAI client expects one.

#### Ollama on Windows, app in WSL

If Ollama runs on Windows while this FastAPI app runs inside WSL, the most
stable setup is to make WSL and Windows share `localhost` through WSL mirrored
networking. That lets this project keep using:

```text
LOCAL_LLM_BASE_URL=http://127.0.0.1:11434/v1
```

One-time Windows setup:

1. Create or edit `%UserProfile%\.wslconfig`:

   ```ini
   [wsl2]
   networkingMode=mirrored
   ```

2. Restart WSL from PowerShell:

   ```powershell
   wsl --shutdown
   ```

3. Start Ollama from the Windows Start menu and keep the project-local values
   in `.env`:

   ```text
   LOCAL_LLM_BASE_URL=http://127.0.0.1:11434/v1
   LOCAL_LLM_MODEL=qwen2.5:7b-instruct
   LOCAL_LLM_API_KEY=ollama
   ```

After that, the app loads `.env` automatically and no per-session export
commands are required.

If mirrored networking is unavailable on your Windows version, use WSL's
default NAT mode instead:

1. On Windows, set a persistent user environment variable:

   ```text
   OLLAMA_HOST=0.0.0.0:11434
   ```

2. Quit and restart the Ollama Windows app.
3. From WSL, get the Windows host IP with:

   ```bash
   ip route show | grep -i default | awk '{ print $3 }'
   ```

4. Put that IP into `.env`, for example:

   ```text
   LOCAL_LLM_BASE_URL=http://172.30.96.1:11434/v1
   ```

Mirrored networking is preferred because the NAT-mode host IP can change after
WSL restarts.

Ask a question:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"season":2024,"question":"Why did the Bills beat the Cardinals?"}'
```

The `/ask` endpoint resolves the game from the question text within the selected
season. Mention an opponent for unique matchups, or include the week when the
Bills played the same opponent more than once:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"season":2024,"question":"What happened in week 9 against the Dolphins?"}'
```

### Inspect the exact LLM prompt

To include the rendered prompt in `/ask` responses and show it in the browser UI,
start the app with debug prompts enabled:

```bash
BILLS_AI_DEBUG_PROMPT=1 uvicorn app.main:app --reload
```

Then ask a question in the UI and expand **LLM Debug Prompt** beneath the metrics
panel. The `/ask` JSON response will also include a `debug_prompt` object with
the selected provider, model, instructions, rendered input, and token limit.
