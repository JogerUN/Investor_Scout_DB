SELECT a.ticker, h.fecha, h.close_price AS precio_hoy,
       LAG(h.close_price, 1) OVER (PARTITION BY h.id_activo ORDER BY h.fecha) AS precio_ayer,
       (h.close_price - LAG(h.close_price, 1) OVER (PARTITION BY h.id_activo ORDER BY h.fecha)) AS cambio_nominal
FROM historico h
JOIN activo a ON h.id_activo = a.id_activo;