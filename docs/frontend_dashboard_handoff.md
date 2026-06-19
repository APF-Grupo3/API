# Handoff técnico: rama `jesus/frontend-dashboard`

## 1. Resumen ejecutivo

En la rama `jesus/frontend-dashboard` se ha construido una demo funcional de **FundCompare** pensada para presentación y trabajo académico, con foco en una experiencia completa pero simple de entender.

Lo que ya existe en esta rama:

- Un **backend Flask** que expone endpoints mínimos funcionales.
- Un **dashboard web** servido por el propio backend.
- Consulta de datos reales de mercado mediante **Yahoo Finance** usando `yfinance`.
- Cálculo de métricas financieras básicas con `pandas` y `numpy`.
- Visualización de resultados en tabla, rankings y gráficos con `Chart.js`.
- Sistema de **alertas temporales en memoria**.
- Un endpoint y botón de **Telegram** preparado como integración futura, todavía sin envío real.

Esta fase está centrada en:

- frontend funcional;
- endpoints mínimos para demo;
- conexión básica con datos reales;
- estructura fácil de explicar al equipo.

Queda fuera de esta fase:

- integración con base de datos;
- persistencia real de alertas;
- automatización programada;
- usuarios reales;
- Telegram operativo.

La carpeta `database/` queda reservada para una fase posterior y para otra persona del grupo.

---

## 2. Archivos creados o modificados

### `api/app.py`

Función principal:

- Es el punto de entrada de la aplicación Flask.
- Define todos los endpoints usados por la demo.
- Descarga datos con `yfinance`.
- Calcula métricas financieras.
- Gestiona alertas temporales en memoria.
- Sirve el dashboard HTML y sus archivos estáticos.

Partes importantes:

- Configuración de Flask y `CORS`.
- Limpieza de variables proxy del entorno para evitar fallos de red con `yfinance`.
- Configuración de caché temporal de `yfinance`.
- Funciones auxiliares para:
  - normalizar período;
  - parsear tickers;
  - descargar histórico;
  - extraer cierres;
  - calcular métricas;
  - generar rankings.
- Lista global `alerts_memory` para alertas temporales.

¿Deben tocarlo otros compañeros?

- Sí, pero con cuidado.
- Es el archivo que probablemente ampliarán quienes trabajen en base de datos, Telegram o scheduler.

Riesgos de modificarlo sin entenderlo:

- Romper contratos JSON que ya usa el frontend.
- Cambiar nombres de campos y dejar de pintar tabla, gráficos o rankings.
- Alterar el cálculo de métricas y cambiar resultados visibles en la demo.
- Introducir dependencias nuevas no previstas para esta fase.

### `dashboard/index.html`

Función principal:

- Define la estructura visual del dashboard.

Partes importantes:

- Header principal.
- Tarjetas superiores de estado.
- Formulario de comparación.
- Tabla comparativa.
- Contenedores de rankings.
- Panel de alertas.
- Botón Telegram.
- Lienzos `<canvas>` para Chart.js.

¿Deben tocarlo otros compañeros?

- Sí, si necesitan mover bloques de interfaz o añadir nuevos paneles visuales.

Riesgos:

- Si se cambian `id` o estructura esperada por `dashboard/app.js`, el frontend deja de funcionar.

### `dashboard/style.css`

Función principal:

- Define el estilo visual del dashboard.

Partes importantes:

- Tema oscuro.
- Tarjetas y paneles.
- Colores de semáforo para métricas.
- Diseño responsive básico para escritorio y móvil.
- Estilo del botón Telegram.

¿Deben tocarlo otros compañeros?

- Solo para ajustes visuales.

Riesgos:

- Cambios agresivos pueden romper legibilidad o responsive.
- No afecta a la lógica, pero sí a la calidad de la demo.

### `dashboard/app.js`

Función principal:

- Es la lógica del frontend.
- Llama a la API con `fetch`.
- Procesa respuestas JSON.
- Rellena tabla, rankings, alertas y gráficos.

Partes importantes:

- Carga del estado de salud de la API.
- Carga de comparación por tickers y período.
- Renderizado de tabla.
- Renderizado de rankings.
- Creación y borrado de alertas.
- Preparación del flujo provisional de Telegram.
- Gestión y destrucción de gráficos Chart.js.

¿Deben tocarlo otros compañeros?

- Sí, especialmente si cambian endpoints o campos JSON.

Riesgos:

- Si se cambian rutas o nombres de campos en backend y no se actualiza este archivo, la interfaz fallará.
- No debe duplicar cálculos financieros ya resueltos por el backend.

### `requirements.txt`

Función principal:

- Declara dependencias mínimas para ejecutar la demo.

Dependencias actuales:

- `Flask`
- `flask-cors`
- `yfinance`
- `pandas`
- `numpy`

