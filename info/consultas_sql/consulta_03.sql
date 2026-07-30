SELECT nombre_portafolio, perfil_riesgo, cash
FROM portafolio
WHERE perfil_riesgo IN ('AGRESIVO', 'MODERADO') AND cash > 1000.00;