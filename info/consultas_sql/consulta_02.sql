SELECT ticker, nombre, moneda, exchange
FROM activo
WHERE tipo_activo = 'EQUITY' AND exchange = 'NASDAQ';