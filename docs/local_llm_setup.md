# Local LLM Setup

## Ollama

Install Ollama, download a model, and start it:

```bash
ollama run qwen2.5:7b-instruct
```

Exit the chat with `/bye`, then make sure the Ollama server is running:

```bash
ollama serve
```

Configure the app's local provider in `.env`:

```text
LOCAL_LLM_BASE_URL=http://127.0.0.1:11434/v1
LOCAL_LLM_MODEL=qwen2.5:7b-instruct
LOCAL_LLM_API_KEY=ollama
```

`LOCAL_LLM_API_KEY` is a placeholder. Ollama does not require a real API key,
but the OpenAI-compatible client expects a value.

## Ollama On Windows With The App In WSL

The preferred setup is WSL mirrored networking so Windows and WSL share
`localhost`.

1. Create or edit `%UserProfile%\.wslconfig`:

   ```ini
   [wsl2]
   networkingMode=mirrored
   ```

2. Restart WSL from PowerShell:

   ```powershell
   wsl --shutdown
   ```

3. Start Ollama from Windows and use the normal local endpoint in `.env`:

   ```text
   LOCAL_LLM_BASE_URL=http://127.0.0.1:11434/v1
   LOCAL_LLM_MODEL=qwen2.5:7b-instruct
   LOCAL_LLM_API_KEY=ollama
   ```

If mirrored networking is unavailable, use WSL's default NAT mode:

1. Set this persistent Windows user environment variable:

   ```text
   OLLAMA_HOST=0.0.0.0:11434
   ```

2. Restart the Ollama Windows application.
3. Find the Windows host IP from WSL:

   ```bash
   ip route show | grep -i default | awk '{ print $3 }'
   ```

4. Use that address in `.env`, for example:

   ```text
   LOCAL_LLM_BASE_URL=http://172.30.96.1:11434/v1
   ```

The NAT-mode host IP can change after WSL restarts, so mirrored networking is
more stable when it is available.
