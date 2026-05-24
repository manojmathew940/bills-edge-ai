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
const groundingBadge = document.querySelector("#grounding-badge");
const groundingDetail = document.querySelector("#grounding-detail");
const gameSummary = document.querySelector("#game-summary");
const gameMeta = document.querySelector("#game-meta");
const gameSummaryTitle = document.querySelector("#game-summary-title");
const finalScore = document.querySelector("#final-score");
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
  return useOpenAIInput.checked ? "openai" : "local";
}

function setProviderStatus(provider) {
  providerStatus.textContent = provider === "openai" ? "OpenAI model" : "Local model";
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
  metricsBox.textContent = "{}";
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

function formatMargin(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return "-";
  }
  return number > 0 ? `+${number}` : String(number);
}

function formatConversions(conversions) {
  if (!conversions) {
    return "-";
  }
  return `${conversions.conversions}/${conversions.attempts}`;
}

function createMetric(label, value) {
  const metric = document.createElement("div");
  metric.className = "metric";
  metric.innerHTML = `
    <span class="metric-label">${escapeHtml(label)}</span>
    <span class="metric-value">${escapeHtml(value)}</span>
  `;
  return metric;
}

function renderGameSummary(metrics) {
  const game = metrics.game;
  const turnovers = metrics.turnovers || {};
  const pressure = metrics.pressure || {};
  const explosives = metrics.explosives || {};
  const downs = metrics.downs || {};

  gameMeta.textContent = `${game.season} | Week ${game.week} | ${game.is_home ? "Home" : "Away"}`;
  gameSummaryTitle.textContent = `Bills vs ${game.opponent}`;
  finalScore.textContent = `BUF ${game.bills_score} - ${game.opponent} ${game.opponent_score}`;

  const values = [
    ["Turnover margin", formatMargin(turnovers.turnover_margin)],
    ["Sacks BUF / Opp", `${pressure.sacks_made ?? "-"} / ${pressure.sacks_taken ?? "-"}`],
    ["Explosive margin", formatMargin(explosives.explosive_play_margin)],
    [
      "Third down BUF / Opp",
      `${formatConversions(downs.bills_third_down)} / ${formatConversions(downs.opponent_third_down)}`,
    ],
  ];

  summaryMetrics.replaceChildren(...values.map(([label, value]) => createMetric(label, value)));
  gameSummary.hidden = false;
}

function renderGrounding(data) {
  const engine = data.plan && data.plan.engine;
  const hasGameMetrics = engine === "game_metrics" && data.metrics && data.metrics.game;

  if (hasGameMetrics) {
    setGrounding("Game metrics", "metrics", "Grounded in structured metrics from the resolved game.");
    renderGameSummary(data.metrics);
    return;
  }

  gameSummary.hidden = true;
  if (engine === "game_metrics") {
    setGrounding("Needs game", "clarify", "No game metric packet was produced. Add an opponent or week to identify one game.");
    return;
  }

  setGrounding("Direct answer", "direct", "No structured game metrics were used for this answer.");
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
    metricsBox.textContent = JSON.stringify(data.metrics || {}, null, 2);
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

useOpenAIInput.addEventListener("change", () => {
  setProviderStatus(getSelectedProvider());
});
