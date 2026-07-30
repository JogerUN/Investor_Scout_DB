SELECT p.id_portafolio, p.nombre_portafolio, SUM(pos.valor_mercado) AS valor_total_posiciones
FROM portafolio p
JOIN posicion pos ON p.id_portafolio = pos.id_portafolio
GROUP BY p.id_portafolio, p.nombre_portafolio;