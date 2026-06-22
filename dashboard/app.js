const state = {
  returnsChart: null,
  sharpeChart: null,
<<<<<<< HEAD
  cagrChart: null,
  maxDrawdownChart: null,
  sortinoChart: null,
  volatilityChart: null,
  rsiChart: null,
  cliente: null, // usuario logueado (de sessionStorage)
};

// Paleta común para semáforos de métricas
const COLOR_POSITIVE = "rgba(57, 201, 128, 0.8)";
const COLOR_WARNING = "rgba(244, 195, 93, 0.8)";
const COLOR_NEGATIVE = "rgba(255, 107, 107, 0.8)";
const COLOR_NEUTRAL = "rgba(47, 128, 237, 0.8)";

=======
  cliente: null, // usuario logueado (de sessionStorage)
};

>>>>>>> a9d9f421bb71c827b243bd59c063aafabae7e639
// ── Sesión ──
function getSession() {
  try {
    return JSON.parse(sessionStorage.getItem("cliente"));
  } catch {
    return null;
  }
}

function saveSession(cliente) {
  sessionStorage.setItem("cliente", JSON.stringify(cliente));
  state.cliente = cliente;
}

function clearSession() {
  sessionStorage.removeItem("cliente");
  state.cliente = null;
}

// Redirigir a login si no hay sesión
state.cliente = getSession();
if (!state.cliente) {
  window.location.href = "/dashboard/auth";
}

const elements = {
  apiStatus: document.getElementById("apiStatus"),
  dataProvider: document.getElementById("dataProvider"),
  lastQuery: document.getElementById("lastQuery"),
  assetCount: document.getElementById("assetCount"),
  feedbackMessage: document.getElementById("feedbackMessage"),
  compareForm: document.getElementById("compareForm"),
  tickersInput: document.getElementById("tickersInput"),
  periodInput: document.getElementById("periodInput"),
  comparisonTableBody: document.getElementById("comparisonTableBody"),
  rankingSharpe: document.getElementById("rankingSharpe"),
  rankingReturn: document.getElementById("rankingReturn"),
  alertForm: document.getElementById("alertForm"),
  alertsList: document.getElementById("alertsList"),
  telegramButton: document.getElementById("telegramButton"),
  telegramLinkButton: document.getElementById("telegramLinkButton"),
  telegramGroup: document.getElementById("telegramGroup"),
  subscribeButton: document.getElementById("subscribeButton"),
  unsubscribeButton: document.getElementById("unsubscribeButton"),
  userProfileWrapper: document.getElementById("userProfileWrapper"),
  userProfileButton: document.getElementById("userProfileButton"),
  userProfilePanel: document.getElementById("userProfilePanel"),
  profileName: document.getElementById("profileName"),
  profileEmail: document.getElementById("profileEmail"),
  profileCountry: document.getElementById("profileCountry"),
  profilePhone: document.getElementById("profilePhone"),
  profileTelegram: document.getElementById("profileTelegram"),
  logoutButton: document.getElementById("logoutButton"),
  etfSearchInput: document.getElementById("etfSearchInput"),
  etfDropdown: document.getElementById("etfDropdown"),
  etfSelectedTags: document.getElementById("etfSelectedTags"),
  saveFavoritesBtn: document.getElementById("saveFavoritesBtn"),
};

function setFeedback(message, tone = "default") {
  elements.feedbackMessage.textContent = message;
  elements.feedbackMessage.className = "feedback";
  if (tone === "success") {
    elements.feedbackMessage.classList.add("metric-positive");
  } else if (tone === "error") {
    elements.feedbackMessage.classList.add("metric-negative");
  } else if (tone === "warning") {
    elements.feedbackMessage.classList.add("metric-warning");
  }
}

function formatNumber(value) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "N/A";
  }
  return Number(value).toFixed(2);
}

function formatPercent(value) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "N/A";
  }
  return `${(Number(value) * 100).toFixed(2)}%`;
}

