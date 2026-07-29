-- Crea un nuevo portafolio para un cliente existente.
-- Parametros en orden: id_cliente, nombre_portafolio, perfil_riesgo, cash_inicial
INSERT INTO portafolio (id_cliente, nombre_portafolio, perfil_riesgo, cash)
VALUES (%s, %s, %s, %s);
