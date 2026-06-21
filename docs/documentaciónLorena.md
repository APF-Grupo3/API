# Documentación de modificaciones — Lorena

Registro de todos los cambios realizados en el proyecto FundCompare durante la sesión de desarrollo.

---

## 1. Telegram por usuario (backend)

### 1.1 Modelo de datos (`api/models.py`)

Se añadieron campos de Telegram al modelo `Cliente`:

| Campo               | Tipo          | Descripción                                    |
|---------------------|---------------|------------------------------------------------|
| `telegram_chat_id`  | String(50)    | ID del chat de Telegram del usuario (unique)   |
| `telegram_linked_at`| DateTime      | Fecha/hora en que se vinculó Telegram          |
| `telegram_tickers`  | String(500)   | ETFs a los que el usuario quiere suscribirse   |

Se creó el modelo `TelegramToken` para la vinculación segura:

| Campo        | Tipo       | Descripción                                          |
|--------------|------------|------------------------------------------------------|
| `id`         | Integer PK | Identificador                                        |
| `cliente_id` | Integer FK | Referencia al cliente que solicita la vinculación     |
| `token`      | String(64) | Token hex de 32 bytes, único                         |
| `created_at` | DateTime   | Momento de creación                                   |
| `expires_at` | DateTime   | Momento de expiración (15 minutos tras la creación)   |

Constante: `TOKEN_EXPIRY_MINUTES = 15`

El método `to_dict()` del `Cliente` ahora incluye `telegram_vinculado` (booleano derivado de `telegram_chat_id is not None`) y `telegram_tickers`.

### 1.2 Endpoints de Telegram (`api/app.py`)

Se añadieron 8 endpoints bajo `/api/v1/telegram/`:

| Método | Ruta                                | Descripción                                                                 |
|--------|-------------------------------------|-----------------------------------------------------------------------------|
| GET    | `/telegram/estado`                  | Devuelve si el bot está configurado y operativo                             |
| POST   | `/telegram/generar-enlace`          | Genera un token de vinculación y devuelve el deep link `t.me/Bot?start=TOKEN` |
| POST   | `/telegram/vincular`                | Recibe `{token, chat_id}` desde n8n, asocia el chat_id al cliente           |
| POST   | `/telegram/desvincular`             | Elimina el chat_id de Telegram de un cliente                                |
| POST   | `/telegram/configurar-tickers`      | Actualiza los ETFs a los que el usuario quiere suscribirse                  |
| GET    | `/telegram/usuarios-suscritos`      | Lista todos los clientes con Telegram vinculado y tickers configurados       |
| POST   | `/telegram/enviar-resumen`          | Envía un resumen personalizado de los tickers al usuario por Telegram        |
| POST   | `/telegram/verificar-alertas`       | Comprueba alertas activas y notifica por Telegram si se cumplen             |

Función helper modificada: `send_telegram_message(text, chat_id=None)` — acepta un `chat_id` opcional; si no se pasa, usa el global de `.env`.

Función nueva: `_get_bot_username(token)` — llama a la API `getMe` de Telegram para obtener el username del bot (necesario para construir el deep link).

### 1.3 Autenticación (`api/auth.py`)

Endpoints existentes que se utilizan en el flujo:

| Método | Ruta                | Descripción                                       |
|--------|---------------------|----------------------------------------------------|
| POST   | `/api/v1/registro`  | Crea un cliente con hash de contraseña (Werkzeug)  |
| POST   | `/api/v1/login`     | Verifica credenciales y crea sesión Flask           |
| POST   | `/api/v1/logout`    | Cierra la sesión del usuario                        |
| GET    | `/api/v1/sesion`    | Devuelve los datos del usuario logueado (si existe) |

### 1.4 Configuración (`api/configuracion.py`)

Se añadió `SQLALCHEMY_TRACK_MODIFICATIONS = False` para suprimir warnings de Flask-SQLAlchemy.

