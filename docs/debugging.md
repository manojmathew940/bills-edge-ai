# LLM Debugging

Enable LLM call details in `/ask` responses and in the browser UI:

```bash
NFL_AI_DEBUG_PAYLOAD=1 uvicorn app.main:app --reload
```

The response then includes a `debug_payload` containing the selected provider,
model, instructions, rendered input, and token limit. The normal response also
contains `data_request` and `analytics` objects with the extraction decision,
generated SQL, validation result, row limit, and returned rows.

`NFL_AI_DEBUG_PROMPT=1` enables the same debug behavior and terminal prompt
output used by the extraction integration.

Debug output can contain the user's full question, generated SQL, analytics
rows, and complete model prompts. Do not enable it in a public production
environment or retain its output without applying the appropriate data-handling
controls.
