-- Ejecuta una compra (BUY). Reutiliza el procedimiento p_realizar_transaccion
-- que ya existe en el schema: descuenta el cash del portafolio y registra
-- el movimiento de forma atomica.
-- Parametros en orden: id_portafolio, ticker, cantidad, precio, fecha
CALL p_realizar_transaccion(%s, %s, 'BUY', %s, %s, %s);
