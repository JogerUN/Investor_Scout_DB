-- Ultimas metricas de mercado registradas para un activo.
-- Parametro: ticker
SELECT
    mm.fecha,
    mm.precio,
    mm.market_cap,
    mm.enterprise_value,
    mm.pe_ratio,
    mm.pe_forward,
    mm.beta,
    mm.dividend_yield
FROM metricas_mercado mm
JOIN activo a ON mm.id_activo = a.id_activo
WHERE a.ticker = %s
ORDER BY mm.fecha DESC
LIMIT 1;
