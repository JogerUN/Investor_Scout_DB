-- =============================================================
-- SEED SCRIPT: seed.sql
-- InvestorScout Database Population Script
-- =============================================================

USE InvestorScout2;

SET FOREIGN_KEY_CHECKS = 0;

-- -------------------------------------------------------------
-- 1. CLEAN EXISTING DATA
-- -------------------------------------------------------------
TRUNCATE TABLE snapshot_posicion;
TRUNCATE TABLE movimiento;
TRUNCATE TABLE posicion;
TRUNCATE TABLE activos_portafolio;
TRUNCATE TABLE metricas_portafolio;
TRUNCATE TABLE metricas_mercado;
TRUNCATE TABLE historico;
TRUNCATE TABLE equity;
TRUNCATE TABLE bond;
TRUNCATE TABLE activo;
TRUNCATE TABLE portafolio;
TRUNCATE TABLE cliente;

SET FOREIGN_KEY_CHECKS = 1;

-- -------------------------------------------------------------
-- 2. CLIENTE
-- -------------------------------------------------------------
INSERT INTO cliente (id_cliente, nombre, apellido, email, password_hash, telefono, fecha_registro) VALUES
(1, 'Carlos', 'Mendoza', 'carlos.mendoza@email.com', '$2b$12$eImiTXuWVxfM37uY4JANjO5E.123456789012345678901234567', '+573001234567', '2024-01-10 08:30:00'),
(2, 'Ana', 'Gómez', 'ana.gomez@email.com', '$2b$12$eImiTXuWVxfM37uY4JANjO5E.123456789012345678901234568', '+573109876543', '2024-02-15 10:15:00'),
(3, 'Roberto', 'Silva', 'roberto.silva@email.com', '$2b$12$eImiTXuWVxfM37uY4JANjO5E.123456789012345678901234569', '+573205554433', '2024-03-01 14:00:00');

-- -------------------------------------------------------------
-- 3. PORTAFOLIO
-- -------------------------------------------------------------
INSERT INTO portafolio (id_portafolio, id_cliente, nombre_portafolio, perfil_riesgo, cash, fecha_creacion) VALUES
(1, 1, 'Portafolio Crecimiento Tech', 'AGRESIVO', 15000.00, '2024-01-11 09:00:00'),
(2, 1, 'Portafolio Conservador Renta Fija', 'CONSERVADOR', 5000.00, '2024-01-12 11:30:00'),
(3, 2, 'Portafolio Balanceado Global', 'MODERADO', 8500.00, '2024-02-16 12:00:00'),
(4, 3, 'Portafolio Especulativo', 'AGRESIVO', 2000.00, '2024-03-02 15:45:00');

-- -------------------------------------------------------------
-- 4. ACTIVO (EQUITY & BOND)
-- -------------------------------------------------------------
INSERT INTO activo (id_activo, ticker, nombre, tipo_activo, moneda, exchange, pais) VALUES
(1, 'AAPL', 'Apple Inc.', 'EQUITY', 'USD', 'NASDAQ', 'USA'),
(2, 'MSFT', 'Microsoft Corporation', 'EQUITY', 'USD', 'NASDAQ', 'USA'),
(3, 'NVDA', 'NVIDIA Corporation', 'EQUITY', 'USD', 'NASDAQ', 'USA'),
(4, 'US10Y', 'US Treasury Bond 10Y 4.25%', 'BOND', 'USD', 'NYSE', 'USA'),
(5, 'CORPBOND1', 'Corporate Tech Bond 5.5%', 'BOND', 'USD', 'NYSE', 'USA');

-- -------------------------------------------------------------
-- 5. EQUITY (Subtipo ISA de ACTIVO)
-- Triggers `verificar_equity` validados al insertar
-- -------------------------------------------------------------
INSERT INTO equity (id_equity, id_activo, sector, industria, earnings_date) VALUES
(1, 1, 'Technology', 'Consumer Electronics', '2026-08-05'),
(2, 2, 'Technology', 'Software—Infrastructure', '2026-08-10'),
(3, 3, 'Technology', 'Semiconductors', '2026-08-20');

-- -------------------------------------------------------------
-- 6. BOND (Subtipo ISA de ACTIVO)
-- Triggers `verificar_bond` validados al insertar
-- -------------------------------------------------------------
INSERT INTO bond (id_bond, id_activo, fecha_maduracion, tasa_cupon, frecuencia_pago, valor_nominal, calificacion, emisor) VALUES
(1, 4, '2034-02-15', 4.2500, 'SEMESTRAL', 1000.00, 'AAA', 'SOBERANO'),
(2, 5, '2029-06-30', 5.5000, 'TRIMESTRAL', 1000.00, 'AAA', 'CORPORATIVO');