function formatDate(value) {
  if (!value) {
    return "-";
  }
  return new Date(value).toLocaleString("es-ES");
}

function metricClass(type, value) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "metric-empty";
  }

  if (type === "rentabilidad") {
    return value >= 0 ? "metric-positive" : "metric-negative";
  }

  if (type === "sharpe") {
    if (value > 1) {
      return "metric-positive";
    }
    if (value >= 0) {
      return "metric-warning";
    }
    return "metric-negative";
  }

  if (type === "drawdown") {
    return value < -0.2 ? "metric-negative" : "metric-warning";
  }

  return "";
}

function buildMetricCell(value, formatter, className = "") {
  const safeClass = className ? ` class="${className}"` : "";
  return `<td${safeClass}>${formatter(value)}</td>`;
}

function renderComparisonTable(funds) {
  if (!funds.length) {
    elements.comparisonTableBody.innerHTML =
      '<tr><td colspan="7" class="metric-empty">No hay resultados para mostrar.</td></tr>';
    return;
  }

  elements.comparisonTableBody.innerHTML = funds
    .map((fund) => {
      if (fund.error) {
        return `
          <tr>
            <td>${fund.ticker}</td>
            <td colspan="6" class="metric-negative">${fund.observaciones}</td>
          </tr>
        `;
      }

      return `
        <tr>
          <td>${fund.ticker}</td>
          ${buildMetricCell(fund.precio_cierre, formatNumber)}
          ${buildMetricCell(
            fund.rentabilidad_acumulada,
            formatPercent,
            metricClass("rentabilidad", fund.rentabilidad_acumulada)
          )}
          ${buildMetricCell(fund.volatilidad_anual, formatPercent)}
          ${buildMetricCell(
            fund.sharpe_ratio,
            formatNumber,
            metricClass("sharpe", fund.sharpe_ratio)
          )}
          ${buildMetricCell(fund.sortino_ratio, formatNumber)}
          ${buildMetricCell(
            fund.max_drawdown,
            formatPercent,
            metricClass("drawdown", fund.max_drawdown)
          )}
          ${buildMetricCell(fund.cagr, formatPercent)}
          ${buildMetricCell(fund.momentum_20d, formatPercent)}
          ${buildMetricCell(fund.rsi_14, formatNumber)}
          ${buildMetricCell(fund.bollinger_score, formatNumber)}
          ${buildMetricCell(fund.sma_20, formatNumber)}
          ${buildMetricCell(fund.sma_50, formatNumber)}
          ${buildMetricCell(fund.volumen_actual, formatNumber)}
        </tr>
      `;
    })
    .join("");
}

function renderRanking(target, ranking, formatter) {
  if (!ranking.length) {
    target.innerHTML = '<li class="metric-empty">Sin datos disponibles.</li>';
    return;
  }

  target.innerHTML = ranking
    .map((item) => `<li><strong>${item.ticker}</strong> · ${formatter(item.valor)}</li>`)
    .join("");
}

function destroyChart(chart) {
  if (chart) {
    chart.destroy();
  }
}

function buildBarChart(canvasId, label, labels, values, colors) {
  const canvas = document.getElementById(canvasId);
  if (!window.Chart) {
    return null;
  }

  return new Chart(canvas, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label,
          data: values,
          backgroundColor: colors,
          borderRadius: 8,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          display: false,
        },
      },
      scales: {
        x: {
          ticks: { color: "#edf3ff" },
          grid: { color: "rgba(255,255,255,0.05)" },
        },
        y: {
          ticks: { color: "#8f9bb2" },
          grid: { color: "rgba(255,255,255,0.05)" },
        },
      },
    },
  });
}

// Funciones para determinar el color de las métricas adicionales
function colorForCagr(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return COLOR_NEUTRAL;
  return COLOR_POSITIVE;   // Siempre verde
}

