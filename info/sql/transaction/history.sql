-- Historial de movimientos (compras/ventas) de un portafolio.
-- Parametro: id_portafolio
SELECT
    m.id_movimiento,
    a.ticker,
    m.tipo_mov,
    m.cantidad,
    m.precio_por_accion,
    m.fee,
    m.fecha_transaccion
FROM movimiento m
JOIN activo a ON m.id_activo = a.id_activo
WHERE m.id_portafolio = %s
ORDER BY m.fecha_transaccion DESC;
