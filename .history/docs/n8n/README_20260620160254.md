# FundCompare — Integración n8n + Telegram

## Índice
1. [Arquitectura](#arquitectura)
2. [Crear el bot de Telegram](#1-crear-el-bot-de-telegram)
3. [Obtener el chat ID](#2-obtener-el-chat-id)
4. [Variables de entorno en Flask](#3-variables-de-entorno-en-flask)
5. [Instalar y arrancar n8n](#4-instalar-y-arrancar-n8n)
6. [Configurar credencial Telegram en n8n](#5-configurar-credencial-telegram-en-n8n)
7. [Importar los workflows](#6-importar-los-workflows)
8. [Descripción de cada workflow](#7-descripcion-de-cada-workflow)
9. [Nuevos endpoints del backend](#8-nuevos-endpoints-del-backend)
10. [Flujo del botón Telegram en el dashboard](#9-flujo-del-boton-telegram-en-el-dashboard)
11. [Verificación rápida](#10-verificacion-rapida)

---

## Arquitectura

```
Dashboard (browser)
    │
    │  POST /api/v1/telegram/enviar-resumen  (botón)
    ▼
Flask API (api/app.py)
    │  urllib → Telegram Bot API
    ▼
Telegram Bot → Chat del grupo / canal

────────────────────────────────────────────
n8n (scheduler / webhook)
    │
    │  GET /api/v1/comparar
    │  POST /api/v1/telegram/verificar-alertas
    ▼
Flask API
    │
    ▼ (datos JSON)
n8n Code node (formatea mensaje)
    │
    ▼
n8n Telegram node → Chat del grupo / canal
```

**Regla clave:** el backend calcula y provee datos; n8n orquesta y programa; Telegram recibe el resultado.

---

## 1. Crear el bot de Telegram

1. Abre Telegram y busca **@BotFather**.
2. Escribe `/newbot`.
3. Asigna un nombre y un username (acaba en `bot`).
4. BotFather te devuelve el **token** con formato `123456789:ABCDEFabcdef...` — guárdalo.

---

## 2. Obtener el chat ID

El bot necesita saber a qué chat enviar los mensajes.

**Opción A — chat personal:**
1. Manda un mensaje cualquiera a tu bot.
2. Visita: `https://api.telegram.org/bot<TOKEN>/getUpdates`
3. En el JSON busca `"chat":{"id": XXXXXXX}` — ese número es tu `TELEGRAM_CHAT_ID`.

**Opción B — grupo:**
1. Añade el bot al grupo.
2. Manda un mensaje en el grupo.
3. Visita la URL de `getUpdates` — el `id` del chat de grupo es negativo (ej. `-1001234567890`).

---

## 3. Variables de entorno en Flask

Crea un archivo `.env` en la raíz del proyecto (ya existe `.env.example` como plantilla):

```env
TELEGRAM_BOT_TOKEN=123456789:ABCDEFabcdef...
TELEGRAM_CHAT_ID=123456789
```

> **Nunca subas `.env` al repositorio.** Está añadido en `.gitignore`.

Para cargar las variables al arrancar Flask en PowerShell:

```powershell
# opción A — cargar manualmente antes de arrancar
$env:TELEGRAM_BOT_TOKEN = "TU_TOKEN"
$env:TELEGRAM_CHAT_ID   = "TU_CHAT_ID"
python api/app.py

# opción B — instalar python-dotenv y añadir load_dotenv() en app.py
pip install python-dotenv
```

Verifica que Flask detecta las credenciales:

```
GET http://localhost:5000/api/v1/telegram/estado
```

Respuesta esperada cuando está bien configurado:
```json
{ "configurado": true, "token_presente": true, "chat_id_presente": true, "mensaje": "Telegram listo para envios" }
```

---

## 4. Instalar y arrancar n8n

### Opción recomendada — npx (sin instalación global)

```powershell
npx n8n
```

n8n arranca en `http://localhost:5678`.

### Opción alternativa — Docker

```powershell
docker run -it --rm -p 5678:5678 n8nio/n8n
```

### Variable n8n para el chat ID

En n8n, ve a **Settings → Variables** y crea:

| Name | Value |
|------|-------|
| `FUNDCOMPARE_CHAT_ID` | tu chat ID de Telegram |

Los workflows usan `$vars.FUNDCOMPARE_CHAT_ID` para no hardcodear el ID.

---

## 5. Configurar credencial Telegram en n8n

1. En n8n, ve a **Credentials → New**.
2. Busca **Telegram**.
3. Rellena el campo **Access Token** con el token de tu bot.
4. Guarda con el nombre `FundCompare Bot`.
5. Apunta el **ID** que n8n asigna a la credencial (lo necesitarás al importar los workflows).

---

## 6. Importar los workflows

Los tres archivos JSON están en `docs/n8n/`:

| Archivo | Propósito |
|---------|-----------|
| `workflow_resumen_diario.json` | Resumen automático a las 9h L-V |
| `workflow_verificacion_alertas.json` | Comprueba alertas cada hora en días laborables |
| `workflow_webhook_comparacion.json` | Webhook para comparación bajo demanda |

### Pasos para importar

1. En n8n, ve a **Workflows → Import from File**.
2. Selecciona el JSON correspondiente.
3. En el nodo **Enviar por Telegram** / **Notificar por Telegram**:
   - Haz clic en el campo **Credential**.
   - Selecciona la credencial `FundCompare Bot` que creaste.
4. En los nodos **HTTP Request**, comprueba que la URL base es correcta:
   - Desarrollo local: `http://localhost:5000`
   - Producción: reemplaza con la URL real del servidor.
5. Activa el workflow con el interruptor superior derecho.

---

## 7. Descripción de cada workflow

### `workflow_resumen_diario.json`

```
Schedule (9h L-V)
  → GET /api/v1/comparar?tickers=SPY,QQQ,IWM&periodo=1mo
  → Code: formatea fondos + rankings en Markdown
  → Telegram: envía resumen al chat
```

Puedes cambiar los tickers y el periodo directamente en el nodo **Obtener comparacion**.

---

### `workflow_verificacion_alertas.json`

```
Schedule (cada hora L-V)
  → POST /api/v1/telegram/verificar-alertas  { "enviar_notificaciones": false }
  → IF alertas_disparadas > 0
      → Code: formatea lista de alertas activadas
      → Telegram: notifica al chat
```

El endpoint devuelve qué alertas se dispararon sin enviar nada por sí mismo (n8n controla el envío).  
Si prefieres que Flask envíe directamente, cambia el body a `{ "enviar_notificaciones": true }` y elimina el nodo Telegram de n8n.

---

### `workflow_webhook_comparacion.json`

```
Webhook POST /webhook/fundcompare/comparar
  → GET /api/v1/comparar?tickers=...&periodo=...
  → Code: formatea el resultado
  → Telegram: envía el resumen
  → Respond to Webhook: devuelve { status, fondos_comparados }
```

Llámalo así desde cualquier sistema externo:

```bash
curl -X POST http://localhost:5678/webhook/fundcompare/comparar \
  -H "Content-Type: application/json" \
  -d '{"tickers": "AAPL,MSFT,GOOGL", "periodo": "3mo"}'
```

---

## 8. Nuevos endpoints del backend

Los siguientes endpoints se han añadido a `api/app.py` para esta integración:

### `GET /api/v1/telegram/estado`

Comprueba si las variables `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID` están configuradas.

```json
{
  "configurado": true,
  "token_presente": true,
  "chat_id_presente": true,
  "mensaje": "Telegram listo para envios"
}
```

### `POST /api/v1/telegram/enviar-resumen` *(actualizado)*

Ahora envía un mensaje real de Telegram. Acepta body JSON:

```json
{ "tickers": "SPY,QQQ,IWM", "periodo": "1mo" }
```

Respuestas posibles:
- `200` `status: "sent"` — mensaje enviado correctamente
- `503` `status: "not_configured"` — faltan credenciales
- `502` `status: "error"` — error de la API de Telegram

### `POST /api/v1/telegram/verificar-alertas`

Evalúa todas las alertas en memoria contra métricas en tiempo real.

Body JSON:
```json
{ "enviar_notificaciones": false }
```

Respuesta:
```json
{
  "total_alertas": 3,
  "alertas_disparadas": 1,
  "detalle": [
    {
      "alerta": { "id": 1, "ticker": "SPY", "metrica": "sharpe_ratio", "condicion": "<", "umbral": 0.5 },
      "valor_actual": 0.312,
      "disparada": true
    }
  ],
  "notificaciones_enviadas": false
}
```

---

## 9. Flujo del botón Telegram en el dashboard

El botón `Enviar resumen por Telegram` del header ahora:

1. Lee los tickers y periodo del formulario activo.
2. Envía `POST /api/v1/telegram/enviar-resumen` con `{ tickers, periodo }`.
3. Flask calcula las métricas, construye el mensaje Markdown y lo envía al bot.
4. El dashboard muestra el mensaje de respuesta en la barra de feedback.

> Los IDs del DOM (`telegramButton`, `tickersInput`, `periodInput`) y todos los contratos JSON permanecen **inalterados** respecto a la rama `jesus/frontend-dashboard`.

---

## 10. Verificación rápida

```powershell
# 1. Configurar credenciales (PowerShell)
$env:TELEGRAM_BOT_TOKEN = "TU_TOKEN"
$env:TELEGRAM_CHAT_ID   = "TU_CHAT_ID"

# 2. Arrancar Flask
python api/app.py

# 3. Verificar estado
Invoke-RestMethod http://localhost:5000/api/v1/telegram/estado

# 4. Enviar resumen de prueba
Invoke-RestMethod -Method POST `
  -Uri http://localhost:5000/api/v1/telegram/enviar-resumen `
  -ContentType "application/json" `
  -Body '{"tickers":"SPY,QQQ","periodo":"1mo"}'

# 5. Verificar alertas (sin enviar)
Invoke-RestMethod -Method POST `
  -Uri http://localhost:5000/api/v1/telegram/verificar-alertas `
  -ContentType "application/json" `
  -Body '{"enviar_notificaciones":false}'
```

Si ves `"status": "sent"` en el paso 4, la integración funciona correctamente.