### 1.5 Dependencias (`requirements.txt`)

```
Flask>=3.0.0
flask-cors>=4.0.0
Flask-SQLAlchemy>=3.1.0
Werkzeug>=3.0.0
python-dotenv>=1.0.0
yfinance>=0.2.40,<1.0.0
pandas>=2.0.0
numpy>=1.26.0
```

---

## 2. Workflows de n8n

### 2.1 Vinculación Telegram (`integraciones/n8n/workflow_vinculacion_telegram.json`)

Flujo:
1. **Telegram Trigger** — escucha mensajes entrantes del bot
2. **IF /start** — filtra solo los mensajes que comienzan con `/start`
3. **Code** — extrae el token y el chat_id del mensaje
4. **HTTP POST** — llama a `http://host.docker.internal:5000/api/v1/telegram/vincular` con `{token, chat_id}`
5. **IF 200** — si la respuesta es exitosa, Flask envía el mensaje de bienvenida directamente
6. **Error** — si falla, notifica al usuario por Telegram

### 2.2 Resumen diario por usuario (`integraciones/n8n/workflow_resumen_diario_por_usuario.json`)

Flujo:
1. **Schedule Trigger** — se ejecuta a las 9:00 L-V
2. **GET /usuarios-suscritos** — obtiene la lista de usuarios con Telegram vinculado
3. **Code** — separa cada usuario en un item individual
4. **GET /comparar** — consulta los tickers personalizados de cada usuario
5. **Code** — formatea el resumen personalizado
6. **Telegram** — envía el mensaje al chat_id del usuario

---

## 3. Infraestructura

### 3.1 n8n (Docker)

```bash
docker run -it -p 5678:5678 \
  -e WEBHOOK_URL=https://puzzling-series-theater.ngrok-free.dev \
  -v n8n_data:/home/node/.n8n \
  n8nio/n8n
```

- Puerto: 5678
- `WEBHOOK_URL` necesario para que n8n acepte webhooks por HTTPS

### 3.2 ngrok (túnel para n8n / Telegram)

```bash
ngrok http --url=puzzling-series-theater.ngrok-free.dev 5678
```

- Dominio estático: `puzzling-series-theater.ngrok-free.dev`
- Redirige tráfico HTTPS al puerto 5678 (n8n)
- Necesario para que Telegram envíe los updates del bot a n8n

### 3.3 Flask (servidor local)

```bash
python api/app.py
```

- Puerto: 5000
- Escucha en `0.0.0.0` (accesible desde la red local)
- Acceso local: `http://localhost:5000/dashboard/`
- Acceso desde otro PC en misma red: `http://TU_IP_LOCAL:5000/dashboard/`

### 3.4 Exponer Flask a compañeros (localhost.run)

Si los compañeros NO están en la misma red WiFi, se usa un túnel SSH gratuito:

```bash
ssh -R 80:127.0.0.1:5000 nokey@localhost.run
```

- Genera una URL pública temporal (tipo `https://xxxx.lhr.life`)
- Redirige todo el tráfico a tu Flask local (puerto 5000)
- Se accede a `https://xxxx.lhr.life/dashboard/auth`

### 3.5 Resumen de comandos para lanzar todo

| Paso | Terminal | Comando | Qué hace |
|------|----------|---------|----------|
| 1 | docker | `docker run -it -p 5678:5678 -e WEBHOOK_URL=https://puzzling-series-theater.ngrok-free.dev -v n8n_data:/home/node/.n8n n8nio/n8n` | Lanza n8n |
| 2 | ngrok | `ngrok http --url=puzzling-series-theater.ngrok-free.dev 5678` | Expone n8n a internet (Telegram) |
| 3 | flask | `python api/app.py` | Lanza la API + dashboard |
| 4 | ssh (opcional) | `ssh -R 80:127.0.0.1:5000 nokey@localhost.run` | Expone Flask a compañeros remotos |

