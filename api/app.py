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
from flask import Flask, jsonify, redirect, request, send_from_directory
from flask_cors import CORS

APP_NAME = "FundCompare API"
APP_VERSION = "1.0.0"
DATA_PROVIDER = "Yahoo Finance"

VALID_PERIODS = {"1mo", "3mo", "6mo", "1y", "2y", "5y"}

VALID_RANKING_CRITERIA = {
    "precio_cierre",
    "rentabilidad_acumulada",
    "cagr",
    "volatilidad_anual",
    "sharpe_ratio",
    "sortino_ratio",
    "max_drawdown",
    "momentum_20d",
    "rsi_14",
    "bollinger_score",
    "distancia_sma50",
    "volumen_actual",
    "volumen_medio_20d",
}

VALID_ALERT_METRICS = VALID_RANKING_CRITERIA

BASE_DIR = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = BASE_DIR / "dashboard"
CACHE_DIR = Path(tempfile.gettempdir()) / "fundcompare-yfinance-cache"

CACHE_DIR.mkdir(parents=True, exist_ok=True)
yf.set_tz_cache_location(str(CACHE_DIR))

app = Flask(__name__)
CORS(app)

alerts_memory: list[dict] = []
next_alert_id = 1


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_period(period: str | None) -> str:
    if period in VALID_PERIODS:
        return period
    return "1y"


def safe_round(value: float | None, digits: int = 4) -> float | None:
    if value is None:
        return None
    if isinstance(value, (float, np.floating)) and np.isnan(value):
        return None
    return round(float(value), digits)


def build_error_fund(ticker: str, message: str) -> dict:
    return {
        "ticker": ticker,
        "precio_cierre": None,
        "rentabilidad_acumulada": None,
        "cagr": None,
        "volatilidad_anual": None,
        "sharpe_ratio": None,
        "sortino_ratio": None,
        "max_drawdown": None,
        "momentum_20d": None,
        "rsi_14": None,
        "sma_20": None,
        "sma_50": None,
        "distancia_sma50": None,
        "cruce_medias_alcista": None,
        "cruce_medias_bajista": None,
        "bollinger_mid": None,
        "bollinger_upper": None,
        "bollinger_lower": None,
        "bollinger_score": None,
        "rsi_sobrecompra": None,
        "rsi_sobreventa": None,
        "volatilidad_alta": None,
        "volumen_actual": None,
        "volumen_medio_20d": None,
        "volumen_superior_media": None,
        "signals": [],
        "comentarios_usuario": [],
        "observaciones": message,
        "error": True,
    }


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


# =========================
# METRICAS TECNICAS - MARISA
# =========================

def calculate_cagr(close_prices: pd.Series) -> float | None:
    """
    Calcula la rentabilidad anual compuesta.
    """
    if len(close_prices) < 2:
        return None

    days = (close_prices.index[-1] - close_prices.index[0]).days

    if days <= 0:
        return None

    years = days / 365.25
    cagr = (close_prices.iloc[-1] / close_prices.iloc[0]) ** (1 / years) - 1

    return float(cagr)


def calculate_rsi(close_prices: pd.Series, window: int = 14) -> float | None:
    """
    Calcula el RSI usando suavizado de Wilder.
    """
    if len(close_prices) < window + 1:
        return None

    delta = close_prices.diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)

    avg_gain = gains.ewm(alpha=1 / window, adjust=False).mean()
    avg_loss = losses.ewm(alpha=1 / window, adjust=False).mean()

    last_gain = avg_gain.iloc[-1]
    last_loss = avg_loss.iloc[-1]

    if pd.isna(last_gain) or pd.isna(last_loss):
        return None

    if last_loss == 0:
        return 100.0

    rs = last_gain / last_loss
    rsi = 100 - (100 / (1 + rs))

    return float(rsi)


