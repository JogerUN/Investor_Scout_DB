-- Muestra las posiciones activas de un portafolio.
-- Parametro: id_portafolio
SELECT
    a.ticker,
    a.nombre,
    p.posicion_actual AS acciones,
    p.costo_base,
    p.valor_mercado,
    p.unrealized_pnl,
    p.daily_pnl
FROM posicion p
JOIN activo a ON p.id_activo = a.id_activo
WHERE p.id_portafolio = %s;
