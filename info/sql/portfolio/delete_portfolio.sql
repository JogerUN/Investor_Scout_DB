-- Elimina un portafolio.
-- OJO: si el portafolio ya tiene movimientos registrados, esto va a
-- fallar con un error de MySQL (fk_movimiento_port es ON DELETE RESTRICT).
-- Eso es el diseño protegiendo el historial, no un error del programa.
-- Parametro: id_portafolio
DELETE FROM portafolio
WHERE id_portafolio = %s;