-- -------------------------------------------------------------
-- 7. ACTIVOS_PORTAFOLIO (Relación N:N)
-- -------------------------------------------------------------
INSERT INTO activos_portafolio (id_activo, id_portafolio) VALUES
(1, 1), (2, 1), (3, 1),
(4, 2), (5, 2),
(1, 3), (4, 3);

-- -------------------------------------------------------------
-- 8. METRICAS_MERCADO (Datos históricos diarios de mercado)
-- -------------------------------------------------------------
INSERT INTO metricas_mercado (id_metricas, id_activo, fecha, precio, market_cap, enterprise_value, pe_ratio, pe_forward, beta, dividend_yield) VALUES
-- 2026-07-25
(1, 1, '2026-07-25', 180.00, 2800000000000, 2750000000000, 24.50, 22.10, 1.15, 0.0150),
(2, 2, '2026-07-25', 410.00, 3000000000000, 2950000000000, 32.00, 28.50, 0.90, 0.0080),
(3, 3, '2026-07-25', 120.00, 2900000000000, 2880000000000, 40.00, 35.00, 1.75, 0.0005),
(4, 4, '2026-07-25', 98.50, NULL, NULL, NULL, NULL, 0.15, 0.0425),
(5, 5, '2026-07-25', 101.20, NULL, NULL, NULL, NULL, 0.25, 0.0550),

-- 2026-07-26
(6, 1, '2026-07-26', 182.50, 2830000000000, 2780000000000, 24.80, 22.30, 1.15, 0.0148),
(7, 2, '2026-07-26', 415.00, 3040000000000, 2990000000000, 32.40, 28.80, 0.90, 0.0079),
(8, 3, '2026-07-26', 123.00, 2970000000000, 2950000000000, 41.00, 36.00, 1.75, 0.0005),
(9, 4, '2026-07-26', 99.00, NULL, NULL, NULL, NULL, 0.15, 0.0425),
(10, 5, '2026-07-26', 101.50, NULL, NULL, NULL, NULL, 0.25, 0.0550),

-- 2026-07-27 (Latest Date for calculation)
(11, 1, '2026-07-27', 185.00, 2870000000000, 2820000000000, 23.50, 21.00, 1.12, 0.0160),
(12, 2, '2026-07-27', 420.00, 3080000000000, 3030000000000, 31.50, 27.50, 0.88, 0.0082),
(13, 3, '2026-07-27', 125.00, 3020000000000, 3000000000000, 42.00, 37.00, 1.70, 0.0005),
(14, 4, '2026-07-27', 99.20, NULL, NULL, NULL, NULL, 0.14, 0.0425),
(15, 5, '2026-07-27', 102.00, NULL, NULL, NULL, NULL, 0.24, 0.0550);

-- -------------------------------------------------------------
-- 9. HISTORICO (OHLCV Precios)
-- -------------------------------------------------------------
INSERT INTO historico (id_activo, fecha, open_price, high_price, low_price, close_price, volumen) VALUES
(1, '2026-07-25', 178.50, 181.00, 178.00, 180.00, 50000000),
(1, '2026-07-26', 180.50, 183.00, 179.80, 182.50, 52000000),
(1, '2026-07-27', 182.00, 186.00, 181.50, 185.00, 55000000),

(2, '2026-07-25', 405.00, 412.00, 404.00, 410.00, 22000000),
(2, '2026-07-26', 411.00, 416.50, 410.00, 415.00, 21000000),
(2, '2026-07-27', 415.50, 421.00, 414.00, 420.00, 25000000),

(3, '2026-07-25', 117.00, 121.00, 116.50, 120.00, 80000000),
(3, '2026-07-26', 120.50, 124.00, 119.50, 123.00, 85000000),
(3, '2026-07-27', 123.50, 126.00, 122.00, 125.00, 90000000),

(4, '2026-07-25', 98.20, 98.70, 98.10, 98.50, 100000),
(4, '2026-07-26', 98.60, 99.10, 98.50, 99.00, 120000),
(4, '2026-07-27', 99.00, 99.40, 98.90, 99.20, 110000),

(5, '2026-07-25', 101.00, 101.40, 100.80, 101.20, 50000),
(5, '2026-07-26', 101.20, 101.70, 101.10, 101.50, 60000),
(5, '2026-07-27', 101.60, 102.20, 101.50, 102.00, 55000);