def calculate_sma(close_prices: pd.Series, window: int) -> float | None:
    """
    Calcula una media movil simple.
    """
    if len(close_prices) < window:
        return None

    sma = close_prices.rolling(window=window).mean().iloc[-1]

    if pd.isna(sma):
        return None

    return float(sma)


def calculate_momentum(close_prices: pd.Series, window: int = 20) -> float | None:
    """
    Calcula el momentum a 20 sesiones.
    """
    if len(close_prices) < window + 1:
        return None

    momentum = (close_prices.iloc[-1] / close_prices.iloc[-(window + 1)]) - 1

    return float(momentum)


def calculate_bollinger(close_prices: pd.Series, window: int = 20) -> dict:
    """
    Calcula las bandas de Bollinger y un score entre 0 y 1.
    """
    if len(close_prices) < window:
        return {
            "bollinger_mid": None,
            "bollinger_upper": None,
            "bollinger_lower": None,
            "bollinger_score": None,
        }

    rolling_mean = close_prices.rolling(window=window).mean()
    rolling_std = close_prices.rolling(window=window).std(ddof=0)

    mid = rolling_mean.iloc[-1]
    std = rolling_std.iloc[-1]

    if pd.isna(mid) or pd.isna(std):
        return {
            "bollinger_mid": None,
            "bollinger_upper": None,
            "bollinger_lower": None,
            "bollinger_score": None,
        }

    upper = mid + 2 * std
    lower = mid - 2 * std
    current_price = float(close_prices.iloc[-1])

    if upper == lower:
        score = 0.5
    else:
        score = (current_price - float(lower)) / (float(upper) - float(lower))
        score = max(0.0, min(1.0, score))

    return {
        "bollinger_mid": float(mid),
        "bollinger_upper": float(upper),
        "bollinger_lower": float(lower),
        "bollinger_score": float(score),
    }


def calculate_volume_metrics(history: pd.DataFrame) -> dict:
    """
    Calcula volumen actual, volumen medio de 20 sesiones
    y si el volumen actual supera su media.
    """
    if "Volume" not in history.columns:
        return {
            "volumen_actual": None,
            "volumen_medio_20d": None,
            "volumen_superior_media": None,
        }

    volume_data = history["Volume"]

    if isinstance(volume_data, pd.DataFrame):
        volume_data = volume_data.iloc[:, 0]

    volume_series = pd.to_numeric(volume_data, errors="coerce").dropna()

    if volume_series.empty:
        return {
            "volumen_actual": None,
            "volumen_medio_20d": None,
            "volumen_superior_media": None,
        }

    volumen_actual = float(volume_series.iloc[-1])

    volumen_medio_20d = (
        float(volume_series.rolling(window=20).mean().iloc[-1])
        if len(volume_series) >= 20
        else None
    )

    volumen_superior_media = (
        volumen_medio_20d is not None and volumen_actual > volumen_medio_20d
    )

    return {
        "volumen_actual": safe_round(volumen_actual, 0),
        "volumen_medio_20d": safe_round(volumen_medio_20d, 0),
        "volumen_superior_media": volumen_superior_media,
    }


def build_signal_flags(
    total_return: float,
    annual_volatility: float,
    momentum_20d: float | None,
    rsi_14: float | None,
    sma_20: float | None,
    sma_50: float | None,
) -> dict:
    """
    Genera señales booleanas a partir de las metricas tecnicas.
    Se mantienen los nombres originales para no romper otros bloques.
    """
    return {
        "cruce_medias_alcista": (
            sma_20 is not None and sma_50 is not None and sma_20 > sma_50
        ),
        "cruce_medias_bajista": (
            sma_20 is not None and sma_50 is not None and sma_20 < sma_50
        ),
        "rsi_sobrecompra": rsi_14 is not None and rsi_14 > 70,
        "rsi_sobreventa": rsi_14 is not None and rsi_14 < 30,
        "volatilidad_alta": annual_volatility > 0.35,
        "momentum_alcista": momentum_20d is not None and momentum_20d > 0.05,
        "momentum_bajista": momentum_20d is not None and momentum_20d < -0.05,
        "rentabilidad_negativa": total_return < 0,
    }


