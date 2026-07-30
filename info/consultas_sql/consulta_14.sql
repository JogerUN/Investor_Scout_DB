SELECT p.id_portafolio, p.nombre_portafolio, mp.fecha_calculo, mp.sharpe, mp.retorno_total,
       DENSE_RANK() OVER (PARTITION BY mp.fecha_calculo ORDER BY mp.sharpe DESC) AS ranking_sharpe
FROM portafolio p
JOIN metricas_portafolio mp ON p.id_portafolio = mp.id_portafolio;