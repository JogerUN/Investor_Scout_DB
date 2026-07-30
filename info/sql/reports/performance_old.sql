-- ultimas metricas calculadas del protafolio
-- Parametro esperado: %s= id_portafolio

SELECT
    fecha_calculo,
    retorno_total,
    volatilidad,
    sharpe,
    max_drawdown,
    beta,
    alpha,

    fn_total_value(%s) AS valor_total, -- Call fuction
    fn_unrealized_pnl(%s) AS ganancia_no_realizada -- Call fuction

FROM metricas_portafolio
WHERE id_portafolio = %s
ORDER BY fecha_calculo DESC
LIMIT 1;