def build_signals_and_comments(
    flags: dict,
    bollinger_score: float | None,
) -> tuple[list[str], list[str]]:
    """
    Devuelve:
    - signals: etiquetas tecnicas reutilizables.
    - comentarios_usuario: mensajes legibles para interfaz o alertas.
    """
    signals: list[str] = []
    comentarios_usuario: list[str] = []

    if flags["volatilidad_alta"]:
        signals.append("volatilidad_alta")
        comentarios_usuario.append("Accion con elevada volatilidad.")

    if flags["momentum_alcista"]:
        signals.append("momentum_alcista")
        comentarios_usuario.append("La accion se encuentra en momento alcista.")
    elif flags["momentum_bajista"]:
        signals.append("momentum_bajista")
        comentarios_usuario.append(
            "La accion muestra perdida de impulso o momento bajista."
        )

    if flags["cruce_medias_alcista"]:
        signals.append("cruce_medias_alcista")
        comentarios_usuario.append(
            "La media corta se situa por encima de la media larga, indicando tendencia alcista."
        )
    elif flags["cruce_medias_bajista"]:
        signals.append("cruce_medias_bajista")
        comentarios_usuario.append(
            "La media corta se situa por debajo de la media larga, indicando tendencia bajista."
        )

    if flags["rsi_sobrecompra"]:
        signals.append("rsi_sobrecompra")
        comentarios_usuario.append("Posible situacion de sobrecompra.")
    elif flags["rsi_sobreventa"]:
        signals.append("rsi_sobreventa")
        comentarios_usuario.append("Posible situacion de sobreventa.")

    if bollinger_score is not None:
        if bollinger_score >= 0.9:
            signals.append("bollinger_cerca_banda_superior")
            comentarios_usuario.append(
                "El precio se situa cerca de la banda superior de Bollinger."
            )
        elif bollinger_score <= 0.1:
            signals.append("bollinger_cerca_banda_inferior")
            comentarios_usuario.append(
                "El precio se situa cerca de la banda inferior de Bollinger."
            )

    if flags["rentabilidad_negativa"]:
        signals.append("rentabilidad_negativa")
        comentarios_usuario.append(
            "El activo acumula rentabilidad negativa en el periodo analizado."
        )

    if not comentarios_usuario:
        comentarios_usuario.append(
            "Comportamiento sin senales tecnicas destacadas en el periodo analizado."
        )

    return signals, comentarios_usuario