function colorForDrawdown(value) {
  // Esta se queda EXACTAMENTE igual, manteniendo la lógica de riesgo
  if (value === null || value === undefined || Number.isNaN(value)) return COLOR_NEUTRAL;
  if (value > -0.1) return COLOR_POSITIVE;   // caída menor al 10% (verde)
  if (value > -0.2) return COLOR_WARNING;    // entre -10% y -20% (amarillo/naranja)
  return COLOR_NEGATIVE;                     // peor que -20% (rojo)
}

function colorForSortino(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return COLOR_NEUTRAL;
  return COLOR_POSITIVE;   // Siempre verde
}

function colorForVolatility(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return COLOR_NEUTRAL;
  return COLOR_POSITIVE;   // Siempre verde
}

function colorForRsi(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return COLOR_NEUTRAL;
  return COLOR_POSITIVE;   // Siempre verde
}

function renderCharts(funds) {
  const validFunds = funds.filter((fund) => !fund.error);
  const labels = validFunds.map((fund) => fund.ticker);

  destroyChart(state.returnsChart);
  destroyChart(state.sharpeChart);
// Añadir las destrucciones de los otros gráficos si existen
  destroyChart(state.cagrChart);
  destroyChart(state.maxDrawdownChart);
  destroyChart(state.sortinoChart);
  destroyChart(state.volatilityChart);
  destroyChart(state.rsiChart);

  state.returnsChart = buildBarChart(
    "returnsChart",
    "Rentabilidad acumulada (%)",
    labels,
    validFunds.map((fund) => (fund.rentabilidad_acumulada ?? 0) * 100),
    validFunds.map((fund) =>
      (fund.rentabilidad_acumulada ?? 0) >= 0 ? COLOR_POSITIVE : COLOR_NEGATIVE
    )
  );

  state.sharpeChart = buildBarChart(
    "sharpeChart",
    "Sharpe Ratio",
    labels,
    validFunds.map((fund) => fund.sharpe_ratio ?? 0),
    validFunds.map((fund) => {
// Mantener la misma lógica de colores que en la tabla
      if ((fund.sharpe_ratio ?? -1) > 1) return COLOR_POSITIVE;
      if ((fund.sharpe_ratio ?? -1) >= 0) return COLOR_WARNING;
      return COLOR_NEGATIVE;
    })
  );

  state.cagrChart = buildBarChart(
    "cagrChart",
    "CAGR (%)",
    labels,
    validFunds.map((fund) => (fund.cagr ?? 0) * 100),
    validFunds.map((fund) => colorForCagr(fund.cagr))
  );

  state.maxDrawdownChart = buildBarChart(
    "maxDrawdownChart",
    "Max Drawdown (%)",
    labels,
    validFunds.map((fund) => (fund.max_drawdown ?? 0) * 100),
    validFunds.map((fund) => colorForDrawdown(fund.max_drawdown))
  );

  state.sortinoChart = buildBarChart(
    "sortinoChart",
    "Sortino Ratio",
    labels,
    validFunds.map((fund) => fund.sortino_ratio ?? 0),
    validFunds.map((fund) => colorForSortino(fund.sortino_ratio))
  );

  state.volatilityChart = buildBarChart(
    "volatilityChart",
    "Volatilidad anual (%)",
    labels,
    validFunds.map((fund) => (fund.volatilidad_anual ?? 0) * 100),
    validFunds.map((fund) => colorForVolatility(fund.volatilidad_anual))
  );

  state.rsiChart = buildBarChart(
    "rsiChart",
    "RSI (14)",
    labels,
    validFunds.map((fund) => fund.rsi_14 ?? 0),
    validFunds.map((fund) => colorForRsi(fund.rsi_14))
  );
}

async function fetchHealth() {
  try {
    const response = await fetch("/api/v1/health");
    const data = await response.json();
    elements.apiStatus.textContent = data.status;
    elements.dataProvider.textContent = data.data_provider;
  } catch (error) {
    elements.apiStatus.textContent = "error";
    elements.dataProvider.textContent = "No disponible";
    setFeedback("No se pudo conectar con la API.", "error");
  }
}

