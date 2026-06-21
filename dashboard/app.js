const state = {
  returnsChart: null,
  sharpeChart: null,
};

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

function renderCharts(funds) {
  const validFunds = funds.filter((fund) => !fund.error);
  const labels = validFunds.map((fund) => fund.ticker);

  destroyChart(state.returnsChart);
  destroyChart(state.sharpeChart);

  state.returnsChart = buildBarChart(
    "returnsChart",
    "Rentabilidad acumulada",
    labels,
    validFunds.map((fund) => fund.rentabilidad_acumulada * 100),
    validFunds.map((fund) =>
      fund.rentabilidad_acumulada >= 0 ? "rgba(57, 201, 128, 0.8)" : "rgba(255, 107, 107, 0.8)"
    )
  );

  state.sharpeChart = buildBarChart(
    "sharpeChart",
    "Sharpe Ratio",
    labels,
    validFunds.map((fund) => fund.sharpe_ratio ?? 0),
    validFunds.map((fund) => {
      if ((fund.sharpe_ratio ?? -1) > 1) {
        return "rgba(57, 201, 128, 0.8)";
      }
      if ((fund.sharpe_ratio ?? -1) >= 0) {
        return "rgba(244, 195, 93, 0.8)";
      }
      return "rgba(255, 107, 107, 0.8)";
    })
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
    renderComparisonTable([]);
    renderRanking(elements.rankingSharpe, [], formatNumber);
    renderRanking(elements.rankingReturn, [], formatPercent);
    elements.assetCount.textContent = "0";
    setFeedback(error.message, "error");
  }
}

async function loadAlerts() {
  try {
    const response = await fetch("/api/v1/alertas");
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
              <strong>${alert.ticker}</strong> · ${alert.metrica} ${alert.condicion} ${alert.umbral}
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
  };

  try {
    const response = await fetch("/api/v1/alertas", {
      method: "POST",
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
    const response = await fetch(`/api/v1/alertas/${alertId}`, { method: "DELETE" });
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
    const response = await fetch("/api/v1/telegram/enviar-resumen", { method: "POST" });
    const data = await response.json();
    setFeedback(data.message, "success");
  } catch (error) {
    setFeedback("No se pudo preparar el resumen de Telegram.", "error");
  }
}

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

fetchHealth();
loadComparison();
loadAlerts();
