from __future__ import annotations

import numpy as np
import pandas as pd


def safe_round(value: float | None, digits: int = 4) -> float | None:
    """Redondea valores numéricos y devuelve None si el valor no es válido."""
    if value is None:
        return None
    if isinstance(value, (float, np.floating)) and np.isnan(value):
        return None
    return round(float(value), digits)


def calculate_momentum(close_prices: pd.Series, window: int = 20) -> float | None:
    """
    Calcula el momentum como variación porcentual entre el precio actual
    y el precio de hace 'window' sesiones.
    """
    if len(close_prices) < window + 1:
        return None

    momentum = (close_prices.iloc[-1] / close_prices.iloc[-(window + 1)]) - 1
    return float(momentum)


def calculate_rsi(close_prices: pd.Series, window: int = 14) -> float | None:
    """
    Calcula el RSI clásico de 'window' periodos.
    """
    if len(close_prices) < window + 1:
        return None

    delta = close_prices.diff()

    ganancias = delta.clip(lower=0)
    perdidas = -delta.clip(upper=0)

    media_ganancias = ganancias.rolling(window=window, min_periods=window).mean()
    media_perdidas = perdidas.rolling(window=window, min_periods=window).mean()

    if media_ganancias.empty or media_perdidas.empty:
        return None

    last_gain = media_ganancias.iloc[-1]
    last_loss = media_perdidas.iloc[-1]

    if pd.isna(last_gain) or pd.isna(last_loss):
        return None

    if last_loss == 0:
        return 100.0

    rs = last_gain / last_loss
    rsi = 100 - (100 / (1 + rs))
    return float(rsi)


def calculate_sma(close_prices: pd.Series, window: int) -> float | None:
    """
    Calcula una media móvil simple.
    """
    if len(close_prices) < window:
        return None

    sma = close_prices.rolling(window=window).mean().iloc[-1]

    if pd.isna(sma):
        return None

    return float(sma)


def calculate_bollinger(close_prices: pd.Series, window: int = 20) -> dict:
    """
    Calcula Bandas de Bollinger:
    - banda media
    - banda superior
    - banda inferior
    - bollinger_score: posición relativa del precio actual dentro de las bandas
      0   -> cerca de banda inferior
      0.5 -> zona media
      1   -> cerca de banda superior
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


def build_signal_flags(
    total_return: float,
    annual_volatility: float,
    momentum_20d: float | None,
    rsi_14: float | None,
    sma_20: float | None,
    sma_50: float | None,
) -> dict:
    """
    Genera señales booleanas a partir de las métricas calculadas.
    """
    return {
        "cruce_medias_alcista": (
            sma_20 is not None and sma_50 is not None and sma_20 > sma_50
        ),
        "cruce_medias_bajista": (
            sma_20 is not None and sma_50 is not None and sma_20 < sma_50
        ),
        "rsi_sobrecompra": (rsi_14 is not None and rsi_14 > 70),
        "rsi_sobreventa": (rsi_14 is not None and rsi_14 < 30),
        "volatilidad_alta": annual_volatility > 0.35,
        "momentum_alcista": (momentum_20d is not None and momentum_20d > 0.05),
        "momentum_bajista": (momentum_20d is not None and momentum_20d < -0.05),
        "rentabilidad_negativa": total_return < 0,
    }


def build_signals_and_comments(
    flags: dict,
    bollinger_score: float | None,
) -> tuple[list[str], list[str]]:
    """
    Devuelve:
    - signals: etiquetas técnicas reutilizables por backend/Telegram/frontend
    - comentarios_usuario: mensajes legibles para interfaz o alertas
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
            "La media corta se situa por encima de la media larga."
        )
    elif flags["cruce_medias_bajista"]:
        signals.append("cruce_medias_bajista")
        comentarios_usuario.append(
            "La media corta se situa por debajo de la media larga."
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
    Función principal del módulo.
    Recibe una serie de cierres y devuelve todas las métricas técnicas,
    señales y comentarios listos para reutilizar.
    """
    momentum_20d = calculate_momentum(close_prices, window=20)
    rsi_14 = calculate_rsi(close_prices, window=14)
    sma_20 = calculate_sma(close_prices, window=20)
    sma_50 = calculate_sma(close_prices, window=50)
    bollinger_data = calculate_bollinger(close_prices, window=20)

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

    return {
        "momentum_20d": safe_round(momentum_20d),
        "rsi_14": safe_round(rsi_14, 2),
        "sma_20": safe_round(sma_20, 2),
        "sma_50": safe_round(sma_50, 2),
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


def example_output() -> dict:
    """
    Ejemplo estático de salida para documentación o pruebas rápidas.
    """
    return {
        "momentum_20d": 0.0842,
        "rsi_14": 71.35,
        "sma_20": 210.42,
        "sma_50": 205.87,
        "cruce_medias_alcista": True,
        "cruce_medias_bajista": False,
        "bollinger_mid": 208.11,
        "bollinger_upper": 214.95,
        "bollinger_lower": 201.27,
        "bollinger_score": 0.92,
        "rsi_sobrecompra": True,
        "rsi_sobreventa": False,
        "volatilidad_alta": False,
        "signals": [
            "momentum_alcista",
            "cruce_medias_alcista",
            "rsi_sobrecompra",
            "bollinger_cerca_banda_superior",
        ],
        "comentarios_usuario": [
            "La accion se encuentra en momento alcista.",
            "La media corta se situa por encima de la media larga.",
            "Posible situacion de sobrecompra.",
            "El precio se situa cerca de la banda superior de Bollinger.",
        ],
    }