async function loadComparison() {
  const tickers = elements.tickersInput.value.trim();
  const period = elements.periodInput.value;
  setFeedback("Consultando Yahoo Finance...", "warning");

  try {
    const response = await fetch(
      `/api/v1/comparar?tickers=${encodeURIComponent(tickers)}&periodo=${encodeURIComponent(period)}`
    );
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "No se pudo completar la comparacion");
    }

    renderComparisonTable(data.fondos);
    renderRanking(elements.rankingSharpe, data.ranking_sharpe, formatNumber);
    renderRanking(elements.rankingReturn, data.ranking_rentabilidad, formatPercent);
    renderCharts(data.fondos);

    elements.lastQuery.textContent = formatDate(data.fecha_consulta);
    elements.assetCount.textContent = String(data.fondos.length);

    const failedFunds = data.fondos.filter((fund) => fund.error).length;
    if (failedFunds > 0) {
      setFeedback(
        `Comparacion completada con ${failedFunds} ticker(s) con incidencia.`,
        "warning"
      );
    } else {
      setFeedback("Comparacion completada correctamente.", "success");
    }
  } catch (error) {
    destroyChart(state.returnsChart);
    destroyChart(state.sharpeChart);
// Añadir destrucción de los otros gráficos si existen
    destroyChart(state.cagrChart);
    destroyChart(state.maxDrawdownChart);
    destroyChart(state.sortinoChart);
    destroyChart(state.volatilityChart);
    destroyChart(state.rsiChart);
    renderComparisonTable([]);
    renderRanking(elements.rankingSharpe, [], formatNumber);
    renderRanking(elements.rankingReturn, [], formatPercent);
    elements.assetCount.textContent = "0";
    setFeedback(error.message, "error");
  }
}

async function loadAlerts() {
  try {
    const response = await fetch("/api/v1/alertas", { credentials: "include" });
    const data = await response.json();

    if (!data.alertas.length) {
      elements.alertsList.innerHTML =
        '<li class="metric-empty">No hay alertas creadas todavia.</li>';
      return;
    }

    elements.alertsList.innerHTML = data.alertas
      .map(
        (alert) => `
          <li class="alert-item">
            <div class="alert-copy">
              <strong>${alert.ticker}</strong> · ${alert.metrica} ${alert.condicion} ${alert.umbral} · ${alert.periodo || "1mo"}
            </div>
            <button class="delete-button" type="button" data-alert-id="${alert.id}">
              Eliminar
            </button>
          </li>
        `
      )
      .join("");
  } catch (error) {
    elements.alertsList.innerHTML =
      '<li class="metric-negative">No se pudieron cargar las alertas.</li>';
  }
}

async function createAlert(event) {
  event.preventDefault();

  const payload = {
    ticker: document.getElementById("alertTicker").value.trim().toUpperCase(),
    metrica: document.getElementById("alertMetric").value,
    condicion: document.getElementById("alertCondition").value,
    umbral: Number(document.getElementById("alertThreshold").value),
    periodo: document.getElementById("alertPeriod").value,
  };

  try {
    const response = await fetch("/api/v1/alertas", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "No se pudo crear la alerta");
    }

    elements.alertForm.reset();
    await loadAlerts();
    setFeedback(`Alerta creada para ${data.alerta.ticker}.`, "success");
  } catch (error) {
    setFeedback(error.message, "error");
  }
}

async function deleteAlert(alertId) {
  try {
    const response = await fetch(`/api/v1/alertas/${alertId}`, { method: "DELETE", credentials: "include" });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "No se pudo eliminar la alerta");
    }
    await loadAlerts();
    setFeedback(`Alerta ${alertId} eliminada.`, "success");
  } catch (error) {
    setFeedback(error.message, "error");
  }
}

async function sendTelegramSummary() {
  try {
    const tickers = elements.tickersInput.value.trim();
    const periodo = elements.periodInput.value;
    const response = await fetch("/api/v1/telegram/enviar-resumen", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tickers, periodo }),
    });
    const data = await response.json();
    const tone = response.ok ? "success" : "warning";
    setFeedback(data.message, tone);
  } catch (error) {
    setFeedback("No se pudo preparar el resumen de Telegram.", "error");
  }
}

