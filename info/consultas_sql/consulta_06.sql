SELECT c.id_cliente, c.nombre, c.apellido, COUNT(p.id_portafolio) AS total_portafolios
FROM cliente c
LEFT JOIN portafolio p ON c.id_cliente = p.id_cliente
GROUP BY c.id_cliente, c.nombre, c.apellido;