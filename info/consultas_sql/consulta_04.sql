SELECT a.ticker, a.nombre, b.tasa_cupon, b.fecha_maduracion, b.emisor
FROM activo a
JOIN bond b ON a.id_activo = b.id_activo
WHERE b.calificacion = 'AAA';
