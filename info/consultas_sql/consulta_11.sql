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
