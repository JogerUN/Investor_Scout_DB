SELECT a.ticker, a.nombre, SUM(pos.posicion_actual) AS total_acciones_en_custodia, SUM(pos.valor_mercado) AS capital_total_mercado
FROM activo a
JOIN posicion pos ON a.id_activo = pos.id_activo
GROUP BY a.id_activo, a.ticker, a.nombre
ORDER BY capital_total_mercado DESC;