def calculate_technical_metrics(
    close_prices: pd.Series,
    total_return: float,
    annual_volatility: float,
) -> dict:
    """
    Funcion principal que agrupa todas las metricas tecnicas adicionales.
    """
    current_price = float(close_prices.iloc[-1])

    momentum_20d = calculate_momentum(close_prices, window=20)
    rsi_14 = calculate_rsi(close_prices, window=14)
    sma_20 = calculate_sma(close_prices, window=20)
    sma_50 = calculate_sma(close_prices, window=50)
    bollinger_data = calculate_bollinger(close_prices, window=20)

    distancia_sma50 = (
        (current_price / sma_50) - 1
        if sma_50 is not None and sma_50 != 0
        else None
    )

    flags = build_signal_flags(
        total_return=total_return,
        annual_volatility=annual_volatility,
        momentum_20d=momentum_20d,
        rsi_14=rsi_14,
        sma_20=sma_20,
        sma_50=sma_50,
    )

    signals, comentarios_usuario = build_signals_and_comments(
        flags=flags,
        bollinger_score=bollinger_data["bollinger_score"],
    )

    if distancia_sma50 is not None:
        comentarios_usuario.append(
            f"La accion cotiza un {safe_round(distancia_sma50 * 100, 2)}% respecto a su media de 50 sesiones."
        )

    return {
        "momentum_20d": safe_round(momentum_20d),
        "rsi_14": safe_round(rsi_14, 2),
        "sma_20": safe_round(sma_20, 2),
        "sma_50": safe_round(sma_50, 2),
        "distancia_sma50": safe_round(distancia_sma50),
        "cruce_medias_alcista": flags["cruce_medias_alcista"],
        "cruce_medias_bajista": flags["cruce_medias_bajista"],
        "bollinger_mid": safe_round(bollinger_data["bollinger_mid"], 2),
        "bollinger_upper": safe_round(bollinger_data["bollinger_upper"], 2),
        "bollinger_lower": safe_round(bollinger_data["bollinger_lower"], 2),
        "bollinger_score": safe_round(bollinger_data["bollinger_score"]),
        "rsi_sobrecompra": flags["rsi_sobrecompra"],
        "rsi_sobreventa": flags["rsi_sobreventa"],
        "volatilidad_alta": flags["volatilidad_alta"],
        "signals": signals,
        "comentarios_usuario": comentarios_usuario,
    }


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
        cagr = calculate_cagr(close_prices)

        risk_free_rate = 0.02

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
            (annualized_return - risk_free_rate) / annual_volatility
            if annual_volatility > 0
            else None
        )

        sortino_ratio = (
            (annualized_return - risk_free_rate) / downside_volatility
            if downside_volatility > 0
            else None
        )

        technical_metrics = calculate_technical_metrics(
            close_prices=close_prices,
            total_return=total_return,
            annual_volatility=annual_volatility,
        )

        volume_metrics = calculate_volume_metrics(history)

        notes = [f"Metricas calculadas con {len(close_prices)} cierres diarios"]

        if downside_volatility == 0:
            notes.append("Sortino limitado por ausencia de retornos negativos")

        if technical_metrics["sma_50"] is None:
            notes.append(
                "No hay suficientes datos para calcular algunas metricas de ventana larga."
            )

        if volume_metrics["volumen_superior_media"]:
            notes.append("El volumen actual se situa por encima de su media de 20 sesiones.")

        notes.extend(technical_metrics["comentarios_usuario"])

        return {
            "ticker": ticker,
            "precio_cierre": safe_round(close_prices.iloc[-1], 2),
            "rentabilidad_acumulada": safe_round(total_return),
            "cagr": safe_round(cagr),
            "volatilidad_anual": safe_round(annual_volatility),
            "sharpe_ratio": safe_round(sharpe_ratio),
            "sortino_ratio": safe_round(sortino_ratio),
            "max_drawdown": safe_round(max_drawdown),
            **technical_metrics,
            **volume_metrics,
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
    return send_from_directory(DASHBOARD_DIR, "index.html")


@app.route("/dashboard/<path:filename>")
def dashboard_assets(filename: str) -> object:
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
    return jsonify(
        {
            "total": len(alerts_memory),
            "alertas": alerts_memory,
        }
    )


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

    metric_name = str(payload["metrica"])

    if metric_name not in VALID_ALERT_METRICS:
        return (
            jsonify(
                {
                    "error": "Metrica no valida",
                    "metricas_permitidas": sorted(VALID_ALERT_METRICS),
                }
            ),
            400,
        )

    try:
        threshold = float(payload["umbral"])
    except (TypeError, ValueError):
        return jsonify({"error": "El umbral debe ser numerico"}), 400

    if not np.isfinite(threshold):
        return jsonify({"error": "El umbral debe ser numerico"}), 400

    alert = {
        "id": next_alert_id,
        "ticker": str(payload["ticker"]).upper(),
        "metrica": metric_name,
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
            "metricas_recomendadas_para_alertas": [
                "volatilidad_anual",
                "sharpe_ratio",
                "sortino_ratio",
                "max_drawdown",
                "momentum_20d",
                "rsi_14",
                "bollinger_score",
                "distancia_sma50",
                "volumen_actual",
                "volumen_medio_20d",
            ],
        }
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
