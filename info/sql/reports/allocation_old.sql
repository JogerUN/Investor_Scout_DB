-- Distribucion del portafolio.
-- Parametro esperado: %s = id_portafolio

WITH total_portafolio AS
(
    SELECT IFNULL(SUM(valor_mercado),0) AS total_valor
    FROM posicion
    WHERE id_portafolio = %s 
)

SELECT 
    a.ticker,
    a.tipo_activo,
    p.posicion_actual,
    p.costo_base,
    p.valor_mercado,
    ROUND(
        IFNULL(
            p.valor_mercado / NULLIF(t.total_valor,0) * 100,
            0
        ),
        2
    ) AS porcentaje
FROM posicion AS p
JOIN activo AS a
ON p.id_activo = a.id_activo
CROSS JOIN total_portafolio AS t 
WHERE p.id_portafolio = %s
ORDER BY p.valor_mercado DESC;