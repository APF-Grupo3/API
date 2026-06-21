Cambios:

icono de persona con capacidad para cerrar sesión
si la persona no ha vinculado su movil aparece icono vincular telegram
si ha vinculado telegram aparece icono enviar resumen por telegram
botón favoritos para incluir en la base de datos
que se puedan seleccionar más de 3 activos
corrección para que las alertas se guarden en la base de datos y no se pierdan al reiniciar el servidor 
creación de botón de suscripción y funcionalidad de flujo resumen diario

### Cambios 21/06/2026

**Suscripción diaria por Telegram:**
- Nueva columna `telegram_suscrito` (boolean) en la tabla `clientes`
- Botón "Suscripción diaria" (verde) visible cuando Telegram está vinculado y no suscrito
- Botón "Anular suscripción" (rojo) visible cuando ya está suscrito
- Endpoint `POST /api/v1/telegram/suscripcion` para activar/desactivar
- El estado se refresca desde BD al hacer clic (sin problemas de refresh)

**Flujo resumen diario (n8n) confirmado:**
- Endpoint `GET /api/v1/telegram/usuarios-suscritos` ahora filtra por `telegram_suscrito = True`
- Usa `etfs_favoritos` como fallback si `telegram_tickers` es NULL
- Workflow n8n con `host.docker.internal` (no localhost)
- No necesitó cambios en el workflow, solo en el backend

**Sistema de alertas completo:**
- Máximo 5 alertas por usuario (validación en backend)
- Nueva columna `periodo` en alertas (1d, 5d, 1wk, 1mo, 3mo, 6mo, 1y)
- Selector de periodo en el formulario del dashboard
- Endpoint `GET /api/v1/alertas/comprobar` — calcula métricas de cada alerta con su periodo y devuelve las disparadas con chat_id del usuario
- Workflow n8n `workflow_verificacion_alertas.json` — se ejecuta a las 22h L-V (cierre), envía mensaje individual por Telegram a cada usuario cuya alerta se dispare
- Nueva tabla `alertas_log` — registra cada alerta disparada (alerta_id, cliente_id, ticker, metrica, condicion, umbral, valor_actual, periodo, fecha)

**Organización:**
- Carpeta `n8n` movida de `docs/` a `integraciones/n8n/`
- Referencias actualizadas en documentaciónLorena.md


- cambios pendientes que  me gustaría implementar:

creo que podríamos hacer otras tabs (ventanas como en el html del profesor)
por ejemplo una de gráficas o algo para que no aparezca únicmante una página