### 3.6 Bot de Telegram

- Token: configurado en `.env` como `TELEGRAM_BOT_TOKEN`
- Flujo deep link: `t.me/{bot_username}?start={token_64_hex}`

---

## 4. Dashboard (frontend)

### 4.1 Gestión de sesión

**`dashboard/auth.js`** — Tras un login exitoso, guarda `datos.cliente` en `sessionStorage`:
```js
sessionStorage.setItem("cliente", JSON.stringify(datos.cliente));
```

**`dashboard/app.js`** — Al cargar el dashboard:
- Lee la sesión de `sessionStorage`
- Si no hay sesión, redirige a `/dashboard/auth`
- Funciones: `getSession()`, `saveSession(cliente)`, `clearSession()`

### 4.2 Icono de perfil de usuario (`dashboard/index.html` + `style.css` + `app.js`)

Se añadió en la zona hero un **botón circular con icono de persona** (`#userProfileButton`).

Al hacer click se despliega un panel (`#userProfilePanel`) con:
- **Nombre** completo del usuario
- **Email**
- **País**
- **Teléfono**
- **Estado de Telegram** (Vinculado ✓ / No vinculado)
- Botón **"Cerrar sesión"** → llama a `POST /api/v1/logout`, limpia `sessionStorage` y redirige a `/dashboard/auth`

El panel se cierra al hacer click fuera de él.

### 4.3 Botones condicionales de Telegram

Se reemplazó el botón único de Telegram por **dos botones condicionales**:

| Botón                        | Cuándo se muestra          | Qué hace                                                                 |
|------------------------------|----------------------------|--------------------------------------------------------------------------|
| **Vincular Telegram** (verde) | `telegram_vinculado: false` | Llama a `POST /telegram/generar-enlace`, muestra modal con el deep link |
| **Enviar resumen** (azul)     | `telegram_vinculado: true`  | Envía resumen de los tickers actuales por Telegram al usuario           |

### 4.4 Modal de vinculación

Cuando el usuario pulsa "Vincular Telegram":
1. Se genera el enlace via API
2. Se muestra un **modal centrado** con:
   - Enlace para abrir en Telegram (abre nueva pestaña)
   - Hora de expiración del token
   - Botón "Cerrar"
3. Al cerrar el modal, se consulta `GET /api/v1/sesion` para refrescar el estado del usuario y actualizar los botones automáticamente

### 4.5 Estilos nuevos (`dashboard/style.css`)

Clases CSS añadidas:

| Clase                      | Descripción                                      |
|----------------------------|--------------------------------------------------|
| `.hero-actions`            | Contenedor flex para los botones del hero         |
| `.telegram-link`           | Estilo verde para el botón de vincular            |
| `.user-profile-wrapper`    | Contenedor relativo para el dropdown del perfil   |
| `.user-profile-button`     | Botón circular 44×44px con borde sutil            |
| `.user-profile-panel`      | Panel desplegable con datos del usuario           |
| `.profile-field`           | Fila etiqueta-valor dentro del panel              |
| `.logout-button`           | Botón rojo para cerrar sesión                     |
| `.telegram-modal-overlay`  | Overlay oscuro con blur para el modal             |
| `.telegram-modal`          | Caja centrada del modal de vinculación            |
| `.modal-close`             | Botón transparente para cerrar el modal           |
| `.modal-timer`             | Texto pequeño con la hora de expiración           |

---

## 5. Archivos modificados (resumen)

