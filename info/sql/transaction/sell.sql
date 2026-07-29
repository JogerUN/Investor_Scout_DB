-- Ejecuta una venta (SELL). Misma logica que buy.sql, pero tipo SELL.
-- Parametros en orden: id_portafolio, ticker, cantidad, precio, fecha
CALL p_realizar_transaccion(%s, %s, 'SELL', %s, %s, %s);
