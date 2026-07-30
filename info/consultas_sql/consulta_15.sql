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