¿Deben tocarlo otros compañeros?

- Solo si la siguiente fase realmente necesita nuevas librerías.

Riesgos:

- Cambiar versiones sin validar puede romper `yfinance` o el arranque local.

### `README.md`

Función principal:

- Da una entrada rápida para ejecutar la demo actual.

Partes importantes:

- Sección inicial actualizada con instrucciones resumidas.

Observación:

- Debajo de esa cabecera aún existe documentación histórica de una arquitectura más amplia.
- Puede servir como contexto, pero no describe exactamente la fase actual del dashboard.

¿Deben tocarlo otros compañeros?

- Solo si quieren unificar la documentación general del proyecto.

Riesgos:

- Mezclar documentación futura con la demo actual puede generar confusión.

---

## 3. Arquitectura actual simplificada

La arquitectura actual es deliberadamente simple para que la demo sea fácil de ejecutar, explicar y ampliar después.

Flujo general:

1. El usuario entra en `/dashboard`.
2. El navegador carga `index.html`, `style.css` y `app.js`.
3. `dashboard/app.js` hace peticiones `fetch` al backend Flask.
4. Flask recibe la petición y consulta datos de Yahoo Finance mediante `yfinance`.
5. El backend calcula métricas financieras con `pandas` y `numpy`.
6. Flask devuelve un JSON estructurado.
7. El frontend usa ese JSON para pintar:
   - tabla comparativa;
   - rankings;
   - gráficos;
   - alertas visibles.

Diagrama textual:

```text
Browser / Dashboard
    ->
Flask API
    ->
yfinance (Yahoo Finance)
    ->
calculo de metricas con pandas/numpy
    ->
JSON
    ->
tabla + rankings + graficos
```

Idea clave:

- El **backend calcula**.
- El **frontend visualiza**.

Esto evita duplicar lógica financiera en JavaScript y facilita mantener una única fuente de verdad.

---

## 4. Cómo ejecutar la aplicación

### Requisitos previos

- Tener Python instalado.
- Usar PowerShell en Windows.

### Pasos

1. Crear entorno virtual:

```powershell
python -m venv .venv
```

2. Si PowerShell bloquea la activación, permitirla en la sesión actual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

3. Activar el entorno:

```powershell
.venv\Scripts\Activate.ps1
```

4. Instalar dependencias:

```powershell
pip install -r requirements.txt
```

5. Arrancar la aplicación:

```powershell
python api/app.py
```

### URLs principales

- Dashboard:
  - `http://localhost:5000/dashboard`
- Health:
  - `http://localhost:5000/api/v1/health`
- Comparación de ejemplo:
  - `http://localhost:5000/api/v1/comparar?tickers=SPY,QQQ,IWM&periodo=1mo`

---

## 5. Endpoints implementados

### `GET /`

Función:

- Redirige al dashboard.

Uso:

- Permite que la raíz de la aplicación lleve directamente a la interfaz.

### `GET /dashboard`

Función:

- Sirve la interfaz web principal.

### `GET /dashboard/<filename>`

Función:

- Sirve archivos estáticos del dashboard, como CSS y JavaScript.

Ejemplos:

- `/dashboard/style.css`
- `/dashboard/app.js`

### `GET /api/v1/health`

Función:

- Devuelve el estado básico de la API.

Campos principales:

- `status`
- `app`
- `data_provider`
- `timestamp`
- `version`

Ejemplo de respuesta:

```json
{
  "status": "ok",
  "app": "FundCompare API",
  "data_provider": "Yahoo Finance",
  "timestamp": "2026-06-19T22:39:40.672571+00:00",
  "version": "1.0.0"
}
```

### `GET /api/v1/comparar`

Función:

- Compara varios activos en una sola petición.

Parámetros:

- `tickers`
- `periodo`

Ejemplo:

```text
GET /api/v1/comparar?tickers=SPY,QQQ,IWM&periodo=1mo
```

Qué devuelve:

- `fecha_consulta`
- `periodo`
- `fondos`
- `ranking_sharpe`
- `ranking_rentabilidad`

Campos de cada elemento en `fondos`:

- `ticker`
- `precio_cierre`
- `rentabilidad_acumulada`
- `volatilidad_anual`
- `sharpe_ratio`
- `sortino_ratio`
- `max_drawdown`
- `observaciones`
- `error`

Comportamiento importante:

- Si falla un ticker, no debe romper toda la respuesta.
- Ese activo devuelve `error: true` y el resto puede seguir funcionando.

### `GET /api/v1/metricas/<ticker>`

Función:

- Devuelve métricas para un solo activo.

Ejemplo:

```text
GET /api/v1/metricas/SPY?periodo=1mo
```

Uso:

