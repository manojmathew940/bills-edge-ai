# NFL AI Analyst

This project is an NFL analytics backend that combines:

- league-wide structured game analytics
- optional retrieval from NFL-related sources
- LLM-powered explanation generation

The goal is to answer questions such as:

- What was Kansas City's EPA on third-and-long in the fourth quarter?
- Which offenses were most successful in the red zone?
- How did Josh Allen perform against a specific defensive team?
- Which plays had the largest effect on a game's win probability?

The long-term direction is to support a data-grounded architecture where:

1. NFL game data is ingested and cleaned into analysis-ready datasets.
2. A data extractor LLM decides whether local analytics data can help answer a
   question.
3. The extractor may generate SQL against approved analytics views.
4. Application code validates and executes that SQL with guardrails.
5. An answer LLM synthesizes the returned data into a grounded explanation.
6. Retrieval or web search can later add supporting context from articles and
   reports when local data is not enough.

Future extensions may include:

- adding weekly player and team statistics
- comparing web search vs. RAG for NFL context
- adding roster and draft analysis
- exposing the system through a website and API

## Current Status

The repo is currently a FastAPI application with data ingestion, processed
play-level data, a browser UI, and an LLM-backed `/ask` endpoint.

## Raw Data Ingestion

Download every raw NFL play-by-play row for one season:

```bash
python3 -m app.data_foundation.ingestion 2024
```

This saves the complete raw season to:

```text
data/raw/nfl_play_by_play_2024_raw.csv.gz
```

The script also writes a metadata file next to the raw data:

```text
data/raw/nfl_play_by_play_2024_raw.metadata.json
```

The raw data is intentionally saved before normalization so the source columns can be inspected before deciding the analysis-ready schema mapping. The ingestion script validates the season range, checks required nflverse columns, limits the compressed source size, and only writes into `data/raw/`.

## Processed Play Data

Create the first curated play-level dataset for a season:

```bash
python3 -m app.data_foundation.cleaning 2024
```

This reads the raw NFL play-by-play file and writes:

```text
data/processed/nfl_plays_2024.parquet
```

## Run The App

Start the API:

```bash
uvicorn app.main:app --reload
```

## Ask A Question

The intended `/ask` workflow is data-extractor first:

1. A data extractor LLM receives the user's question and the approved analytics
   schema.
2. It decides whether local structured data can help answer the question.
3. If data is useful, it generates one SQL query against approved analytics
   views.
4. The app validates the SQL before execution.
5. The app executes valid read-only SQL with row limits.
6. The answer LLM receives the question and returned local analytics rows.
7. If no local data is needed or available, the answer LLM answers directly or
   says what context is missing.

The answer flow should not invent plays, injuries, quotes, roster context,
transaction news, or reporting that was not supplied. Current local data is
structured play-level NFL data; future retrieval or web search can add outside
context later.

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
  -d '{"question":"How efficient was Kansas City on third-and-long in the fourth quarter?","provider":"local"}'
```

In the target workflow, `/ask` first tries to extract useful local data. A
data-backed response should expose the extractor decision, generated SQL,
validation result, returned rows, and answer text. If the extractor decides no
local data is needed, the answer LLM can answer without SQL. If local data is
insufficient, the answer should state what extra context is missing.

Example data-backed question:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Which teams had the highest offensive EPA per play in 2024?","provider":"local"}'
```

### Inspect the LLM debug payload

To include the LLM call details in `/ask` responses and show them in the browser
UI, start the app with debug payloads enabled:

```bash
NFL_AI_DEBUG_PAYLOAD=1 uvicorn app.main:app --reload
```

Then ask a question in the UI and expand **LLM Debug Payload**. The `/ask` JSON
response should include a `debug_payload` object with the selected provider,
model, instructions, rendered input, and token limit. The normal `/ask` response
also includes `data_request` and `analytics` objects with the extractor
decision, generated SQL, validation result, row limit, and returned rows. The
`NFL_AI_DEBUG_PROMPT=1` is also supported.
