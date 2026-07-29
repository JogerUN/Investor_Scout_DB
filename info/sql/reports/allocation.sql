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