// ── Perfil de usuario ──
function applyProfile() {
  if (!state.cliente) return;
  elements.userProfileWrapper.hidden = false;
  elements.profileName.textContent = `${state.cliente.nombre} ${state.cliente.apellido || ""}`.trim();
  elements.profileEmail.textContent = state.cliente.email;
  elements.profileCountry.textContent = state.cliente.pais || "-";
  elements.profilePhone.textContent = state.cliente.telefono || "-";
  elements.profileTelegram.textContent = state.cliente.telegram_vinculado ? "Vinculado ✓" : "No vinculado";

  // Mostrar SOLO el botón que corresponda según BD
  if (state.cliente.telegram_vinculado) {
    elements.telegramGroup.hidden = false;
    elements.telegramLinkButton.hidden = true;
    // Suscripción: mostrar según estado
    if (state.cliente.telegram_suscrito) {
      elements.subscribeButton.hidden = true;
      elements.unsubscribeButton.hidden = false;
    } else {
      elements.subscribeButton.hidden = false;
      elements.unsubscribeButton.hidden = true;
    }
  } else {
    elements.telegramGroup.hidden = true;
    elements.telegramLinkButton.hidden = false;
    elements.subscribeButton.hidden = true;
    elements.unsubscribeButton.hidden = true;
  }
}

async function renderProfile() {
  // Siempre consultar la BD para tener el estado real de telegram_vinculado
  try {
    const response = await fetch("/api/v1/sesion");
    const data = await response.json();
    if (data.autenticado && data.cliente) {
      saveSession(data.cliente);
    } else {
      // Sesión del servidor caducada → redirigir a login
      clearSession();
      window.location.href = "/dashboard/auth";
      return;
    }
  } catch {
    // Si falla la red, usar datos locales como fallback
  }
  applyProfile();
}

// Toggle panel de perfil
elements.userProfileButton.addEventListener("click", (e) => {
  e.stopPropagation();
  elements.userProfilePanel.hidden = !elements.userProfilePanel.hidden;
});

document.addEventListener("click", (e) => {
  if (!elements.userProfileWrapper.contains(e.target)) {
    elements.userProfilePanel.hidden = true;
  }
});

// Cerrar sesión
elements.logoutButton.addEventListener("click", async () => {
  try {
    await fetch("/api/v1/logout", { method: "POST" });
  } catch {
    // silenciar
  }
  clearSession();
  window.location.href = "/dashboard/auth";
});

// ── Vincular Telegram ──
async function linkTelegram() {
  if (!state.cliente) return;

  try {
    const response = await fetch("/api/v1/telegram/generar-enlace", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cliente_id: state.cliente.id }),
    });
    const data = await response.json();

    if (!response.ok) {
      if (data.telegram_vinculado) {
        // Ya está vinculado, actualizar estado
        state.cliente.telegram_vinculado = true;
        saveSession(state.cliente);
        applyProfile();
        setFeedback("Tu Telegram ya está vinculado.", "success");
        return;
      }
      setFeedback(data.error || "No se pudo generar el enlace.", "error");
      return;
    }

    // Mostrar modal con el enlace
    showTelegramModal(data.enlace, data.expira);
  } catch (error) {
    setFeedback("Error al conectar con el servidor.", "error");
  }
}

function showTelegramModal(enlace, expira) {
  // Eliminar modal previo si existe
  const prev = document.querySelector(".telegram-modal-overlay");
  if (prev) prev.remove();

  const overlay = document.createElement("div");
  overlay.className = "telegram-modal-overlay";
  overlay.innerHTML = `
    <div class="telegram-modal">
      <h3>Vincular tu Telegram</h3>
      <p>Abre este enlace en Telegram para vincular tu cuenta. El enlace expira en 15 minutos.</p>
      <a href="${enlace}" target="_blank" rel="noopener">Abrir en Telegram</a>
      <span class="modal-timer">Expira: ${new Date(expira).toLocaleTimeString("es-ES")}</span>
      <button class="modal-close" type="button">Cerrar</button>
    </div>
  `;

  document.body.appendChild(overlay);

  overlay.querySelector(".modal-close").addEventListener("click", () => {
    overlay.remove();
    // Refrescar datos del cliente para ver si se vinculó
    refreshClienteData();
  });

  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) {
      overlay.remove();
      refreshClienteData();
    }
  });
}

