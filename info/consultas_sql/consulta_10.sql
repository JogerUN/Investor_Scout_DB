SELECT a.ticker, a.nombre, mm.pe_ratio, mm.dividend_yield, mm.fecha
FROM activo a
JOIN metricas_mercado mm ON a.id_activo = mm.id_activo
WHERE mm.pe_ratio < 25.00 AND mm.dividend_yield > 0.0100;