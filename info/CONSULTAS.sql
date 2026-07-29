-- SCRIPT CONSULTAS

-- 1. ¿Cuáles son los datos de contacto de todos los clientes registrados ordenados por fecha de registro?

SELECT id_cliente, nombre, apellido, email, telefono, fecha_registro
FROM cliente
ORDER BY fecha_registro DESC;


-- 2. ¿Qué activos de tipo 'EQUITY' cotizan actualmente en el mercado NASDAQ?

SELECT ticker, nombre, moneda, exchange
FROM activo
WHERE tipo_activo = 'EQUITY' AND exchange = 'NASDAQ';


-- 3. ¿Cuáles portafolios tienen un perfil de riesgo 'AGRESIVO' o 'MODERADO' y cuentan con más de 1,000 USD en efectivo?

SELECT nombre_portafolio, perfil_riesgo, cash
FROM portafolio
WHERE perfil_riesgo IN ('AGRESIVO', 'MODERADO') AND cash > 1000.00;


-- 4. ¿Cuáles son los bonos disponibles en el sistema con calificación 'AAA' y cuál es su tasa de cupón?
SELECT a.ticker, a.nombre, b.tasa_cupon, b.fecha_maduracion, b.emisor
FROM activo a
JOIN bond b ON a.id_activo = b.id_activo
WHERE b.calificacion = 'AAA';


-- 5. ¿Qué empresas del sector 'Technology' reportarán resultados (earnings date) en los próximos días?
SELECT a.ticker, a.nombre, e.sector, e.industria, e.earnings_date
FROM activo a
JOIN equity e ON a.id_activo = e.id_activo
WHERE e.sector = 'Technology' AND e.earnings_date IS NOT NULL
ORDER BY e.earnings_date ASC;



-- =============================================================
-- NIVEL 2: CONSULTAS INTERMEDIAS (Joins, Agregaciones y Group By)
-- =============================================================

-- 6. ¿Cuántos portafolios activos tiene cada cliente registrados a su nombre?
SELECT c.id_cliente, c.nombre, c.apellido, COUNT(p.id_portafolio) AS total_portafolios
FROM cliente c
LEFT JOIN portafolio p ON c.id_cliente = p.id_cliente
GROUP BY c.id_cliente, c.nombre, c.apellido;


-- 7. ¿Cuál es el valor total invertido en posiciones activas (excluyendo el efectivo) por cada portafolio?
SELECT p.id_portafolio, p.nombre_portafolio, SUM(pos.valor_mercado) AS valor_total_posiciones
FROM portafolio p
JOIN posicion pos ON p.id_portafolio = pos.id_portafolio
GROUP BY p.id_portafolio, p.nombre_portafolio;


-- 8. ¿Cuál es el total invertido por activo sumando todas las cuentas de los clientes?
SELECT a.ticker, a.nombre, SUM(pos.posicion_actual) AS total_acciones_en_custodia, SUM(pos.valor_mercado) AS capital_total_mercado
FROM activo a
JOIN posicion pos ON a.id_activo = pos.id_activo
GROUP BY a.id_activo, a.ticker, a.nombre
ORDER BY capital_total_mercado DESC;


-- 9. ¿Cuál es el monto total gastado en comisiones (fees) de broker por portafolio en sus movimientos?
SELECT p.id_portafolio, p.nombre_portafolio, SUM(m.fee) AS total_comisiones_pagadas
FROM portafolio p
JOIN movimiento m ON p.id_portafolio = m.id_portafolio
GROUP BY p.id_portafolio, p.nombre_portafolio;


-- 10. ¿Cuáles son los activos que tienen un Ratio P/E menor a 25 y un rendimiento por dividendo (Dividend Yield) mayor al 1%?
SELECT a.ticker, a.nombre, mm.pe_ratio, mm.dividend_yield, mm.fecha
FROM activo a
JOIN metricas_mercado mm ON a.id_activo = mm.id_activo
WHERE mm.pe_ratio < 25.00 AND mm.dividend_yield > 0.0100;

-- =============================================================
-- NIVEL 3: CONSULTAS AVANZADAS (Subconsultas, CTEs, Window Functions y Lógica de Negocio)
-- =============================================================

-- 11. ¿Cuál es el patrimonio total acumulado (Efectivo + Valor de Mercado de Posiciones) de cada cliente?
WITH ValorPosiciones AS (
    SELECT id_portafolio, COALESCE(SUM(valor_mercado), 0) AS valor_titulos
    FROM posicion
    GROUP BY id_portafolio
)
SELECT c.id_cliente, c.nombre, c.apellido,
       SUM(p.cash) AS efectivo_total,
       SUM(COALESCE(vp.valor_titulos, 0)) AS titulos_total,
       (SUM(p.cash) + SUM(COALESCE(vp.valor_titulos, 0))) AS patrimonio_neto_total
FROM cliente c
JOIN portafolio p ON c.id_cliente = p.id_cliente
LEFT JOIN ValorPosiciones vp ON p.id_portafolio = vp.id_portafolio
GROUP BY c.id_cliente, c.nombre, c.apellido;


-- 12. ¿Cuál es la posición con mayor ganancia no realizada (Unrealized PnL) dentro de cada portafolio? (Usando Subconsulta Correlacionada)
SELECT pos.id_portafolio, p.nombre_portafolio, a.ticker, pos.unrealized_pnl
FROM posicion pos
JOIN portafolio p ON pos.id_portafolio = p.id_portafolio
JOIN activo a ON pos.id_activo = a.id_activo
WHERE pos.unrealized_pnl = (
    SELECT MAX(sub_pos.unrealized_pnl)
    FROM posicion sub_pos
    WHERE sub_pos.id_portafolio = pos.id_portafolio
);


-- 13. ¿Cuál es la variación diaria del precio de cierre de los activos ordenados cronológicamente? (Usando Window Function LAG)
SELECT a.ticker, h.fecha, h.close_price AS precio_hoy,
       LAG(h.close_price, 1) OVER (PARTITION BY h.id_activo ORDER BY h.fecha) AS precio_ayer,
       (h.close_price - LAG(h.close_price, 1) OVER (PARTITION BY h.id_activo ORDER BY h.fecha)) AS cambio_nominal
FROM historico h
JOIN activo a ON h.id_activo = a.id_activo;


-- 14. Ranking de portafolios según su Sharpe Ratio diario (Usando Window Function DENSE_RANK)
SELECT p.id_portafolio, p.nombre_portafolio, mp.fecha_calculo, mp.sharpe, mp.retorno_total,
       DENSE_RANK() OVER (PARTITION BY mp.fecha_calculo ORDER BY mp.sharpe DESC) AS ranking_sharpe
FROM portafolio p
JOIN metricas_portafolio mp ON p.id_portafolio = mp.id_portafolio;


-- 15. ¿Qué portafolios tienen un porcentaje de efectivo (Cash) superior al 30% de su valor patrimonio total?
WITH ResumenPortafolio AS (
    SELECT p.id_portafolio, p.nombre_portafolio, p.cash,
           (p.cash + COALESCE(SUM(pos.valor_mercado), 0)) AS valor_total_portafolio
    FROM portafolio p
    LEFT JOIN posicion pos ON p.id_portafolio = pos.id_portafolio
    GROUP BY p.id_portafolio, p.nombre_portafolio, p.cash
)
SELECT id_portafolio, nombre_portafolio, cash, valor_total_portafolio,
       ROUND((cash / valor_total_portafolio) * 100, 2) AS pct_efectivo
FROM ResumenPortafolio
WHERE (cash / valor_total_portafolio) > 0.30;

