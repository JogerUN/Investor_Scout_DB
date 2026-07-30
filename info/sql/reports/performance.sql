-- Métricas de rendimiento del portafolio (espera 3 parámetros: id_portafolio, id_portafolio, id_portafolio)
SELECT
    fecha_calculo,
    retorno_total,
    volatilidad,
    sharpe,
    max_drawdown,
    beta,
    alpha,
    fn_total_value(%s) AS valor_total,
    fn_unrealized_pnl(%s) AS ganancia_no_realizada
FROM metricas_portafolio
WHERE id_portafolio = %s
ORDER BY fecha_calculo DESC
LIMIT 1;