async function refreshClienteData() {
  if (!state.cliente) return;
  try {
    const response = await fetch("/api/v1/sesion");
    const data = await response.json();
    if (data.autenticado && data.cliente) {
      saveSession(data.cliente);
      applyProfile();
      if (data.cliente.telegram_vinculado) {
        setFeedback("¡Telegram vinculado correctamente!", "success");
      }
    }
  } catch {
    // silenciar
  }
}

elements.telegramLinkButton.addEventListener("click", linkTelegram);

// ── ETF Multi-Select ──
let etfCatalog = [];
let selectedTickers = [];
let searchTimeout = null;

async function loadEtfCatalog() {
  try {
    const response = await fetch("/api/v1/etfs/catalogo?limit=500");
    const data = await response.json();
    etfCatalog = data.etfs || [];
  } catch {
    etfCatalog = [];
  }
}

async function loadFavorites() {
  if (!state.cliente) return;
  // Usar los favoritos que ya vienen en el objeto cliente
  const favs = state.cliente.etfs_favoritos || [];
  if (favs.length > 0) {
    selectedTickers = [...favs];
  } else {
    selectedTickers = ["SPY", "QQQ", "IWM"];
  }
  syncTickersInput();
  renderTags();
}

function syncTickersInput() {
  elements.tickersInput.value = selectedTickers.join(", ");
}

function renderTags() {
  const count = selectedTickers.length;
  elements.etfSelectedTags.innerHTML =
    selectedTickers
      .map(
        (t) =>
          `<span class="etf-tag">${t}<button class="etf-tag-remove" type="button" data-ticker="${t}">&times;</button></span>`
      )
      .join("") +
    `<span class="etf-tag-count">${count} activo${count !== 1 ? "s" : ""}</span>`;
}

function renderDropdown(query) {
  const q = query.toUpperCase();
  let filtered = etfCatalog;

  if (q) {
    filtered = etfCatalog.filter(
      (e) => e.ticker.includes(q) || e.nombre.toUpperCase().includes(q)
    );
  }

  if (filtered.length === 0) {
    elements.etfDropdown.innerHTML =
      '<div class="etf-dropdown-empty">No se encontraron ETFs</div>';
    elements.etfDropdown.hidden = false;
    return;
  }

  // Agrupar por categoría
  const grouped = {};
  for (const etf of filtered) {
    if (!grouped[etf.categoria]) grouped[etf.categoria] = [];
    grouped[etf.categoria].push(etf);
  }

  let html = "";
  for (const [cat, etfs] of Object.entries(grouped)) {
    html += `<div class="etf-dropdown-category">${cat}</div>`;
    for (const etf of etfs) {
      const isSelected = selectedTickers.includes(etf.ticker);
      html += `
        <div class="etf-dropdown-item ${isSelected ? "selected" : ""}" data-ticker="${etf.ticker}">
          <span class="etf-dropdown-ticker">${etf.ticker}</span>
          <span class="etf-dropdown-name">${etf.nombre}</span>
          <span class="etf-dropdown-check">${isSelected ? "✓" : ""}</span>
        </div>`;
    }
  }

  elements.etfDropdown.innerHTML = html;
  elements.etfDropdown.hidden = false;
}

function updateDropdownItem(ticker, selected) {
  const item = elements.etfDropdown.querySelector(`[data-ticker="${ticker}"]`);
  if (!item) return;
  if (selected) {
    item.classList.add("selected");
    const check = item.querySelector(".etf-dropdown-check");
    if (check) check.textContent = "✓";
  } else {
    item.classList.remove("selected");
    const check = item.querySelector(".etf-dropdown-check");
    if (check) check.textContent = "";
  }
}

