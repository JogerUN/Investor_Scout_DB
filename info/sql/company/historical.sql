-- Precios historicos de un activo (ultimos 30 registros).
-- Parametro: ticker
SELECT
    h.fecha,
    h.open_price,
    h.high_price,
    h.low_price,
    h.close_price,
    h.volumen
FROM historico h
JOIN activo a ON h.id_activo = a.id_activo
WHERE a.ticker = %s
ORDER BY h.fecha DESC
LIMIT 30;
