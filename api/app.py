from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

for proxy_var in (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
):
    os.environ.pop(proxy_var, None)

import yfinance as yf
from flask import Flask, jsonify, redirect, request, send_from_directory, session
from flask_cors import CORS

# --- base de datos y autenticación ---
from configuracion import config
from models import db
from auth import auth_bp

APP_NAME = "FundCompare API"
APP_VERSION = "1.0.0"
DATA_PROVIDER = "Yahoo Finance"
VALID_PERIODS = {"1mo", "3mo", "6mo", "1y", "2y", "5y"}
VALID_RANKING_CRITERIA = {
    "precio_cierre",
    "rentabilidad_acumulada",
    "volatilidad_anual",
    "sharpe_ratio",
    "sortino_ratio",
    "max_drawdown",
}

BASE_DIR = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = BASE_DIR / "dashboard"
CACHE_DIR = Path(tempfile.gettempdir()) / "fundcompare-yfinance-cache"

CACHE_DIR.mkdir(parents=True, exist_ok=True)
yf.set_tz_cache_location(str(CACHE_DIR))

app = Flask(__name__)
CORS(app, supports_credentials=True)

# --- configuración y base de datos ---
entorno = os.environ.get("FLASK_ENV", "development")
app.config.from_object(config[entorno])

db.init_app(app)
app.register_blueprint(auth_bp)

with app.app_context():
    db.create_all()  # Crea las tablas si no existen (no borra datos existentes)

alerts_memory: list[dict] = []
next_alert_id = 1


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_period(period: str | None) -> str:
    if period in VALID_PERIODS:
        return period
    return "1y"


def build_error_fund(ticker: str, message: str) -> dict:
    return {
        "ticker": ticker,
        "precio_cierre": None,
        "rentabilidad_acumulada": None,
        "volatilidad_anual": None,
        "sharpe_ratio": None,
        "sortino_ratio": None,
        "max_drawdown": None,
        "observaciones": message,
        "error": True,
    }


def safe_round(value: float | None, digits: int = 4) -> float | None:
    if value is None:
        return None
    if isinstance(value, (float, np.floating)) and np.isnan(value):
        return None
    return round(float(value), digits)


def download_history(ticker: str, period: str) -> pd.DataFrame:
    history = yf.download(
        ticker,
        period=period,
        progress=False,
        auto_adjust=True,
        threads=False,
    )
    if history.empty:
        raise ValueError("No se encontraron datos para el ticker indicado")
    if "Close" not in history.columns:
        raise ValueError("Yahoo Finance no devolvio precios de cierre")
    return history


def extract_close_prices(history: pd.DataFrame, ticker: str) -> pd.Series:
    close_data = history["Close"]

    if isinstance(close_data, pd.DataFrame):
        if ticker in close_data.columns:
            close_data = close_data[ticker]
        else:
            close_data = close_data.iloc[:, 0]

    close_series = pd.to_numeric(close_data, errors="coerce").dropna()
    if close_series.empty:
        raise ValueError("Yahoo Finance no devolvio cierres validos")
    return close_series


def calculate_metrics(ticker: str, period: str) -> dict:
    try:
        history = download_history(ticker, period)
        close_prices = extract_close_prices(history, ticker)

        if len(close_prices) < 2:
            raise ValueError("No hay suficientes datos para calcular metricas")

        daily_returns = close_prices.pct_change().dropna()
        if daily_returns.empty:
            raise ValueError("No hay suficientes retornos diarios para el calculo")

        total_return = (close_prices.iloc[-1] / close_prices.iloc[0]) - 1
        annualized_return = daily_returns.mean() * 252
        annual_volatility = daily_returns.std(ddof=0) * np.sqrt(252)

        downside_returns = daily_returns[daily_returns < 0]
        downside_volatility = (
            downside_returns.std(ddof=0) * np.sqrt(252)
            if not downside_returns.empty
            else 0.0
        )

        running_max = close_prices.cummax()
        drawdowns = (close_prices / running_max) - 1
        max_drawdown = drawdowns.min()

        sharpe_ratio = (
            annualized_return / annual_volatility if annual_volatility > 0 else None
        )
        sortino_ratio = (
            annualized_return / downside_volatility if downside_volatility > 0 else None
        )

        notes = [f"Metricas calculadas con {len(close_prices)} cierres diarios"]
        if downside_volatility == 0:
            notes.append("Sortino limitado por ausencia de retornos negativos")

        return {
            "ticker": ticker,
            "precio_cierre": safe_round(close_prices.iloc[-1], 2),
            "rentabilidad_acumulada": safe_round(total_return),
            "volatilidad_anual": safe_round(annual_volatility),
            "sharpe_ratio": safe_round(sharpe_ratio),
            "sortino_ratio": safe_round(sortino_ratio),
            "max_drawdown": safe_round(max_drawdown),
            "observaciones": " | ".join(notes),
            "error": False,
        }
    except Exception as exc:
        return build_error_fund(ticker, str(exc))


def parse_tickers(raw_tickers: str | None) -> list[str]:
    if not raw_tickers:
        return []
    seen: set[str] = set()
    tickers: list[str] = []
    for item in raw_tickers.split(","):
        ticker = item.strip().upper()
        if ticker and ticker not in seen:
            tickers.append(ticker)
            seen.add(ticker)
    return tickers


