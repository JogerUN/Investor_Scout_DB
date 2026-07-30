-- Recalcula valor_mercado y unrealized_pnl de todas las posiciones de
-- un portafolio con el precio de mercado mas reciente disponible.
-- Parametro: id_portafolio
CALL p_recalcular_posiciones(%s);