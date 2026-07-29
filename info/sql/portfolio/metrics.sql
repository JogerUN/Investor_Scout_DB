-- Historico de metricas de performance de un portafolio.
-- Parametro: id_portafolio
SELECT
    fecha_calculo,
    retorno_total,
    volatilidad,
    sharpe,
    max_drawdown,
    beta,
    alpha
FROM metricas_portafolio
WHERE id_portafolio = %s
ORDER BY fecha_calculo DESC;