function addTicker(ticker) {
  if (selectedTickers.includes(ticker)) return;
  if (selectedTickers.length >= 50) {
    setFeedback("Máximo 50 activos permitidos.", "warning");
    return;
  }
  selectedTickers.push(ticker);
  syncTickersInput();
  renderTags();
  updateDropdownItem(ticker, true);
}

function removeTicker(ticker) {
  const idx = selectedTickers.indexOf(ticker);
  if (idx < 0) return;
  selectedTickers.splice(idx, 1);
  syncTickersInput();
  renderTags();
  updateDropdownItem(ticker, false);
}

elements.etfSearchInput.addEventListener("input", () => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    renderDropdown(elements.etfSearchInput.value.trim());
  }, 150);
});

elements.etfSearchInput.addEventListener("focus", () => {
  renderDropdown(elements.etfSearchInput.value.trim());
});

// Evitar que Enter en el buscador envíe el formulario
elements.etfSearchInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") e.preventDefault();
});

document.addEventListener("click", (e) => {
  if (!document.getElementById("etfSelectWrapper").contains(e.target)) {
    elements.etfDropdown.hidden = true;
  }
});

elements.etfDropdown.addEventListener("mousedown", (e) => {
  // mousedown en vez de click: se dispara ANTES de cualquier reflow
  e.preventDefault(); // evita que el input pierda el foco
  e.stopPropagation();
  const item = e.target.closest("[data-ticker]");
  if (!item) return;
  const ticker = item.dataset.ticker;
  if (selectedTickers.includes(ticker)) {
    removeTicker(ticker);
  } else {
    addTicker(ticker);
  }
});

elements.etfSelectedTags.addEventListener("click", (e) => {
  e.stopPropagation();
  const btn = e.target.closest(".etf-tag-remove");
  if (btn) {
    removeTicker(btn.dataset.ticker);
  }
});

async function saveFavorites() {
  if (!state.cliente) return;
  try {
    const response = await fetch("/api/v1/cliente/etfs-favoritos", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ etfs: selectedTickers }),
    });
    const data = await response.json();
    if (response.ok) {
      state.cliente.etfs_favoritos = selectedTickers;
      saveSession(state.cliente);
      setFeedback(data.mensaje, "success");
    } else {
      setFeedback(data.error || "No se pudieron guardar los favoritos", "error");
    }
  } catch {
    setFeedback("Error al guardar favoritos.", "error");
  }
}

elements.saveFavoritesBtn.addEventListener("click", saveFavorites);

elements.compareForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await loadComparison();
});

elements.alertForm.addEventListener("submit", createAlert);

elements.alertsList.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-alert-id]");
  if (!button) {
    return;
  }
  await deleteAlert(button.dataset.alertId);
});

elements.telegramButton.addEventListener("click", sendTelegramSummary);

// ── Suscripción diaria ──
async function toggleSubscription(suscribir) {
  if (!state.cliente) return;
  try {
    const response = await fetch("/api/v1/telegram/suscripcion", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cliente_id: state.cliente.id, suscribir }),
    });
    const data = await response.json();
    if (response.ok) {
      setFeedback(data.mensaje, "success");
      // Refrescar estado desde BD para que los botones reflejen el cambio real
      await renderProfile();
    } else {
      setFeedback(data.error || "Error al cambiar suscripción", "error");
    }
  } catch {
    setFeedback("No se pudo cambiar la suscripción.", "error");
  }
}

elements.subscribeButton.addEventListener("click", () => toggleSubscription(true));
elements.unsubscribeButton.addEventListener("click", () => toggleSubscription(false));

// ── Init ──
(async () => {
  await loadEtfCatalog();
  await renderProfile();
  await loadFavorites();
  fetchHealth();
  loadComparison();
  loadAlerts();
})();
