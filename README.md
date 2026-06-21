## Demo funcional actual

Este repositorio incluye una demo simplificada en Flask para el trabajo de master.

- Arranque: `python api/app.py`
- Dashboard: `http://localhost:5000/dashboard`
- Dependencias: `pip install -r requirements.txt`
- La carpeta `database/` no se usa en esta demo.
- Las alertas se guardan solo en memoria.

Nota: el contenido historico del README que aparece debajo puede describir una arquitectura mas amplia prevista para fases posteriores. Para probar la demo actual, usa las instrucciones de esta seccion.

# API
desarrollo de una API financiera

# 📊 FundCompare API — Comparador de Fondos de Inversión y ETFs

> **Proyecto Final · Automatización de Procesos Financieros**  
> Universidad Internacional de Valencia (VIU) · Máster en Finanzas · Grupo 3  
> 🗓️ Entrega: 23 de junio de 2026

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-26A5E4?logo=telegram&logoColor=white)](https://core.telegram.org/bots)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/Estado-En%20desarrollo-yellow)]()

---

## 📋 Tabla de Contenidos

1. [Descripción del Proyecto](#-descripción-del-proyecto)
2. [Objetivos](#-objetivos)
3. [Arquitectura](#-arquitectura)
4. [Base de Datos](#-base-de-datos)
5. [Automatización de Procesos](#-automatización-de-procesos)
6. [Endpoints de la API](#-endpoints-de-la-api)
7. [Métricas Implementadas](#-métricas-implementadas)
8. [Alertas por Telegram](#-alertas-por-telegram)
9. [Interfaz de Usuario](#-interfaz-de-usuario)
10. [Tecnologías y Librerías](#-tecnologías-y-librerías)
11. [Estructura del Repositorio](#-estructura-del-repositorio)
12. [Instalación y Uso](#-instalación-y-uso)
13. [Ejemplos de Uso](#-ejemplos-de-uso)
14. [Pruebas](#-pruebas)
15. [Integrantes del Grupo](#-integrantes-del-grupo)

---

## 🎯 Descripción del Proyecto

**FundCompare API** es una API REST desarrollada en Python que automatiza la comparación de fondos de inversión y ETFs mediante métricas financieras cuantitativas, rankings configurables y un sistema de alertas personalizadas vía Telegram.

El sistema opera de forma **completamente autónoma**: descarga datos de mercado varias veces al día desde Yahoo Finance, recalcula métricas en tiempo real y notifica proactivamente a los usuarios suscritos cuando un fondo de su cartera de seguimiento supera o cae por debajo de un umbral definido.

### ¿Qué problema resuelve?

La comparación manual de fondos implica visitar múltiples plataformas, copiar datos y calcular métricas a mano. FundCompare API automatiza este workflow completo:

```
Datos de mercado (yfinance) → Cálculo automático de métricas → Rankings 
        → Detección de cambios → Alerta por Telegram al usuario
```

---

## 🏹 Objetivos

### Objetivo General

Desarrollar un sistema automatizado e integral para la comparación de fondos de inversión y ETFs, que combine una API REST, una base de datos relacional, procesos programados y notificaciones proactivas, aplicando las herramientas del curso de Automatización de Procesos Financieros.

### Objetivos Específicos

- Integrar Yahoo Finance (`yfinance`) para extracción automatizada y periódica de datos de mercado.
- Diseñar y mantener una base de datos SQLite relacional con tres tablas: métricas históricas, usuarios y preferencias de alerta.
- Calcular automáticamente métricas de rentabilidad y riesgo (Sharpe, Sortino, drawdown, volatilidad, beta).
- Programar tareas recurrentes con `APScheduler` para la actualización de datos sin intervención humana.
- Implementar un bot de Telegram que notifique a usuarios suscritos cuando una métrica supera un umbral definido.
- Exponer los resultados mediante una API REST documentada con OpenAPI/Swagger.
- Ofrecer una interfaz web mínima (dashboard HTML) para visualizar comparaciones sin necesidad de cliente técnico.

---

## 🏗️ Arquitectura

```
                    ┌─────────────────────────────────────────────┐
                    │              CLIENTES                        │
                    │   Browser (Dashboard) · curl · Notebook      │
                    └──────────────────┬──────────────────────────┘
                                       │ HTTP REST
                    ┌──────────────────▼──────────────────────────┐
                    │              FASTAPI APP                     │
                    │   /api/v1/fondos  /metricas  /rankings       │
                    │   /usuarios       /alertas   /health         │
                    │   /dashboard  (HTML estático servido)        │
                    └────────┬──────────────────┬─────────────────┘
                             │                  │
           ┌─────────────────▼───┐   ┌──────────▼──────────────────┐
           │    CAPA DE DATOS    │   │      CAPA DE CÁLCULO        │
           │  yfinance (Yahoo)   │   │  pandas / numpy             │
           │  requests           │   │  Sharpe, Sortino, Beta      │
           └─────────────────┬───┘   │  Drawdown, Volatilidad      │
                             │       └──────────┬──────────────────┘
                             │                  │
                    ┌────────▼──────────────────▼─────────────────┐
                    │              BASE DE DATOS (SQLite)          │
                    │   metricas_historico · usuarios · alertas    │
                    └──────────────────┬──────────────────────────┘
                                       │
              ┌────────────────────────┼──────────────────────────┐
              │                        │                          │
   ┌──────────▼───────────┐  ┌─────────▼──────────┐  ┌──────────▼──────────┐
   │     SCHEDULER        │  │    BOT TELEGRAM     │  │    DASHBOARD UI     │
   │  APScheduler         │  │  python-telegram-   │  │  HTML + Chart.js    │
   │  Descarga cada 6h    │  │  bot                │  │  Visualización      │
   │  Recalcula métricas  │  │  Alertas push       │  │  comparativa        │
   └──────────────────────┘  └────────────────────┘  └─────────────────────┘
```

**Flujo completo de una alerta automática:**

1. El scheduler ejecuta la descarga de datos (`yfinance`) cada 6 horas.
2. Se recalculan todas las métricas y se persisten en `metricas_historico`.
3. El motor de alertas compara los nuevos valores con los umbrales en `alertas`.
4. Si algún umbral se supera, el bot de Telegram envía un mensaje al `chat_id` del usuario.

---

## 🗄️ Base de Datos

La base de datos es SQLite, gestionada con SQLAlchemy ORM. Contiene tres tablas principales:

### Diagrama E-R

```
┌────────────────────────┐         ┌────────────────────────┐
│        usuarios        │         │       alertas          │
├────────────────────────┤         ├────────────────────────┤
│ id          INTEGER PK │──┐      │ id          INTEGER PK │
│ telegram_chat_id TEXT  │  └─────▶│ usuario_id  INTEGER FK │
│ nombre      TEXT       │         │ ticker      TEXT       │
│ email       TEXT       │         │ metrica     TEXT       │
│ activo      BOOLEAN    │         │ condicion   TEXT       │
│ fecha_alta  DATETIME   │         │ umbral      REAL       │
└────────────────────────┘         │ activa      BOOLEAN    │
                                   │ ultima_notif DATETIME  │
                                   └────────────────────────┘
                                             ▲
┌────────────────────────┐                  │ (ticker referencia)
│   metricas_historico   │                  │
├────────────────────────┤                  │
│ id           INTEGER PK│                  │
│ ticker       TEXT      │◀─────────────────┘
│ fecha        DATETIME  │
│ precio_cierre REAL     │
│ rent_acum_1y  REAL     │
│ volatilidad   REAL     │
│ sharpe_ratio  REAL     │
│ sortino_ratio REAL     │
│ max_drawdown  REAL     │
│ beta          REAL     │
└────────────────────────┘
```

### Tabla `usuarios`

Almacena el `telegram_chat_id` de cada usuario para poder enviarle notificaciones directas. El registro se realiza mediante el comando `/start` del bot de Telegram, sin necesidad de formularios externos.

### Tabla `alertas` (preferencias)

Cada fila representa una preferencia de alerta de un usuario: qué ticker vigilar, qué métrica monitorizar, la condición (`>` o `<`) y el valor umbral. Ejemplos:

| usuario_id | ticker | metrica | condicion | umbral | descripción |
|------------|--------|---------|-----------|--------|-------------|
| 1 | SPY | sharpe_ratio | < | 1.0 | Alerta si Sharpe cae por debajo de 1.0 |
| 1 | QQQ | max_drawdown | < | -0.15 | Alerta si drawdown supera -15% |
| 2 | VWCE | volatilidad | > | 0.25 | Alerta si volatilidad supera 25% |

### Tabla `metricas_historico`

Cada descarga del scheduler inserta una nueva fila por ticker, construyendo un histórico completo que permite analizar la evolución de las métricas a lo largo del tiempo.

---

## ⚙️ Automatización de Procesos

Este es el núcleo diferencial del proyecto: el sistema funciona de forma autónoma sin intervención manual.

### Scheduler — APScheduler

Se utiliza `APScheduler` integrado en el propio proceso de FastAPI para ejecutar tareas programadas:

```python
# api/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

# Descarga y recalcula métricas cada 6 horas
scheduler.add_job(actualizar_metricas, "interval", hours=6)

# Comprueba alertas 5 minutos después de cada actualización
scheduler.add_job(comprobar_alertas, "interval", hours=6, minutes=5)
```

### Flujo de la tarea `actualizar_metricas`

```
1. Leer tickers únicos de la tabla metricas_historico y alertas
2. Descargar datos históricos (1 año) con yfinance
3. Calcular métricas con pandas/numpy
4. Insertar nueva fila en metricas_historico con timestamp actual
5. Log de éxito/error por ticker
```

### Flujo de la tarea `comprobar_alertas`

```
1. Leer todas las alertas activas de la BD
2. Para cada alerta, obtener el valor más reciente de metricas_historico
3. Evaluar la condición (valor > umbral o valor < umbral)
4. Si se cumple y han pasado >1h desde la última notificación:
   → Enviar mensaje Telegram al usuario
   → Actualizar ultima_notif en la BD
```

### Registro de ejecuciones

Todas las ejecuciones del scheduler quedan registradas en `logs/scheduler.log` con timestamp, tickers procesados y errores, permitiendo auditar el proceso automatizado.

---

## 🔌 Endpoints de la API

La documentación interactiva está disponible en `/docs` (Swagger UI) una vez desplegada la aplicación.

### Fondos y Métricas

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/api/v1/comparar` | Compara fondos por ticker (`?tickers=SPY,QQQ&periodo=1y`) |
| `GET` | `/api/v1/metricas/{ticker}` | Métricas actuales de un fondo |
| `GET` | `/api/v1/metricas/{ticker}/historico` | Evolución histórica de métricas en BD |
| `GET` | `/api/v1/rankings` | Ranking por criterio (`?criterio=sharpe&top=10`) |

### Usuarios y Alertas

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/api/v1/usuarios` | Registrar usuario (chat_id de Telegram + nombre) |
| `GET` | `/api/v1/usuarios/{id}/alertas` | Listar preferencias de alerta de un usuario |
| `POST` | `/api/v1/alertas` | Crear nueva preferencia de alerta |
| `DELETE` | `/api/v1/alertas/{id}` | Eliminar una alerta |
| `PUT` | `/api/v1/alertas/{id}` | Modificar umbral o condición de una alerta |

### Sistema

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/api/v1/scheduler/ejecutar` | Forzar actualización manual de métricas |
| `GET` | `/api/v1/health` | Estado de la API, BD y última ejecución del scheduler |

---

## 📐 Métricas Implementadas

| Métrica | Descripción | Uso en alertas |
|---------|-------------|----------------|
| **Rentabilidad acumulada** | Retorno total en el período | ✅ |
| **Volatilidad anualizada** | Desviación estándar de retornos anualizados | ✅ |
| **Ratio de Sharpe** | Rentabilidad ajustada al riesgo vs. tasa libre de riesgo | ✅ |
| **Ratio de Sortino** | Variante del Sharpe penalizando solo volatilidad bajista | ✅ |
| **Maximum Drawdown** | Pérdida máxima desde un máximo histórico | ✅ |
| **Beta** | Sensibilidad respecto al S&P 500 | ✅ |
| **Correlación** | Correlación entre fondos para análisis de diversificación | — |

## Métricas Técnicas Incorporadas

Además de las métricas financieras tradicionales, la API incorpora un módulo de análisis técnico que amplía las capacidades de evaluación de activos.

### CAGR (Compound Annual Growth Rate)

Permite estimar la rentabilidad anual compuesta obtenida por el activo durante el periodo analizado.

### Momentum (20 sesiones)

Calcula la variación porcentual del precio durante las últimas 20 sesiones bursátiles.

Interpretación:

* Momentum positivo → Impulso alcista.
* Momentum negativo → Impulso bajista.

### RSI (Relative Strength Index)

Calculado sobre una ventana de 14 sesiones utilizando el método de Wilder.

Interpretación:

* RSI > 70 → Posible sobrecompra.
* RSI < 30 → Posible sobreventa.

### Medias Móviles

Se calculan:

* SMA20 (Media móvil simple de 20 sesiones).
* SMA50 (Media móvil simple de 50 sesiones).

Adicionalmente se calcula la distancia porcentual respecto a la SMA50:

Distancia SMA50 = (Precio Actual / SMA50) - 1

### Bandas de Bollinger

Las Bandas de Bollinger se calculan utilizando los precios de cierre ajustados del activo.

Se emplea:

* SMA20.
* Desviación estándar de 20 sesiones.
* Dos desviaciones estándar.

Banda Superior = SMA20 + (2 × Desviación Estándar)

Banda Inferior = SMA20 - (2 × Desviación Estándar)

La API devuelve:

* Bollinger Upper.
* Bollinger Mid.
* Bollinger Lower.

### Bollinger Score

Se incorpora un indicador adicional denominado Bollinger Score, que mide la posición relativa del precio dentro del canal de Bollinger.

Bollinger Score =
(Precio Actual - Banda Inferior)
/
(Banda Superior - Banda Inferior)

Interpretación:

* 0 → Precio situado en la banda inferior.
* 0.5 → Centro del canal.
* 1 → Precio situado en la banda superior.

### Métricas de Volumen

Se calculan:

* Volumen actual.
* Volumen medio de 20 sesiones.
* Indicador de volumen superior a la media.

### Señales Técnicas Generadas

La API genera automáticamente señales interpretativas:

* Cruce alcista de medias.
* Cruce bajista de medias.
* RSI en sobrecompra.
* RSI en sobreventa.
* Momentum alcista.
* Momentum bajista.
* Volatilidad elevada.
* Rentabilidad negativa.

Estas señales se devuelven junto con comentarios interpretativos para facilitar la toma de decisiones por parte del usuario.

---

## 🤖 Alertas por Telegram

El bot de Telegram es el canal de notificación proactiva del sistema. Los usuarios interactúan con él para registrarse sin necesidad de ninguna interfaz adicional.

### Registro de usuario

```
Usuario → /start
Bot     → "¡Bienvenido a FundCompare! Tu ID de Telegram es 123456789. 
           Ya estás registrado para recibir alertas. 
           Usa /ayuda para ver los comandos disponibles."
```

El bot extrae automáticamente el `chat_id` de Telegram y lo registra en la tabla `usuarios`.

### Comandos del bot

| Comando | Descripción |
|---------|-------------|
| `/start` | Registro automático del usuario |
| `/alertas` | Listar las alertas activas del usuario |
| `/ayuda` | Mostrar comandos disponibles |

### Ejemplo de notificación automática

```
🚨 ALERTA FUNDCOMPARE

📉 SPY — Ratio de Sharpe
El Sharpe Ratio ha caído por debajo de tu umbral.

Valor actual:   0.87
Tu umbral:    < 1.00
Última actualización: 23/06/2026 14:00

🔗 Ver comparativa completa: http://localhost:8000/dashboard
```

---

## 🖥️ Interfaz de Usuario

Para hacer el proyecto accesible a usuarios no técnicos, la API sirve también un **dashboard web mínimo** en `/dashboard`.

### Características del Dashboard

- **Buscador de tickers:** campo de texto para introducir los tickers a comparar.
- **Tabla comparativa:** métricas de cada fondo en formato tabla, con colores semáforo (verde/rojo) según el valor.
- **Gráfico de rentabilidad:** evolución del precio normalizado con Chart.js.
- **Sin dependencias externas:** HTML + CSS + JavaScript vanilla servido directamente por FastAPI vía `StaticFiles`.

### Capturas de pantalla

> *(Se añadirán durante el desarrollo en la carpeta `docs/screenshots/`)*

---

## 🛠️ Tecnologías y Librerías

### Core API

| Librería | Versión | Uso |
|----------|---------|-----|
| `fastapi` | 0.111+ | Framework REST |
| `uvicorn` | 0.29+ | Servidor ASGI |
| `pydantic` | 2.x | Validación de esquemas |

### Datos Financieros

| Librería | Versión | Uso |
|----------|---------|-----|
| `yfinance` | 0.2+ | Descarga de precios históricos |
| `pandas` | 2.x | Cálculo de métricas sobre series temporales |
| `numpy` | 1.26+ | Operaciones numéricas |

### Base de Datos

| Librería | Versión | Uso |
|----------|---------|-----|
| `sqlalchemy` | 2.x | ORM y gestión de SQLite |

### Automatización y Alertas

| Librería | Versión | Uso |
|----------|---------|-----|
| `apscheduler` | 3.x | Scheduler de tareas periódicas |
| `python-telegram-bot` | 20.x | Bot de Telegram y envío de alertas |

### Utilidades

| Librería | Versión | Uso |
|----------|---------|-----|
| `python-dotenv` | 1.x | Variables de entorno y API keys |
| `pytest` | 7.x | Testing automatizado |

---

## 📁 Estructura del Repositorio

```
API/
├── api/                            # Código fuente de la API
│   ├── main.py                     # Punto de entrada FastAPI + scheduler
│   ├── routers/                    # Rutas agrupadas por dominio
│   │   ├── fondos.py               # /comparar, /metricas, /rankings
│   │   ├── usuarios.py             # /usuarios
│   │   └── alertas.py              # /alertas
│   ├── services/                   # Lógica de negocio
│   │   ├── data_fetcher.py         # Descarga datos con yfinance
│   │   ├── metrics.py              # Cálculo de métricas financieras
│   │   ├── ranking.py              # Generación de rankings
│   │   └── alert_engine.py         # Motor de comprobación de alertas
│   ├── models/                     # Modelos de datos
│   │   ├── schemas.py              # Esquemas Pydantic (request/response)
│   │   └── database.py             # Modelos SQLAlchemy + engine SQLite
│   ├── scheduler.py                # Configuración APScheduler
│   ├── telegram_bot.py             # Bot de Telegram (handlers + envío)
│   └── utils/
│       └── config.py               # Variables de entorno
│
├── dashboard/                      # Interfaz web
│   ├── index.html                  # Dashboard principal
│   ├── style.css                   # Estilos
│   └── app.js                      # Lógica JS (fetch a la API + Chart.js)
│
├── database/                       # Base de datos SQLite
│   └── fondos.db                   # Generada automáticamente al iniciar
│
├── logs/                           # Logs del scheduler
│   └── scheduler.log
│
├── scripts/                        # Scripts auxiliares
│   ├── init_db.py                  # Crea tablas e inserta tickers de ejemplo
│   └── test_telegram.py            # Prueba el envío de un mensaje Telegram
│
├── docs/                           # Documentación técnica
│   ├── arquitectura.md
│   ├── metricas.md
│   └── screenshots/
│
├── Html_profesor_files/            # Material del profesor
├── Html_profesor.html
├── tutorial-api-completo.ipynb
│
├── .env.example                    # Plantilla de variables de entorno
├── .gitignore
├── Instrucciones.md
├── requirements.txt
└── README.md
```

---

## 🚀 Instalación y Uso

### Requisitos previos

- Python 3.10 o superior
- Un bot de Telegram creado con [@BotFather](https://t.me/botfather) (obtener el token)

### 1. Clonar el repositorio

```bash
git clone https://github.com/APF-Grupo3/API.git
cd API
```

### 2. Entorno virtual e instalación de dependencias

```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
cp .env.example .env
```

Editar `.env`:

```env
# Token del bot de Telegram (obtenido de @BotFather)
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Base de datos
DATABASE_URL=sqlite:///./database/fondos.db

# Tasa libre de riesgo para Sharpe (anualizada, ej: Euribor 12m)
RISK_FREE_RATE=0.038

# Frecuencia de actualización en horas (por defecto 6)
SCHEDULER_INTERVAL_HOURS=6
```

### 4. Inicializar la base de datos

```bash
python scripts/init_db.py
```

Este script crea las tres tablas y carga una lista inicial de tickers (SPY, QQQ, VTI, VWCE, IWM).

### 5. Iniciar la API

```bash
cd api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Al arrancar, el scheduler queda activo y el bot de Telegram empieza a escuchar.

| Recurso | URL |
|---------|-----|
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Dashboard | http://localhost:8000/dashboard |
| Health check | http://localhost:8000/api/v1/health |

---

## 💡 Ejemplos de Uso

### Comparar ETFs y obtener ranking

```bash
curl "http://localhost:8000/api/v1/comparar?tickers=SPY,QQQ,IWM&periodo=1y"
```

```json
{
  "fecha_consulta": "2026-06-23T14:00:00",
  "periodo": "1y",
  "fondos": [
    {
      "ticker": "SPY",
      "nombre": "SPDR S&P 500 ETF Trust",
      "metricas": {
        "rentabilidad_acumulada": 0.187,
        "volatilidad_anual": 0.142,
        "sharpe_ratio": 1.32,
        "sortino_ratio": 1.89,
        "max_drawdown": -0.084,
        "beta": 1.00
      }
    }
  ],
  "ranking_sharpe": ["SPY", "IWM", "QQQ"]
}
```

### Registrar una alerta

```bash
curl -X POST "http://localhost:8000/api/v1/alertas" \
  -H "Content-Type: application/json" \
  -d '{
    "usuario_id": 1,
    "ticker": "SPY",
    "metrica": "sharpe_ratio",
    "condicion": "<",
    "umbral": 1.0
  }'
```

### Forzar actualización manual de métricas

```bash
curl -X POST "http://localhost:8000/api/v1/scheduler/ejecutar"
```

### Desde Python (notebook)

```python
import requests

# Comparar fondos
r = requests.get(
    "http://localhost:8000/api/v1/comparar",
    params={"tickers": "SPY,QQQ,VWCE", "periodo": "2y"}
)
df = pd.DataFrame([f["metricas"] for f in r.json()["fondos"]],
                  index=[f["ticker"] for f in r.json()["fondos"]])
df.sort_values("sharpe_ratio", ascending=False)
```

---

## 🧪 Pruebas

```bash
pytest -v
```

| Módulo de test | Qué se valida |
|----------------|---------------|
| `test_metricas.py` | Cálculo correcto de Sharpe, Sortino, drawdown y volatilidad sobre datos sintéticos |
| `test_endpoints.py` | Códigos de respuesta y estructura JSON de todos los endpoints |
| `test_alert_engine.py` | Detección correcta de umbrales superados y no superados |
| `test_scheduler.py` | Ejecución de la tarea de actualización e inserción en BD |

---

## 👥 Integrantes del Grupo

| Nombre | GitHub | Contribución Principal |
|--------|--------|----------------------|
| _[Nombre 1]_ | [@usuario1](https://github.com/) | API REST, endpoints, arquitectura |
| _[Nombre 2]_ | [@usuario2](https://github.com/) | Módulo de métricas financieras |
| _[Nombre 3]_ | [@usuario3](https://github.com/) | Base de datos, scheduler, automatización |
| _[Nombre 4]_ | [@usuario4](https://github.com/) | Bot Telegram, dashboard UI |

---

## 📚 Referencias

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [yfinance — Yahoo Finance Market Data](https://pypi.org/project/yfinance/)
- [APScheduler Documentation](https://apscheduler.readthedocs.io/)
- [python-telegram-bot Documentation](https://python-telegram-bot.org/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [Automatización de Procesos Financieros — VIU (Material del curso)](https://jomucon21muri.github.io/Automatizacion_PF/)

---

<div align="center">

**Grupo 3 · Automatización de Procesos Financieros · VIU 2026**

</div>
