-- ======================================================================
-- Este archivo es solo de REFERENCIA para copiar cada bloque a su
-- archivo individual dentro de info/sql/. No se ejecuta como un
-- solo script -- cada bloque va en su propio .sql.
-- ======================================================================


-- ======================================================================
-- ARCHIVO: info/sql/portfolio/create_portfolio.sql
-- ======================================================================
-- Crea un nuevo portafolio para un cliente existente.
-- Parametros en orden: id_cliente, nombre_portafolio, perfil_riesgo, cash_inicial
INSERT INTO portafolio (id_cliente, nombre_portafolio, perfil_riesgo, cash)
VALUES (%s, %s, %s, %s);


-- ======================================================================
-- ARCHIVO: info/sql/portfolio/delete_portfolio.sql
-- ======================================================================
-- Elimina un portafolio.
-- OJO: si el portafolio ya tiene movimientos registrados, esto va a
-- fallar con un error de MySQL (fk_movimiento_port es ON DELETE RESTRICT).
-- Eso es el diseño protegiendo el historial, no un error del programa.
-- Parametro: id_portafolio
DELETE FROM portafolio
WHERE id_portafolio = %s;


-- ======================================================================
-- ARCHIVO: info/sql/portfolio/positions.sql
-- ======================================================================
-- Muestra las posiciones activas de un portafolio.
-- Parametro: id_portafolio
SELECT
    a.ticker,
    a.nombre,
    p.posicion_actual AS acciones,
    p.costo_base,
    p.valor_mercado,
    p.unrealized_pnl,
    p.daily_pnl
FROM posicion p
JOIN activo a ON p.id_activo = a.id_activo
WHERE p.id_portafolio = %s;


-- ======================================================================
-- ARCHIVO: info/sql/portfolio/metrics.sql
-- ======================================================================
-- Historico de metricas de performance de un portafolio.
-- Parametro: id_portafolio
SELECT
    fecha_calculo,
    retorno_total,
    volatilidad,
    sharpe,
    max_drawdown,
    beta,
    alpha
FROM metricas_portafolio
WHERE id_portafolio = %s
ORDER BY fecha_calculo DESC;


-- ======================================================================
-- ARCHIVO: info/sql/transaction/buy.sql
-- ======================================================================
-- Ejecuta una compra (BUY). Reutiliza el procedimiento p_realizar_transaccion
-- que ya existe en el schema: descuenta el cash del portafolio y registra
-- el movimiento de forma atomica.
-- Parametros en orden: id_portafolio, ticker, cantidad, precio, fecha
CALL p_realizar_transaccion(%s, %s, 'BUY', %s, %s, %s);


-- ======================================================================
-- ARCHIVO: info/sql/transaction/sell.sql
-- ======================================================================
-- Ejecuta una venta (SELL). Misma logica que buy.sql, pero tipo SELL.
-- Parametros en orden: id_portafolio, ticker, cantidad, precio, fecha
CALL p_realizar_transaccion(%s, %s, 'SELL', %s, %s, %s);


-- ======================================================================
-- ARCHIVO: info/sql/transaction/history.sql
-- ======================================================================
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


-- ======================================================================
-- ARCHIVO: info/sql/company/profile.sql
-- ======================================================================
-- Ficha de un activo: datos generales + detalle de equity o bond
-- (el LEFT JOIN que corresponda va a traer datos, el otro queda en NULL).
-- Parametro: ticker
SELECT
    a.ticker,
    a.nombre,
    a.tipo_activo,
    a.moneda,
    a.exchange,
    a.pais,
    e.sector,
    e.industria,
    e.earnings_date,
    b.fecha_maduracion,
    b.tasa_cupon,
    b.frecuencia_pago,
    b.valor_nominal,
    b.calificacion,
    b.emisor
FROM activo a
LEFT JOIN equity e ON a.id_activo = e.id_activo
LEFT JOIN bond b ON a.id_activo = b.id_activo
WHERE a.ticker = %s;


-- ======================================================================
-- ARCHIVO: info/sql/company/financials.sql
-- ======================================================================
-- Ultimas metricas de mercado registradas para un activo.
-- Parametro: ticker
SELECT
    mm.fecha,
    mm.precio,
    mm.market_cap,
    mm.enterprise_value,
    mm.pe_ratio,
    mm.pe_forward,
    mm.beta,
    mm.dividend_yield
FROM metricas_mercado mm
JOIN activo a ON mm.id_activo = a.id_activo
WHERE a.ticker = %s
ORDER BY mm.fecha DESC
LIMIT 1;


-- ======================================================================
-- ARCHIVO: info/sql/reports/allocation.sql
-- ======================================================================
-- Composicion del portafolio: cuanto pesa cada activo sobre el total invertido.
-- Parametros (el mismo id_portafolio dos veces): id_portafolio, id_portafolio
WITH total_portafolio AS (
    SELECT SUM(valor_mercado) AS total_valor
    FROM posicion
    WHERE id_portafolio = %s
)
SELECT
    a.ticker,
    a.tipo_activo,
    p.valor_mercado,
    ROUND(p.valor_mercado / t.total_valor * 100, 2) AS pct_del_portafolio
FROM posicion p
JOIN activo a ON p.id_activo = a.id_activo
JOIN total_portafolio t
WHERE p.id_portafolio = %s
ORDER BY p.valor_mercado DESC;


-- ======================================================================
-- ARCHIVO: info/sql/reports/performance.sql
-- ======================================================================
-- Resumen de performance, reutilizando fn_total_value y fn_unrealized_pnl
-- que ya existen en el schema.
-- Parametros (el mismo id_portafolio dos veces): id_portafolio, id_portafolio
SELECT
    fn_total_value(%s) AS valor_total,
    fn_unrealized_pnl(%s) AS ganancia_no_realizada;