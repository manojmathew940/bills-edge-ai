const form = document.querySelector("#ask-form");
const askButton = document.querySelector("#ask-button");
const loading = document.querySelector("#loading");
const errorBox = document.querySelector("#error");
const answerBox = document.querySelector("#answer");
const metricsBox = document.querySelector("#metrics");
const debugPanel = document.querySelector("#debug-panel");
const debugPayloadBox = document.querySelector("#debug-payload");
const useOpenAIInput = document.querySelector("#use-openai");
const providerStatus = document.querySelector("#provider-status");

function setLoading(isLoading) {
  askButton.disabled = isLoading;
  loading.hidden = !isLoading;
}

function showError(message) {
  errorBox.textContent = message;
  errorBox.hidden = false;
}

function clearError() {
  errorBox.textContent = "";
  errorBox.hidden = true;
}

function setDebugPayload(debugPayload) {
  if (debugPayload) {
    debugPayloadBox.textContent = JSON.stringify(debugPayload, null, 2);
    debugPanel.hidden = false;
  } else {
    debugPayloadBox.textContent = "{}";
    debugPanel.hidden = true;
  }
}

function getSelectedProvider() {
  return useOpenAIInput.checked ? "openai" : "local";
}

function setProviderStatus(provider) {
  providerStatus.textContent = provider === "openai" ? "OpenAI" : "Local";
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderInlineMarkdown(value) {
  return escapeHtml(value)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>");
}

function renderAnswer(value) {
  const text = String(value || "").trim();

  if (!text) {
    answerBox.textContent = "No answer returned.";
    return;
  }

  const blocks = text.split(/\n{2,}/);
  const html = blocks
    .map((block) => {
      const lines = block.split("\n");
      const isList = lines.every((line) => line.trim().startsWith("- "));

      if (isList) {
        const items = lines
          .map((line) => `<li>${renderInlineMarkdown(line.trim().slice(2))}</li>`)
          .join("");
        return `<ul>${items}</ul>`;
      }

      return `<p>${renderInlineMarkdown(lines.join(" "))}</p>`;
    })
    .join("");

  answerBox.innerHTML = html;
}

async function askQuestion(payload) {
  const response = await fetch("/ask", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const detail = data.detail || {};
    const message = detail.error || detail || `Request failed with status ${response.status}`;
    const error = new Error(message);
    error.debugPayload = detail.debug_payload || detail.debug_prompt;
    throw error;
  }

  return data;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();
  setLoading(true);

  const formData = new FormData(form);
  const payload = {
    season: Number(formData.get("season")),
    question: String(formData.get("question")).trim(),
    provider: getSelectedProvider(),
  };

  answerBox.textContent = "";
  answerBox.classList.remove("empty");

  try {
    const data = await askQuestion(payload);
    renderAnswer(data.answer);
    metricsBox.textContent = JSON.stringify(data.metrics || {}, null, 2);
    setDebugPayload(data.debug_payload || data.debug_prompt);
    setProviderStatus(data.provider || payload.provider);
  } catch (error) {
    answerBox.textContent = "The answer will appear here after a successful request.";
    answerBox.classList.add("empty");
    setDebugPayload(error.debugPayload);
    showError(error.message);
  } finally {
    setLoading(false);
  }
});

useOpenAIInput.addEventListener("change", () => {
  setProviderStatus(getSelectedProvider());
});
