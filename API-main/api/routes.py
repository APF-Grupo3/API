### Clientes 

GET /clientes - Listar todos os clientes
GET /clientes/{id} - Obtener detalles de un cliente específico
POST /clientes - Crear un nuevo cliente
PUT /clientes/{id} - Actualizar la información de un cliente existente
DELETE /clientes/{id} - Eliminar un cliente
GET /clientes/{id}/transacciones - Listar todas las transacciones de un cliente específico
GET /clientes/{id}/portfolio - Obtener el portfolio de un cliente específico

### Transacciones
GET /transacciones
GET /transacciones/{id}
POST /transacciones

### Reportes 
GET /reportes/ventas - Obtener un reporte de ventas por período
GET /reportes/clientes - Obtener un reporte de clientes activos e inactivos
GET /reportes/portfolio - Obtener un reporte del portfolio de clientes

### Portfolio
GET /portfolio - Listar todas las posiciones en el portfolio
GET /portfolio/{id} - Obtener detalles de una posición específica en el portfolio
POST /portfolio - Agregar una nueva posición al portfolio

### webhooks    
POST /webhooks/transacciones - Recibir notificaciones de transacciones desde sistemas externos
POST /webhooks/portfolio - Recibir actualizaciones de portfolio desde sistemas externos

### Auditoría
GET /auditoria - Listar todas las entradas de auditoría
GET /auditoria/{id} - Obtener detalles de una entrada de auditoría específica

