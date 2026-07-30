SELECT pos.id_portafolio, p.nombre_portafolio, a.ticker, pos.unrealized_pnl
FROM posicion pos
JOIN portafolio p ON pos.id_portafolio = p.id_portafolio
JOIN activo a ON pos.id_activo = a.id_activo
WHERE pos.unrealized_pnl = (
    SELECT MAX(sub_pos.unrealized_pnl)
    FROM posicion sub_pos
    WHERE sub_pos.id_portafolio = pos.id_portafolio
);