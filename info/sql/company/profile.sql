-- Ficha de un activo: datos generales + detalle de equity o bond
-- (el LEFT JOIN que corresponda va a traer datos, el otro queda en NULL).
-- Parametro: ticker
SELECT
    a.ticker,
    a.nombre,
    a.tipo_activo,
    a.moneda,
    a.exchange,
    a.pais,
    e.sector,
    e.industria,
    e.earnings_date,
    b.fecha_maduracion,
    b.tasa_cupon,
    b.frecuencia_pago,
    b.valor_nominal,
    b.calificacion,
    b.emisor
FROM activo a
LEFT JOIN equity e ON a.id_activo = e.id_activo
LEFT JOIN bond b ON a.id_activo = b.id_activo
WHERE a.ticker = %s;
