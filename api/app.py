from __future__ import annotations

import json
import os
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

for proxy_var in (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
):
    os.environ.pop(proxy_var, None)

import numpy as np
import pandas as pd
import yfinance as yf
from flask import Flask, jsonify, redirect, request, send_from_directory, session
from flask_cors import CORS

# --- base de datos y autenticación ---
from configuracion import config
from models import Cliente, TelegramToken, db
from auth import auth_bp



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

# ---------------------------------------------------------------------------
# Telegram helpers
# ---------------------------------------------------------------------------


def _telegram_token() -> str:
    return os.environ.get("TELEGRAM_BOT_TOKEN", "")


def _telegram_chat_id() -> str:
    return os.environ.get("TELEGRAM_CHAT_ID", "")


def _get_bot_username(token: str) -> str | None:
    """Obtiene el username del bot llamando a getMe de la API de Telegram."""
    url = f"https://api.telegram.org/bot{token}/getMe"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            if data.get("ok"):
                return data["result"].get("username")
    except Exception:
        pass
    return None


def send_telegram_message(text: str, chat_id: str | None = None) -> dict:
    """Envía un mensaje al chat de Telegram indicado (o al global por defecto).

    Si se pasa chat_id, se envía a ese chat.  Si no, usa TELEGRAM_CHAT_ID.
    Requiere siempre la variable TELEGRAM_BOT_TOKEN.
    """
    token = _telegram_token()
    chat_id = chat_id or _telegram_chat_id()

    if not token:
        return {"ok": False, "error": "TELEGRAM_BOT_TOKEN no configurado"}
    if not chat_id:
        return {"ok": False, "error": "No se indicó chat_id ni está TELEGRAM_CHAT_ID configurado"}

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps(
        {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        return {"ok": False, "error": f"Telegram API {exc.code}: {body}"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _fmt_pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value * 100:.2f}%"


def _fmt_num(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.4f}"


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
        bool(volumen_actual > volumen_medio_20d)
        if volumen_medio_20d is not None
        else None
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
        "cruce_medias_alcista": bool(
            sma_20 is not None and sma_50 is not None and sma_20 > sma_50
        ),
        "cruce_medias_bajista": bool(
            sma_20 is not None and sma_50 is not None and sma_20 < sma_50
        ),
        "rsi_sobrecompra": bool(rsi_14 is not None and rsi_14 > 70),
        "rsi_sobreventa": bool(rsi_14 is not None and rsi_14 < 30),
        "volatilidad_alta": bool(annual_volatility > 0.35),
        "momentum_alcista": bool(momentum_20d is not None and momentum_20d > 0.05),
        "momentum_bajista": bool(momentum_20d is not None and momentum_20d < -0.05),
        "rentabilidad_negativa": bool(total_return < 0),
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


@app.route("/api/v1/telegram/estado")
def telegram_status() -> object:
    """Comprueba si las credenciales de Telegram están configuradas."""
    token_ok = bool(_telegram_token())
    chat_ok = bool(_telegram_chat_id())
    ready = token_ok and chat_ok
    return jsonify(
        {
            "configurado": ready,
            "token_presente": token_ok,
            "chat_id_presente": chat_ok,
            "mensaje": (
                "Telegram listo para envios"
                if ready
                else "Configura TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID en el entorno"
            ),
        }
    )


# ---------------------------------------------------------------------------
# Telegram — vinculación por usuario
# ---------------------------------------------------------------------------


@app.route("/api/v1/telegram/generar-enlace", methods=["POST"])
def telegram_generate_link() -> object:
    """Genera un deep link para que un usuario vincule su cuenta de Telegram.

    Body JSON:
        cliente_id (int): ID del cliente registrado.

    Devuelve:
        enlace  — URL tipo https://t.me/BOT?start=TOKEN
        token   — el token generado (solo para debug / logs internos)
        expira  — cuándo caduca
    """
    payload = request.get_json(silent=True) or {}
    cliente_id = payload.get("cliente_id")

    if not cliente_id:
        return jsonify({"error": "Falta cliente_id"}), 400

    cliente = Cliente.query.get(cliente_id)
    if not cliente:
        return jsonify({"error": "Cliente no encontrado"}), 404

    if cliente.telegram_chat_id:
        return jsonify({
            "error": "Este cliente ya tiene Telegram vinculado",
            "telegram_vinculado": True,
        }), 409

    # Invalidar tokens previos sin usar de este cliente
    TelegramToken.query.filter_by(cliente_id=cliente.id).delete()

    tk = TelegramToken.generate(cliente.id)
    db.session.add(tk)
    db.session.commit()

    bot_token = _telegram_token()
    # Obtener el username del bot para construir el deep link
    bot_username = _get_bot_username(bot_token) if bot_token else None

    if not bot_username:
        return jsonify({
            "error": "No se pudo obtener el username del bot. Verifica TELEGRAM_BOT_TOKEN.",
        }), 503

    return jsonify({
        "enlace": f"https://t.me/{bot_username}?start={tk.token}",
        "token": tk.token,
        "expira": tk.expires_at.isoformat(),
        "mensaje": "El usuario debe abrir este enlace en Telegram para vincular su cuenta.",
    }), 201


@app.route("/api/v1/telegram/vincular", methods=["POST"])
def telegram_link_user() -> object:
    """Vincula un chat_id de Telegram con un usuario a través del token.

    Este endpoint lo llama n8n cuando recibe el /start del bot.

    Body JSON:
        token   (str): token que el usuario envió con /start.
        chat_id (str): chat ID de Telegram extraído del update.

    Solo devuelve el nombre del usuario vinculado, no email ni otros datos.
    """
    payload = request.get_json(silent=True) or {}
    token_str = (payload.get("token") or "").strip()
    chat_id = str(payload.get("chat_id", "")).strip()

    if not token_str or not chat_id:
        return jsonify({"error": "Faltan token y/o chat_id"}), 400

    tk = TelegramToken.query.filter_by(token=token_str).first()

    if not tk:
        return jsonify({"error": "Token no válido o ya utilizado"}), 404

    if tk.is_expired:
        db.session.delete(tk)
        db.session.commit()
        return jsonify({"error": "El token ha expirado. Genera uno nuevo."}), 410

    # Comprobar que el chat_id no está ya usado por otro cliente
    existing = Cliente.query.filter_by(telegram_chat_id=chat_id).first()
    if existing and existing.id != tk.cliente_id:
        return jsonify({"error": "Este chat de Telegram ya está vinculado a otra cuenta"}), 409

    cliente = Cliente.query.get(tk.cliente_id)
    if not cliente:
        db.session.delete(tk)
        db.session.commit()
        return jsonify({"error": "Cliente no encontrado"}), 404

    cliente.telegram_chat_id = chat_id
    cliente.telegram_linked_at = datetime.now(timezone.utc)

    # Borrar el token usado
    db.session.delete(tk)
    db.session.commit()

    # Enviar mensaje de bienvenida al usuario
    send_telegram_message(
        f"✅ *¡Vinculación exitosa!*\n\n"
        f"Hola {cliente.nombre}, tu cuenta de FundCompare está vinculada.\n"
        f"Recibirás alertas y resúmenes de tus ETFs por aquí.",
        chat_id=chat_id,
    )

    return jsonify({
        "status": "linked",
        "cliente_id": cliente.id,
        "mensaje": f"Telegram vinculado correctamente para {cliente.nombre}",
    })


@app.route("/api/v1/telegram/desvincular", methods=["POST"])
def telegram_unlink_user() -> object:
    """Desvincula Telegram de un cliente.

    Body JSON:
        cliente_id (int): ID del cliente.
    """
    payload = request.get_json(silent=True) or {}
    cliente_id = payload.get("cliente_id")

    if not cliente_id:
        return jsonify({"error": "Falta cliente_id"}), 400

    cliente = Cliente.query.get(cliente_id)
    if not cliente:
        return jsonify({"error": "Cliente no encontrado"}), 404

    if not cliente.telegram_chat_id:
        return jsonify({"error": "Este cliente no tiene Telegram vinculado"}), 400

    cliente.telegram_chat_id = None
    cliente.telegram_linked_at = None
    db.session.commit()

    return jsonify({"status": "unlinked", "mensaje": "Telegram desvinculado"})


@app.route("/api/v1/telegram/configurar-tickers", methods=["POST"])
def telegram_set_tickers() -> object:
    """Configura los ETFs/tickers que un usuario quiere recibir por Telegram.

    Body JSON:
        cliente_id (int): ID del cliente.
        tickers    (str): tickers separados por comas, ej. "SPY,QQQ,IWM".
    """
    payload = request.get_json(silent=True) or {}
    cliente_id = payload.get("cliente_id")
    tickers_raw = (payload.get("tickers") or "").strip()

    if not cliente_id:
        return jsonify({"error": "Falta cliente_id"}), 400

    cliente = Cliente.query.get(cliente_id)
    if not cliente:
        return jsonify({"error": "Cliente no encontrado"}), 404

    if not cliente.telegram_chat_id:
        return jsonify({"error": "Vincula primero tu cuenta de Telegram"}), 400

    # Normalizar: mayúsculas, sin espacios, sin duplicados
    tickers_list = list(dict.fromkeys(
        t.strip().upper() for t in tickers_raw.split(",") if t.strip()
    ))
    cliente.telegram_tickers = ",".join(tickers_list) if tickers_list else None
    db.session.commit()

    return jsonify({
        "status": "ok",
        "tickers": tickers_list,
        "mensaje": f"Tickers actualizados: {', '.join(tickers_list)}" if tickers_list
                   else "Se han eliminado todos los tickers de alerta",
    })


@app.route("/api/v1/telegram/usuarios-suscritos")
def telegram_subscribed_users() -> object:
    """Devuelve la lista de usuarios con Telegram vinculado y sus tickers.

    Este endpoint es para que n8n itere y envíe mensajes personalizados.
    Solo expone lo mínimo necesario: id, nombre, chat_id y tickers.
    """
    clientes = Cliente.query.filter(
        Cliente.telegram_chat_id.isnot(None),
        Cliente.activo.is_(True),
        Cliente.telegram_tickers.isnot(None),
    ).all()

    return jsonify({
        "total": len(clientes),
        "usuarios": [
            {
                "cliente_id": c.id,
                "nombre": c.nombre,
                "chat_id": c.telegram_chat_id,
                "tickers": c.telegram_tickers,
            }
            for c in clientes
        ],
    })


@app.route("/api/v1/telegram/enviar-resumen", methods=["POST"])
def telegram_summary() -> object:
    """Calcula métricas para los tickers indicados y envía el resumen por Telegram.

    Body JSON opcional:
        tickers (str): tickers separados por comas. Por defecto "SPY,QQQ,IWM".
        periodo (str): período de datos. Por defecto "1y".
    """
    payload = request.get_json(silent=True) or {}
    raw_tickers = payload.get("tickers") or "SPY,QQQ,IWM"
    period = normalize_period(payload.get("periodo"))
    tickers = parse_tickers(raw_tickers)

    if not tickers:
        tickers = ["SPY", "QQQ", "IWM"]

    funds = [calculate_metrics(ticker, period) for ticker in tickers]

    lines = [
        f"\U0001f4ca *FundCompare \u00b7 Resumen {period}*",
        f"_{utc_now_iso()}_",
        "",
    ]

    for fund in funds:
        if fund.get("error"):
            lines.append(f"\u26a0\ufe0f *{fund['ticker']}*: {fund['observaciones']}")
            continue
        rent = fund["rentabilidad_acumulada"]
        emoji = "\U0001f4c8" if rent is not None and rent >= 0 else "\U0001f4c9"
        lines += [
            f"{emoji} *{fund['ticker']}*",
            f"  Rentabilidad: {_fmt_pct(fund['rentabilidad_acumulada'])}",
            f"  Sharpe: {_fmt_num(fund['sharpe_ratio'])}",
            f"  Sortino: {_fmt_num(fund['sortino_ratio'])}",
            f"  Max Drawdown: {_fmt_pct(fund['max_drawdown'])}",
            "",
        ]

    if funds:
        ranking_s = rank_funds(funds, "sharpe_ratio")
        ranking_r = rank_funds(funds, "rentabilidad_acumulada")
        if ranking_s:
            lines.append(f"\U0001f3c6 *Mejor Sharpe:* {ranking_s[0]['ticker']} ({_fmt_num(ranking_s[0]['valor'])})")
        if ranking_r:
            lines.append(f"\U0001f4b0 *Mejor Rentabilidad:* {ranking_r[0]['ticker']} ({_fmt_pct(ranking_r[0]['valor'])})")

    result = send_telegram_message("\n".join(lines))

    if result.get("ok"):
        return jsonify(
            {"status": "sent", "message": "Resumen enviado correctamente por Telegram"}
        )

    error_detail = result.get("error", "Error desconocido")
    if "no configurados" in error_detail:
        return jsonify(
            {
                "status": "not_configured",
                "message": "Configura TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID para activar el envio real",
                "detalle": error_detail,
            }
        ), 503

    return jsonify(
        {
            "status": "error",
            "message": f"No se pudo enviar el mensaje: {error_detail}",
        }
    ), 502


@app.route("/api/v1/telegram/verificar-alertas", methods=["POST"])
def verify_and_notify_alerts() -> object:
    """Evalúa todas las alertas en memoria contra métricas en tiempo real.

    Body JSON opcional:
        enviar_notificaciones (bool): si True, envía Telegram para cada alerta disparada.
            Por defecto False (solo evalúa, no envía).

    Respuesta:
        total_alertas       -- número total de alertas activas
        alertas_disparadas  -- cuántas se han activado
        detalle             -- lista de alertas disparadas con valor actual
        notificaciones_enviadas -- bool indicando si se enviaron mensajes
    """
    body = request.get_json(silent=True) or {}
    send_notifications = bool(body.get("enviar_notificaciones", False))

    triggered: list[dict] = []

    for alert in alerts_memory:
        metrics = calculate_metrics(alert["ticker"], "1mo")
        if metrics.get("error"):
            continue
        metric_value = metrics.get(alert["metrica"])
        if metric_value is None:
            continue

        condition = alert["condicion"]
        threshold = float(alert["umbral"])
        fired = (
            condition == ">" and metric_value > threshold
        ) or (
            condition == "<" and metric_value < threshold
        )

        if not fired:
            continue

        triggered.append(
            {
                "alerta": alert,
                "valor_actual": metric_value,
                "disparada": True,
            }
        )

        if send_notifications:
            msg = (
                f"\U0001f6a8 *Alerta FundCompare disparada*\n"
                f"Ticker: *{alert['ticker']}*\n"
                f"Metrica: {alert['metrica']}\n"
                f"Condicion: {alert['condicion']} {alert['umbral']}\n"
                f"Valor actual: {_fmt_num(metric_value)}"
            )
            send_telegram_message(msg)

    return jsonify(
        {
            "total_alertas": len(alerts_memory),
            "alertas_disparadas": len(triggered),
            "detalle": triggered,
            "notificaciones_enviadas": send_notifications and len(triggered) > 0,
        }
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)