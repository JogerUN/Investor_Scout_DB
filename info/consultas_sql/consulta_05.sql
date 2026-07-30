SELECT a.ticker, a.nombre, e.sector, e.industria, e.earnings_date
FROM activo a
JOIN equity e ON a.id_activo = e.id_activo
WHERE e.sector = 'Technology' AND e.earnings_date IS NOT NULL
ORDER BY e.earnings_date ASC;