def rank_funds(funds: list[dict], criterion: str) -> list[dict]:
    valid_funds = [
        fund
        for fund in funds
        if not fund.get("error") and fund.get(criterion) is not None
    ]
    ranked = sorted(valid_funds, key=lambda fund: fund[criterion], reverse=True)
    return [{"ticker": fund["ticker"], "valor": fund[criterion]} for fund in ranked]


@app.route("/")
def root() -> object:
    return redirect("/dashboard")


@app.route("/dashboard")
def dashboard_index() -> object:
    # Login obligatorio: si no hay sesión activa, redirige a la pantalla de auth.
    if not session.get("cliente_id"):
        return redirect("/dashboard/auth")
    return send_from_directory(DASHBOARD_DIR, "index.html")


@app.route("/dashboard/auth")
def dashboard_auth() -> object:
    return send_from_directory(DASHBOARD_DIR, "auth.html")


@app.route("/dashboard/<path:filename>")
def dashboard_assets(filename: str) -> object:
    # Los archivos estáticos (css/js) deben servirse siempre,
    # incluso sin sesión, o la propia pantalla de login no podría cargar su CSS/JS.
    return send_from_directory(DASHBOARD_DIR, filename)


@app.route("/api/v1/health")
def health() -> object:
    return jsonify(
        {
            "status": "Operativa",
            "app": APP_NAME,
            "data_provider": DATA_PROVIDER,
            "timestamp": utc_now_iso(),
            "version": APP_VERSION,
        }
    )


@app.route("/api/v1/comparar")
def compare_assets() -> object:
    tickers = parse_tickers(request.args.get("tickers"))
    period = normalize_period(request.args.get("periodo"))

    if not tickers:
        return jsonify({"error": "Debes indicar al menos un ticker"}), 400

    funds = [calculate_metrics(ticker, period) for ticker in tickers]

    return jsonify(
        {
            "fecha_consulta": utc_now_iso(),
            "periodo": period,
            "fondos": funds,
            "ranking_sharpe": rank_funds(funds, "sharpe_ratio"),
            "ranking_rentabilidad": rank_funds(funds, "rentabilidad_acumulada"),
        }
    )


@app.route("/api/v1/metricas/<ticker>")
def ticker_metrics(ticker: str) -> object:
    period = normalize_period(request.args.get("periodo"))
    metrics = calculate_metrics(ticker.upper(), period)
    status_code = 200 if not metrics.get("error") else 404
    return jsonify(metrics), status_code


@app.route("/api/v1/rankings")
def rankings() -> object:
    tickers = parse_tickers(request.args.get("tickers"))
    period = normalize_period(request.args.get("periodo"))
    criterion = request.args.get("criterio", "sharpe_ratio")

    if not tickers:
        return jsonify({"error": "Debes indicar al menos un ticker"}), 400

    if criterion not in VALID_RANKING_CRITERIA:
        return (
            jsonify(
                {
                    "error": "Criterio no valido",
                    "criterios_permitidos": sorted(VALID_RANKING_CRITERIA),
                }
            ),
            400,
        )

    funds = [calculate_metrics(ticker, period) for ticker in tickers]
    return jsonify(
        {
            "fecha_consulta": utc_now_iso(),
            "periodo": period,
            "criterio": criterion,
            "ranking": rank_funds(funds, criterion),
            "fondos": funds,
        }
    )


@app.route("/api/v1/alertas", methods=["GET"])
def list_alerts() -> object:
    return jsonify({"total": len(alerts_memory), "alertas": alerts_memory})


@app.route("/api/v1/alertas", methods=["POST"])
def create_alert() -> object:
    global next_alert_id

    payload = request.get_json(silent=True) or {}
    required_fields = ("ticker", "metrica", "condicion", "umbral")
    missing = [field for field in required_fields if payload.get(field) in (None, "")]

    if missing:
        return jsonify({"error": "Faltan campos obligatorios", "campos": missing}), 400

    if payload["condicion"] not in {">", "<"}:
        return jsonify({"error": "La condicion debe ser > o <"}), 400

    try:
        threshold = float(payload["umbral"])
    except (TypeError, ValueError):
        return jsonify({"error": "El umbral debe ser numerico"}), 400

    if not np.isfinite(threshold):
        return jsonify({"error": "El umbral debe ser numerico"}), 400

    alert = {
        "id": next_alert_id,
        "ticker": str(payload["ticker"]).upper(),
        "metrica": str(payload["metrica"]),
        "condicion": str(payload["condicion"]),
        "umbral": threshold,
        "creada_en": utc_now_iso(),
    }
    alerts_memory.append(alert)
    next_alert_id += 1

    return jsonify({"status": "created", "alerta": alert}), 201


@app.route("/api/v1/alertas/<int:alert_id>", methods=["DELETE"])
def delete_alert(alert_id: int) -> object:
    for index, alert in enumerate(alerts_memory):
        if alert["id"] == alert_id:
            deleted = alerts_memory.pop(index)
            return jsonify({"status": "deleted", "alerta": deleted})
    return jsonify({"error": "Alerta no encontrada"}), 404


@app.route("/api/v1/telegram/enviar-resumen", methods=["POST"])
def telegram_summary() -> object:
    return jsonify(
        {
            "status": "prepared",
            "message": "Integracion con Telegram preparada para fase posterior",
        }
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
