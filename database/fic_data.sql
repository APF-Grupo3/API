-- insertar clientes de ejemplo
 INSERT INTO clientes (email, nombre, apellido, pais, telefono) VALUES
('M.SASASA@EMAIL.COM', 'MARIO', 'SASASA', 'ARGENTINA', '123456789',1),
('J.DOE@EMAIL.COM', 'JOHN', 'DOE', 'USA', '987654321',1),
('ELE.ASA@EMAIL.COM', 'ELE', 'ASA', 'SPAIN', '555555555',1),

-- insetar transacciones de ejemplo
-- transacciones para cliente 1
INSERT INTO transacciones (cliente_id, monto, moneda, tipo, estado, descripcion, referencia_externa, metadara, fecha_transaccion) VALUES
(1, 100.00, 'USD', 'pagado', 'completada', 'Compra de producto A', 'REF12345', '{"detalle":"Producto A, cantidad: 1"}', CURRENT_TIMESTAMP),
(1, 50.00, 'USD', 'pendiente', 'pendiente', 'Compra de producto B', 'REF12346', '{"detalle":"Producto B, cantidad: 2"}', CURRENT_TIMESTAMP),
(1, 20.00, 'USD', 'rembolso', 'completada', 'Rembolso por producto C', 'REF12347', '{"detalle":"Producto C, cantidad: 1"}', CURRENT_TIMESTAMP),

-- transacciones para cliente 2
(2, 200.00, 'USD', 'pagado', 'completada', 'Compra de producto D', 'REF22345', '{"detalle":"Producto D, cantidad: 1"}', CURRENT_TIMESTAMP),
(2, 80.00, 'USD', 'pendiente', 'pendiente', 'Compra de producto E', 'REF22346', '{"detalle":"Producto E, cantidad: 4"}', CURRENT_TIMESTAMP),
(2, 30.00, 'USD', 'rembolso', 'completada', 'Rembolso por producto F', 'REF22347', '{"detalle":"Producto F, cantidad: 2"}', CURRENT_TIMESTAMP),

-- transacciones para cliente 3
(3, 150.00, 'USD', 'pagado', 'completada', 'Compra de producto G', 'REF32345', '{"detalle":"Producto G, cantidad: 1"}', CURRENT_TIMESTAMP),
(3, 60.00, 'USD', 'pendiente', 'pendiente', 'Compra de producto H', 'REF32346', '{"detalle":"Producto H, cantidad: 3"}', CURRENT_TIMESTAMP),
(3, 25.00, 'USD', 'rembolso', 'completada', 'Rembolso por producto I', 'REF32347', '{"detalle":"Producto I, cantidad: 1"}', CURRENT_TIMESTAMP);


-- insertar registros de auditoría logs de ejemplo
INSERT INTO auditoria_logs (cliente_id, accion, usuario, ip_address, timestamp) VALUES
(1, 'creación de cuenta', 'admin', '127.0.0.1', datetime('now')),
(1, 'desactivación de cuenta', 'admin', '127.0.0.1', datetime('now', '-1 day')),
(2, 'creación de cuenta', 'admin', '127.0.0.1', datetime('now', '-5 days'));