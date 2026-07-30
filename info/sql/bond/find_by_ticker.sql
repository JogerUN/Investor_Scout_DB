SELECT 
    id_activo,
    ticker,
    nombre,
    tipo_activo,
    moneda,
    pais
FROM activo
WHERE ticker = %s;