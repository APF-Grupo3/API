-- total de transacciones por cliente

SELECT 
    c.nombre,
    c.email,
    COUNT(t.id) AS total_transacciones,
    SUM(t.monto) AS total_monto,
    AVG(t.monto) AS promedio_monto
FROM clientes c
LEFT JOIN transacciones t ON c.id = t.cliente_id
GROUP BY c.id
ORDER BY total_monto DESC;


-- transacciones en el último mes 
select 
    t.id,
    t.fecha,
    c.nombre,
    t.monto,
    t.moneda,
    t.tipo,
    t.estado,
FROM transacciones t
JOIN clientes c ON t.cliente_id = c.id
WHERE t.fecha >= date('now', '-15 days')
ORDER BY t.fecha DESC;

-- trasacciones por estado

-- resuemen diario de transacciones

-- clientes con más transacciones