- Puede servir para consultas individuales o futuras ampliaciones del dashboard.

### `GET /api/v1/rankings`

Función:

- Devuelve un ranking ordenado según el criterio indicado.

Parámetros:

- `tickers`
- `periodo`
- `criterio`

Criterios documentados para el equipo:

- `sharpe_ratio`
- `sortino_ratio`
- `rentabilidad_acumulada`
- `volatilidad_anual`
- `max_drawdown`

Observación:

- En la implementación actual también existe soporte para `precio_cierre`.

Ejemplo:

```text
GET /api/v1/rankings?tickers=SPY,QQQ,IWM&periodo=1mo&criterio=sharpe_ratio
```

### `GET /api/v1/alertas`

Función:

- Devuelve las alertas temporales creadas en memoria.

Importante:

- No hay persistencia.
- Si la app se reinicia, se pierden.

### `POST /api/v1/alertas`

Función:

- Crea una alerta temporal en memoria.

Campos esperados:

- `ticker`
- `metrica`
- `condicion`
- `umbral`

Ejemplo de payload:

```json
{
  "ticker": "SPY",
  "metrica": "sharpe_ratio",
  "condicion": "<",
  "umbral": 1.0
}
```

### `DELETE /api/v1/alertas/<id>`

Función:

- Elimina una alerta temporal por identificador.

### `POST /api/v1/telegram/enviar-resumen`

Función:

- Es un placeholder.
- No envía mensajes reales todavía.

Qué devuelve:

- Estado de preparación.
- Mensaje indicando que la integración real queda para fase posterior.

Ejemplo de idea de respuesta:

```json
{
  "status": "prepared",
  "message": "Integracion con Telegram preparada para fase posterior"
}
```

---

## 6. Métricas financieras calculadas

La demo muestra métricas sencillas, suficientes para explicar comparación de activos en clase sin entrar en matemáticas excesivamente complejas.

### Rentabilidad acumulada

Qué mide:

- Cuánto ha subido o bajado el activo en el período consultado.

Lógica:

- Se compara el precio final con el precio inicial.

Interpretación:

- Valor positivo: el activo ha ganado valor en ese período.
- Valor negativo: el activo ha perdido valor.

Utilidad en el dashboard:

- Permite ver qué activo ha tenido mejor comportamiento reciente.

### Volatilidad anualizada

Qué mide:

- La variabilidad de los retornos diarios, proyectada a escala anual.

Interpretación:

- Valor alto: movimiento más brusco, más riesgo o más inestabilidad.
- Valor bajo: comportamiento más estable.

Utilidad en el dashboard:

- Ayuda a comparar el riesgo relativo entre activos.

### Sharpe Ratio

Qué mide:

- Relación entre retorno esperado aproximado y volatilidad.

Interpretación:

- Más alto suele ser mejor.
- Un Sharpe alto sugiere mejor retorno ajustado por riesgo.

Utilidad en el dashboard:

- Se usa como criterio principal de ranking.

### Sortino Ratio

Qué mide:

- Similar al Sharpe, pero penalizando solo la volatilidad negativa.

Interpretación:

- Más alto suele ser mejor.
- Puede ser más útil cuando interesa centrarse en el riesgo de caídas.

Utilidad en el dashboard:

- Complementa al Sharpe para evaluar calidad del rendimiento.

### Max Drawdown

Qué mide:

- La mayor caída sufrida desde un máximo acumulado hasta un mínimo posterior dentro del período.

Interpretación:

- Cuanto más negativo, peor.
- Indica la peor racha de caída observada.

Utilidad en el dashboard:

- Ayuda a visualizar el riesgo de pérdida temporal importante.

---

## 7. Funcionamiento del frontend

El frontend está diseñado como un dashboard sencillo, visual y comprensible.

### Header

Incluye:

- nombre del producto `FundCompare`;
- subtítulo explicativo;
- botón visible para Telegram.

Objetivo:

- Presentar rápidamente la demo y su propósito.

### Tarjetas superiores

Muestran:

- estado de la API;
- proveedor de datos;
- última consulta;
- número de activos comparados.

Objetivo:

- Dar contexto rápido al usuario antes de mirar la tabla.

### Formulario de comparación

Permite:

- escribir tickers separados por comas;
- elegir período;
- lanzar la comparación.

Comportamiento:

- `dashboard/app.js` captura el envío del formulario.
- Hace un `fetch` a `/api/v1/comparar`.
- Procesa la respuesta JSON.

### Tabla comparativa

Muestra por activo:

- ticker;
- precio de cierre;
- rentabilidad acumulada;
- volatilidad anual;
- Sharpe;
- Sortino;
- max drawdown.

Detalles visuales:

- porcentajes y números formateados;
- colores para destacar positivo, negativo, advertencia o dato no disponible.

