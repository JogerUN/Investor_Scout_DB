SELECT p.id_portafolio, p.nombre_portafolio, SUM(m.fee) AS total_comisiones_pagadas
FROM portafolio p
JOIN movimiento m ON p.id_portafolio = m.id_portafolio
GROUP BY p.id_portafolio, p.nombre_portafolio;