| Archivo                  | Tipo de cambio                                                          |
|--------------------------|-------------------------------------------------------------------------|
| `api/models.py`          | Campos Telegram + TelegramToken + etfs_favoritos + modelo Alerta        |
| `api/app.py`             | 8 endpoints Telegram + catálogo ETFs + favoritos + alertas en BD        |
| `api/auth.py`            | Sin cambios funcionales (ya tenía login/registro/sesión/logout)          |
| `api/configuracion.py`   | `SQLALCHEMY_TRACK_MODIFICATIONS = False`                                |
| `requirements.txt`       | Dependencias actualizadas                                               |
| `dashboard/index.html`   | Hero con perfil, botones Telegram, modal, selector ETFs, alertas        |
| `dashboard/style.css`    | Estilos perfil, modal, selector multi-selección, dropdown, tags         |
| `dashboard/app.js`       | Sesión, perfil, Telegram, selector ETFs, favoritos, alertas con sesión  |
| `dashboard/auth.js`      | Guarda cliente en sessionStorage tras login                             |
| `integraciones/n8n/*.json`| Workflows de vinculación y resumen diario                               |

---

## 6. Base de datos

- SQLite: `instance/app.db`
- Tablas: `clientes`, `telegram_tokens`, `alertas`
- Usuario registrado: `lorenamartinezperea84@gmail.com` (ID 1)
- Las tablas se crean automáticamente al arrancar Flask (`db.create_all()`)

---

## 7. Estado de Telegram validado contra la BD (no solo sesión)

### Problema detectado

El estado `telegram_vinculado` se leía únicamente de `sessionStorage`, lo que significaba que si el usuario vinculaba o desvinculaba Telegram desde otro dispositivo (o si un administrador modificaba la BD), el dashboard no reflejaba el estado real.

### Solución implementada (`dashboard/app.js`)

Se separó la lógica en dos funciones:

| Función          | Tipo  | Responsabilidad                                                                   |
|------------------|-------|-----------------------------------------------------------------------------------|
| `renderProfile()`| async | Consulta `GET /api/v1/sesion` (que lee de la BD) y actualiza `sessionStorage`     |
| `applyProfile()` | sync  | Aplica la lógica visual: muestra exclusivamente un botón u otro según el estado    |

**Flujo al cargar el dashboard:**
1. `renderProfile()` llama a `GET /api/v1/sesion`
2. El endpoint lee `telegram_chat_id` del modelo `Cliente` en la BD
3. Devuelve `telegram_vinculado: true/false` (derivado de `telegram_chat_id is not None`)
4. Se actualiza `sessionStorage` con los datos frescos
5. `applyProfile()` muestra el botón correcto

**Comportamiento de los botones:**
- Ambos botones arrancan con `hidden` en el HTML → no se muestra ninguno hasta confirmar el estado real
- Si `telegram_vinculado === true` → solo se muestra **"Enviar resumen por Telegram"**
- Si `telegram_vinculado === false` → solo se muestra **"Vincular Telegram"**

**Casos especiales:**
- Si la sesión del servidor ha caducado → redirige automáticamente a `/dashboard/auth`
- Si la red falla → usa datos locales de `sessionStorage` como fallback
- Al cerrar el modal de vinculación → `refreshClienteData()` vuelve a consultar la BD y actualiza los botones

---

## 8. ETFs favoritos (guardados en base de datos)

### 8.1 Modelo (`api/models.py`)

Se añadió el campo `etfs_favoritos` (String 2000) al modelo `Cliente`. Almacena los tickers separados por comas. El método `to_dict()` lo devuelve como lista Python.

### 8.2 Catálogo de ETFs (`api/app.py`)

Se creó un catálogo estático con ~250 activos en 12 categorías:

| Categoría                  | Ejemplos                        |
|----------------------------|---------------------------------|
| Acciones populares US      | AAPL, TSLA, GOOGL, AMZN, MSFT  |
| Acciones populares Europa  | SAN, BBVA, TEF, SAP, ASML      |
| ETFs renta variable        | SPY, QQQ, VTI, IWM             |
| ETFs renta fija            | BND, TLT, AGG                  |
| ETFs sectoriales           | XLF, XLE, XLK                  |
| ...y más                   |                                 |

### 8.3 Endpoints