### Gráficos Chart.js

Actualmente se renderizan:

- gráfico de barras de rentabilidad acumulada;
- gráfico de barras de Sharpe Ratio.

Objetivo:

- Hacer la comparación más rápida visualmente.

### Rankings

Se muestran dos listas:

- ranking por Sharpe;
- ranking por rentabilidad.

Objetivo:

- Resumir la comparación sin depender solo de la tabla.

### Alertas en memoria

El panel permite:

- crear alerta temporal;
- listar alertas activas;
- eliminar alertas.

Importante:

- No hay base de datos.
- Todo se guarda en una lista Python mientras la app está encendida.

### Botón Telegram provisional

Comportamiento:

- Llama a `POST /api/v1/telegram/enviar-resumen`.
- Muestra un mensaje de integración preparada.

Importante:

- No existe todavía bot real ni envío real de mensajes.

### Comunicación entre `dashboard/app.js` y `api/app.py`

La comunicación es directa por `fetch`:

- `fetch("/api/v1/health")`
- `fetch("/api/v1/comparar?...")`
- `fetch("/api/v1/alertas")`
- `fetch("/api/v1/telegram/enviar-resumen", { method: "POST" })`

Responsabilidad de cada capa:

- Flask:
  - obtiene datos;
  - calcula métricas;
  - construye JSON.
- JavaScript:
  - solicita datos;
  - interpreta la respuesta;
  - actualiza el DOM;
  - dibuja gráficos.

---

## 8. Qué NO se ha hecho todavía

Es importante que el equipo tenga claro lo que esta rama **no** resuelve aún:

- No hay base de datos integrada.
- Las alertas no persisten al cerrar la app.
- No hay Telegram real todavía.
- No hay scheduler automático todavía.
- No hay usuarios reales ni login.
- No hay tests automatizados.
- No hay despliegue en servidor.
- No hay integración completa con SQLite o SQLAlchemy.

---

## 9. Cómo pueden continuar trabajando los compañeros

### Compañero de base de datos

Trabajo recomendado:

- crear tabla de usuarios;
- crear tabla de alertas;
- crear tabla de histórico de métricas;
- sustituir la lista en memoria por persistencia real;
- conectar endpoints de alertas con base de datos;
- mantener el mismo contrato JSON para no romper el frontend.

### Compañero de Telegram

Trabajo recomendado:

- añadir token y configuración segura;
- implementar función real de envío;
- conectar `/api/v1/telegram/enviar-resumen` con el bot;
- preparar mensajes de resumen;
- preparar envío futuro de alertas automáticas.

### Compañero de automatización / scheduler

Trabajo recomendado:

- integrar APScheduler u otra solución equivalente;
- actualizar métricas cada cierto tiempo;
- comprobar alertas activas;
- registrar logs de ejecución;
- preparar flujo de actualización sin intervención manual.

### Compañero de documentación / vídeo

Trabajo recomendado:

- abrir el dashboard;
- comparar `SPY`, `QQQ` e `IWM`;
- explicar tabla y rankings;
- mostrar gráficos;
- crear y borrar una alerta;
- pulsar el botón Telegram;
- explicar qué partes quedan preparadas para la siguiente fase.

---

## 10. Riesgos y recomendaciones

### Riesgos principales

- No cambiar nombres de campos JSON sin actualizar `dashboard/app.js`.
- No duplicar lógica financiera en el frontend.
- No tocar `database/` desde esta rama sin coordinación.
- Mantener compatibilidad con los endpoints actuales.

### Recomendaciones adicionales

- Si se cambia una ruta o un parámetro de la API, revisar inmediatamente el frontend.
- Si se añade persistencia real, conservar la estructura JSON actual para no romper la demo.
- Si `yfinance` falla en un ticker, mantener el comportamiento actual de error por activo y no error global.
- Separar bien mejoras visuales de cambios de lógica.

---

## 11. Checklist para validar que todo funciona

- La app arranca con `python api/app.py`.
- Se puede abrir `http://localhost:5000/dashboard`.
- `http://localhost:5000/api/v1/health` responde correctamente.
- `http://localhost:5000/api/v1/comparar?tickers=SPY,QQQ,IWM&periodo=1mo` devuelve datos.
- El dashboard muestra tabla comparativa.
- Los gráficos aparecen.
- Los rankings se rellenan.
- Se puede crear una alerta.
- Se puede eliminar una alerta.
- El botón Telegram muestra mensaje provisional.
- No se ha modificado `database/`.

---

## Cierre

La rama `jesus/frontend-dashboard` deja una base clara para demo y continuación por módulos. El valor principal de esta fase es que ya existe una aplicación ejecutable, visible y explicable, con separación razonable entre frontend, API y cálculo de métricas.
