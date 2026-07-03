const form = document.querySelector("#ask-form");
const askButton = document.querySelector("#ask-button");
const loading = document.querySelector("#loading");
const errorBox = document.querySelector("#error");
const answerBox = document.querySelector("#answer");
const analyticsBox = document.querySelector("#analytics");
const debugPanel = document.querySelector("#debug-panel");
const debugPayloadBox = document.querySelector("#debug-payload");
const modelSelect = document.querySelector("#model");
const providerStatus = document.querySelector("#provider-status");
const groundingBadge = document.querySelector("#grounding-badge");
const groundingDetail = document.querySelector("#grounding-detail");
const gameSummary = document.querySelector("#game-summary");
const summaryMetrics = document.querySelector("#summary-metrics");

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
  return modelSelect.value;
}

function setProviderStatus(provider) {
  if (provider === "openai") {
    providerStatus.textContent = "OpenAI GPT-5.5";
    return;
  }
  if (provider === "local") {
    providerStatus.textContent = "Qwen 2.5 Local";
    return;
  }
  providerStatus.textContent = "Select model";
}

function setGrounding(label, style, detail) {
  groundingBadge.textContent = label;
  groundingBadge.className = `grounding-badge ${style}`;
  groundingDetail.textContent = detail || "";
  groundingDetail.hidden = !detail;
}

function resetResult() {
  clearError();
  setGrounding("Analyzing", "neutral", "");
  gameSummary.hidden = true;
  summaryMetrics.replaceChildren();
  analyticsBox.textContent = "{}";
  setDebugPayload(null);
  answerBox.textContent = "";
  answerBox.classList.remove("empty");
}

function escapeHtml(value) {
  return String(value)
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
    answerBox.classList.add("empty");
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
  answerBox.classList.remove("empty");
}

function renderGrounding(data) {
  const analytics = data.analytics || {};
  const rows = Array.isArray(analytics.rows) ? analytics.rows : [];

  gameSummary.hidden = true;
  summaryMetrics.replaceChildren();

  if (analytics.is_valid === true && rows.length > 0) {
    setGrounding(
      "SQL analytics",
      "metrics",
      `Grounded in ${rows.length} local analytics row${rows.length === 1 ? "" : "s"}.`
    );
    return;
  }

  if (analytics.is_valid === true) {
    setGrounding(
      "SQL analytics",
      "metrics",
      "Local analytics query succeeded but returned no rows."
    );
    return;
  }

  if (analytics.is_valid === false) {
    setGrounding(
      "Data unavailable",
      "clarify",
      analytics.validation_reason || "The local analytics query could not be used."
    );
    return;
  }

  setGrounding(
    "No local data used",
    "direct",
    "The extractor did not request local analytics data for this answer."
  );
}

function renderAnalyticsPayload(data) {
  analyticsBox.textContent = JSON.stringify(
    {
      data_request: data.data_request || null,
      analytics: data.analytics || null,
    },
    null,
    2
  );
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
  resetResult();
  setLoading(true);

  const formData = new FormData(form);
  const payload = {
    season: Number(formData.get("season")),
    question: String(formData.get("question")).trim(),
    provider: getSelectedProvider(),
  };

  try {
    const data = await askQuestion(payload);
    renderAnswer(data.answer);
    renderGrounding(data);
    renderAnalyticsPayload(data);
    setDebugPayload(data.debug_payload || data.debug_prompt);
    setProviderStatus(data.provider || payload.provider);
  } catch (error) {
    gameSummary.hidden = true;
    setGrounding("Unavailable", "clarify", "The analysis could not be completed.");
    answerBox.textContent = "No answer is available for this request.";
    answerBox.classList.add("empty");
    setDebugPayload(error.debugPayload);
    showError(error.message);
  } finally {
    setLoading(false);
  }
});

modelSelect.addEventListener("change", () => {
  setProviderStatus(getSelectedProvider());
});