-- -------------------------------------------------------------
-- 10. MOVIMIENTO
-- Trigger `verificar_limite_movimiento` validado al insertar
-- -------------------------------------------------------------
INSERT INTO movimiento (id_movimiento, id_portafolio, id_activo, tipo_mov, cantidad, precio_por_accion, fee, notas, fecha_transaccion) VALUES
(1, 1, 1, 'BUY', 50.00000000, 175.000000, 10.000000, 'Compra inicial AAPL', '2024-01-15 10:00:00'),
(2, 1, 2, 'BUY', 20.00000000, 390.000000, 15.000000, 'Compra inicial MSFT', '2024-01-16 11:30:00'),
(3, 1, 3, 'BUY', 100.00000000, 110.000000, 20.000000, 'Compra inicial NVDA', '2024-01-17 14:15:00'),
(4, 2, 4, 'BUY', 30.00000000, 97.000000, 5.000000, 'Compra bono US10Y', '2024-01-20 09:45:00'),
(5, 2, 5, 'BUY', 20.00000000, 100.000000, 5.000000, 'Compra bono Corp', '2024-01-21 16:00:00'),
(6, 3, 1, 'BUY', 25.00000000, 178.000000, 7.500000, 'Compra AAPL portafolio 3', '2024-02-20 10:30:00'),
(7, 3, 4, 'BUY', 40.00000000, 98.000000, 10.000000, 'Compra US10Y portafolio 3', '2024-02-22 13:20:00');

-- -------------------------------------------------------------
-- 11. POSICION
-- -------------------------------------------------------------
INSERT INTO posicion (id_portafolio, id_activo, posicion_actual, costo_base, valor_mercado, unrealized_pnl, daily_pnl, fecha_adquisicion) VALUES
(1, 1, 50.00000000, 175.000000, 9250.00, 500.00, 125.00, '2024-01-15 10:00:00'),
(1, 2, 20.00000000, 390.000000, 8400.00, 600.00, 100.00, '2024-01-16 11:30:00'),
(1, 3, 100.00000000, 110.000000, 12500.00, 1500.00, 200.00, '2024-01-17 14:15:00'),

(2, 4, 30.00000000, 97.000000, 2976.00, 66.00, 6.00, '2024-01-20 09:45:00'),
(2, 5, 20.00000000, 100.000000, 2040.00, 40.00, 10.00, '2024-01-21 16:00:00'),

(3, 1, 25.00000000, 178.000000, 4625.00, 175.00, 62.50, '2024-02-20 10:30:00'),
(3, 4, 40.00000000, 98.000000, 3968.00, 48.00, 8.00, '2024-02-22 13:20:00');

-- -------------------------------------------------------------
-- 12. METRICAS_PORTAFOLIO
-- -------------------------------------------------------------
INSERT INTO metricas_portafolio (id_portafolio, fecha_calculo, retorno_total, volatilidad, sharpe, max_drawdown, beta, alpha) VALUES
(1, '2026-07-26', 0.1250, 0.1850, 1.4500, -0.0820, 1.2000, 0.0350),
(1, '2026-07-27', 0.1420, 0.1820, 1.5800, -0.0820, 1.1800, 0.0410),

(2, '2026-07-26', 0.0320, 0.0450, 2.1000, -0.0150, 0.1800, 0.0100),
(2, '2026-07-27', 0.0350, 0.0440, 2.2500, -0.0150, 0.1700, 0.0120),

(3, '2026-07-26', 0.0680, 0.1100, 1.2000, -0.0450, 0.7500, 0.0180),
(3, '2026-07-27', 0.0750, 0.1080, 1.3200, -0.0450, 0.7400, 0.0210);

-- -------------------------------------------------------------
-- 13. SNAPSHOT_POSICION
-- -------------------------------------------------------------
INSERT INTO snapshot_posicion (id_snapshot, id_portafolio, id_activo, fecha_snapshot, posicion_actual, precio_cierre, costo_base, valor_mercado, unrealized_pnl, change_pct) VALUES
(1, 1, 1, '2026-07-26', 50.00000000, 182.500000, 175.000000, 9125.00, 375.00, 0.0139),
(2, 1, 2, '2026-07-26', 20.00000000, 415.000000, 390.000000, 8300.00, 500.00, 0.0122),
(3, 1, 3, '2026-07-26', 100.00000000, 123.000000, 110.000000, 12300.00, 1300.00, 0.0250),

(4, 1, 1, '2026-07-27', 50.00000000, 185.000000, 175.000000, 9250.00, 500.00, 0.0137),
(5, 1, 2, '2026-07-27', 20.00000000, 420.000000, 390.000000, 8400.00, 600.00, 0.0120),
(6, 1, 3, '2026-07-27', 100.00000000, 125.000000, 110.000000, 12500.00, 1500.00, 0.0163);