| Método | Ruta                      | Descripción                                              |
|--------|---------------------------|----------------------------------------------------------|
| GET    | `/etfs/catalogo?q=&limit=` | Búsqueda del catálogo con filtro por texto (máx 500)     |
| GET    | `/cliente/etfs-favoritos`  | Devuelve los favoritos del usuario logueado               |
| POST   | `/cliente/etfs-favoritos`  | Guarda la lista de favoritos (máximo 50)                  |

### 8.4 Selector multi-selección en el dashboard

Se implementó un **dropdown con buscador** para seleccionar activos:

- **Campo de búsqueda** que filtra el catálogo en tiempo real
- **Dropdown con categorías** que muestra ticker + nombre + ✓ si está seleccionado
- **Tags** debajo del buscador con cada activo seleccionado (click en × para eliminar)
- **Badge contador** cuando hay más de 3 activos seleccionados
- Botón **★ Guardar favoritos** que persiste la selección en la BD

Clases CSS añadidas:

| Clase                   | Descripción                                            |
|-------------------------|--------------------------------------------------------|
| `.etf-select-wrapper`   | Contenedor relativo para input + dropdown              |
| `.etf-selected-tags`    | Contenedor flex-wrap para los tags de selección        |
| `.etf-tag`              | Tag azul con ticker y botón ×                          |
| `.etf-tag-count`        | Badge con el número total de seleccionados             |
| `.etf-dropdown`         | Dropdown absoluto con scroll, z-index 90               |
| `.etf-dropdown-category`| Encabezado de categoría en el dropdown                 |
| `.etf-dropdown-item`    | Fila del dropdown (ticker + nombre + check)            |
| `.etf-dropdown-check`   | ✓ verde visible cuando el activo está seleccionado     |

---

## 9. Selección de más de 3 activos

Se eliminó el límite de 3 tickers para la comparación. Ahora el usuario puede seleccionar tantos activos como quiera (hasta el máximo de 50 favoritos guardados). El formulario de comparación envía todos los tickers seleccionados.

---

## 10. Alertas guardadas en base de datos por usuario

### 10.1 Problema

Las alertas se almacenaban en una **lista en memoria** (`alerts_memory`) en el servidor Python. Esto causaba:
- Se perdían al reiniciar el servidor
- Todos los usuarios compartían las mismas alertas (sin filtro por usuario)

### 10.2 Modelo (`api/models.py`)

Se creó el modelo `Alerta`:

| Campo        | Tipo       | Descripción                                    |
|--------------|------------|------------------------------------------------|
| `id`         | Integer PK | Identificador auto-incremental                 |
| `cliente_id` | Integer FK | Referencia al cliente propietario               |
| `ticker`     | String(20) | Ticker del activo                               |
| `metrica`    | String(50) | Métrica a vigilar (ej: "pe_ratio", "rsi")      |
| `condicion`  | String(2)  | Operador de comparación: `>` o `<`              |
| `umbral`     | Float      | Valor umbral para disparar la alerta            |
| `creada_en`  | DateTime   | Fecha de creación                               |

### 10.3 Endpoints actualizados (`api/app.py`)

Los 3 endpoints ahora requieren sesión activa y filtran por `cliente_id`:

| Método | Ruta                        | Cambio                                                      |
|--------|-----------------------------|--------------------------------------------------------------|
| GET    | `/api/v1/alertas`           | Solo devuelve alertas del usuario logueado                   |
| POST   | `/api/v1/alertas`           | Crea la alerta asociada al `cliente_id` de la sesión         |
| DELETE | `/api/v1/alertas/<id>`      | Solo permite eliminar alertas propias del usuario             |

### 10.4 Frontend (`dashboard/app.js`)

Se añadió `credentials: "include"` a los 3 fetch de alertas para enviar la cookie de sesión con cada petición.

### 10.5 Base de datos

- Nueva tabla: `alertas` con FK a `clientes(id)`
- Creada con: `CREATE TABLE IF NOT EXISTS alertas (...)`
