-- ======================================================================
--							CREATE TABLES
-- ======================================================================

DROP DATABASE IF EXISTS InvestorScout2;
CREATE DATABASE InvestorScout2;
USE InvestorScout2;

-- =============================================================
-- INVESTOR SCOUT — DDL MySQL COMPLETO v4
-- Arquitectura: métricas separadas por frecuencia de actualización
-- Motor: MySQL 8.0+ / InnoDB
-- Encoding: utf8mb4
-- =============================================================

SET FOREIGN_KEY_CHECKS = 0;
SET SQL_MODE = 'STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO';

-- -------------------------------------------------------------
-- 1. CLIENTE
-- El inversor registrado. Raíz del sistema.
-- email UNIQUE: un solo acceso por persona.
-- password_hash: NUNCA texto plano. Usar bcrypt en app.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cliente (
    id_cliente      INT             NOT NULL AUTO_INCREMENT,
    nombre          VARCHAR(100)    NOT NULL,
    apellido        VARCHAR(100)    NOT NULL,
    email           VARCHAR(255)    NOT NULL,
    password_hash   VARCHAR(255)    NOT NULL
                    COMMENT 'Hash bcrypt/argon2 — nunca texto plano',
    telefono        VARCHAR(20)         NULL,
    fecha_registro  TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_cliente   PRIMARY KEY (id_cliente),
    CONSTRAINT uq_email     UNIQUE      (email)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Inversores registrados en la plataforma';


-- -------------------------------------------------------------
-- 2. PORTAFOLIO
-- Cuenta de inversión de un cliente.
-- cash: efectivo no invertido en ese portafolio.
-- ON DELETE RESTRICT: no se elimina cliente con portafolios.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS portafolio (
    id_portafolio       INT             NOT NULL AUTO_INCREMENT,
    id_cliente          INT             NOT NULL,
    nombre_portafolio   VARCHAR(150)    NOT NULL,
    perfil_riesgo       ENUM(
                            'CONSERVADOR',
                            'MODERADO',
                            'AGRESIVO'
                        )               NOT NULL DEFAULT 'MODERADO',
    cash                DECIMAL(20,2)   NOT NULL DEFAULT 0.00
                        COMMENT 'Efectivo disponible en USD',
    fecha_creacion      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_portafolio    PRIMARY KEY (id_portafolio),
    CONSTRAINT fk_portafolio_cliente  FOREIGN KEY (id_cliente)
        REFERENCES cliente (id_cliente)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    INDEX idx_portafolio_cliente (id_cliente)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Cuentas de inversión por cliente';

-- -----------------------------------------------------------
-- TABLA 3: METRICAS_PORTAFOLIO
-- Histórico de métricas de performance por portafolio y fecha.
-- PK compuesta (id_portafolio, fecha_calculo):
--   permite un registro por día, preservando el histórico.
-- ON DELETE CASCADE: si el portafolio se elimina, se elimina
--   su historial de métricas (datos dependientes).
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS metricas_portafolio (
    id_portafolio       INT             NOT NULL,
    fecha_calculo       DATE            NOT NULL,
    retorno_total       DECIMAL(8,4)       NULL   COMMENT 'Retorno acumulado %',
    volatilidad         DECIMAL(8,4)       NULL   COMMENT 'Desviación estándar de retornos',
    sharpe              DECIMAL(8,4)       NULL   COMMENT 'Ratio de Sharpe',
    max_drawdown        DECIMAL(8,4)       NULL   COMMENT 'Máxima caída desde pico %',
    beta                DECIMAL(6,4)       NULL   COMMENT 'Sensibilidad relativa al mercado',
    alpha               DECIMAL(8,4)       NULL   COMMENT 'Exceso de retorno vs benchmark',

    CONSTRAINT pk_metricas_portafolio  PRIMARY KEY (id_portafolio, fecha_calculo),
    CONSTRAINT fk_metmetricas_port  FOREIGN KEY (id_portafolio)
        REFERENCES portafolio (id_portafolio)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Histórico diario de métricas de performance por portafolio';


-- -------------------------------------------------------------
-- 4. ACTIVO
-- Catálogo de instrumentos financieros.
-- ticker UNIQUE: no pueden existir dos AAPL.
-- tipo_activo: discriminador ISA → EQUITY o BOND.
-- Aquí NO hay precio ni ratios — esos viven en tablas propias.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS activo (
    id_activo       INT             NOT NULL AUTO_INCREMENT,
    ticker          VARCHAR(20)     NOT NULL,
    nombre          VARCHAR(200)    NOT NULL,
    tipo_activo     ENUM(
                        'EQUITY',
                        'BOND'
                    )               NOT NULL COMMENT 'Discriminador ISA',
    moneda          VARCHAR(3)      NOT NULL DEFAULT 'USD'
                    COMMENT 'ISO 4217',
    exchange        VARCHAR(50)         NULL COMMENT 'NYSE, NASDAQ, BMV...',
    pais            VARCHAR(100)        NULL,

    CONSTRAINT pk_activo    PRIMARY KEY (id_activo),
    CONSTRAINT uq_ticker    UNIQUE      (ticker),

    INDEX idx_activo_tipo (tipo_activo)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Catálogo de instrumentos financieros';
  
  CREATE TABLE IF NOT EXISTS activos_portafolio (
	id_activo INT,
    id_portafolio INT,
    
    PRIMARY KEY (id_activo, id_portafolio),
    FOREIGN KEY (id_activo) REFERENCES activo(id_activo)
		ON DELETE CASCADE
        ON UPDATE CASCADE,
	FOREIGN KEY (id_portafolio) REFERENCES portafolio(id_portafolio)
		ON UPDATE CASCADE
        ON DELETE CASCADE
  );


-- -------------------------------------------------------------
-- 5. MOVIMIENTO
-- Registro INMUTABLE de cada transacción BUY/SELL.
-- Equivalente en BD de la LinkedList de Python.
-- PK simple AUTO_INCREMENT: permite múltiples compras del
-- mismo activo sin colisión de PK.
-- ON DELETE RESTRICT: protege la integridad del historial.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS movimiento (
    id_movimiento       INT             NOT NULL AUTO_INCREMENT,
    id_portafolio       INT             NOT NULL,
    id_activo           INT             NOT NULL,
    tipo_mov            ENUM(
                            'BUY',
                            'SELL'
                        )               NOT NULL,
    cantidad            DECIMAL(18,8)   NOT NULL COMMENT 'Número de acciones',
    precio_por_accion   DECIMAL(18,6)   NOT NULL COMMENT 'Precio unitario al momento',
    fee                 DECIMAL(18,6)   NOT NULL DEFAULT 0.000000
                        COMMENT 'Comisión del bróker',
    notas               TEXT                NULL
                        COMMENT '¿Por qué se realizó esta operación?',
    fecha_transaccion   TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_movimiento    PRIMARY KEY (id_movimiento),
    CONSTRAINT fk_movimiento_port      FOREIGN KEY (id_portafolio)
        REFERENCES portafolio (id_portafolio)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_movimiento_activo    FOREIGN KEY (id_activo)
        REFERENCES activo (id_activo)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    INDEX idx_mov_portafolio    (id_portafolio),
    INDEX idx_mov_activo        (id_activo),
    INDEX idx_mov_fecha         (fecha_transaccion)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Historial inmutable de transacciones — LinkedList en BD';


-- -------------------------------------------------------------
-- 6. POSICION
-- Estado ACTUAL de un activo dentro de un portafolio.
-- PK compuesta (id_portafolio, id_activo): resuelve el N:N.
-- costo_base: precio promedio ponderado, recalculado desde
-- MOVIMIENTO al ejecutar cada operación.
-- ON DELETE CASCADE en portafolio, RESTRICT en activo.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS posicion (
    id_portafolio           INT             NOT NULL,
    id_activo               INT             NOT NULL,
    posicion_actual         DECIMAL(18,8)   NOT NULL DEFAULT 0.00000000
                            COMMENT 'Shares actuales en cartera',
    costo_base              DECIMAL(18,6)   NOT NULL DEFAULT 0.000000
                            COMMENT 'Precio promedio ponderado de compra',
    valor_mercado           DECIMAL(20,2)       NULL
                            COMMENT 'posicion_actual × precio_mercado',
    unrealized_pnl          DECIMAL(20,2)       NULL
                            COMMENT 'Ganancia/pérdida no realizada',
    daily_pnl               DECIMAL(20,2)       NULL
                            COMMENT 'Ganancia/pérdida del día',
    fecha_adquisicion       TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                            COMMENT 'Primera compra de este activo',
    ultima_actualizacion    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                            ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT pk_posicion      PRIMARY KEY (id_portafolio, id_activo),
    CONSTRAINT fk_posicion_port      FOREIGN KEY (id_portafolio)
        REFERENCES portafolio (id_portafolio)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_posicion_activo    FOREIGN KEY (id_activo)
        REFERENCES activo (id_activo)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Posición activa actual por portafolio y activo';


-- -------------------------------------------------------------
-- 7. SNAPSHOT_POSICION
-- Fotografía diaria de cada posición individual.
-- Permite responder: "¿cómo estaba mi AAPL hace 3 meses?"
-- UNIQUE (id_portafolio, id_activo, fecha_snapshot):
-- un snapshot por activo por portafolio por día.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS snapshot_posicion (
    id_snapshot         INT             NOT NULL AUTO_INCREMENT,
    id_portafolio       INT             NOT NULL,
    id_activo           INT             NOT NULL,
    fecha_snapshot      DATE            NOT NULL,
    posicion_actual     DECIMAL(18,8)   NOT NULL COMMENT 'Shares en esa fecha',
    precio_cierre       DECIMAL(18,6)   NOT NULL COMMENT 'Precio de cierre',
    costo_base          DECIMAL(18,6)   NOT NULL COMMENT 'Costo promedio en esa fecha',
    valor_mercado       DECIMAL(20,2)   NOT NULL COMMENT 'Valor de la posición',
    unrealized_pnl      DECIMAL(20,2)   NOT NULL COMMENT 'P&L no realizado',
    change_pct          DECIMAL(8,4)       NULL COMMENT 'Variación % del día',

    CONSTRAINT pk_snapshot          PRIMARY KEY (id_snapshot),
    CONSTRAINT fk_snapshotposi_port      FOREIGN KEY (id_portafolio)
        REFERENCES portafolio (id_portafolio)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_snapshotposi_act       FOREIGN KEY (id_activo)
        REFERENCES activo (id_activo)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT uq_snapshotposi_fecha    UNIQUE (id_portafolio, id_activo, fecha_snapshot),

    INDEX idx_snapshotposi_fecha (fecha_snapshot)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Histórico diario del estado de cada posición individual';


-- -------------------------------------------------------------
-- 8. MARKET_METRICS  ← actualización DIARIA
-- Métricas de valuación dependientes del precio de mercado.
-- Una fila por activo por fecha — NUNCA se sobreescribe,
-- siempre se inserta. Así no se pierde el histórico.
-- Origen: Yahoo Finance precio en tiempo real.
-- UNIQUE (id_activo, fecha): una métrica por día por activo.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS metricas_mercado (
    id_metricas           INT             NOT NULL AUTO_INCREMENT,
    id_activo           INT             NOT NULL,
    fecha               DATE            NOT NULL,
    precio              DECIMAL(18,6)       NULL COMMENT 'Precio de cierre',
    market_cap          BIGINT              NULL COMMENT 'Capitalización en USD',
    enterprise_value    BIGINT              NULL COMMENT 'EV = market cap + deuda - caja',
    pe_ratio            DECIMAL(10,2)       NULL COMMENT 'Price to Earnings (trailing)',
    pe_forward          DECIMAL(10,2)       NULL COMMENT 'P/E forward (estimado)',
    beta                DECIMAL(5,2)        NULL COMMENT 'Volatilidad relativa al mercado',
    dividend_yield      DECIMAL(8,4)        NULL COMMENT 'Rendimiento por dividendos %',

    CONSTRAINT pk_metricas_mercado    PRIMARY KEY (id_metricas),
    CONSTRAINT fk_metricasmercado_activo       FOREIGN KEY (id_activo)
        REFERENCES activo (id_activo)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT uq_metricasmercado_fecha        UNIQUE (id_activo, fecha),

    INDEX idx_metricas_mercado_fecha (fecha)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Métricas de valuación diarias por activo (dependen del precio)';

-- -------------------------------------------------------------
-- 9. HISTORICO
-- Serie temporal OHLCV de precios por activo.
-- PK compuesta (id_activo, fecha): un precio por día.
-- Diferente de MARKET_METRICS: este es el precio histórico
-- puro para velas y retornos históricos.
-- ON DELETE CASCADE: se elimina con el activo.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS historico (
    id_activo   INT             NOT NULL,
    fecha       DATE            NOT NULL,
    open_price  DECIMAL(18,6)       NULL,
    high_price  DECIMAL(18,6)       NULL,
    low_price   DECIMAL(18,6)       NULL,
    close_price DECIMAL(18,6)   NOT NULL,
    volumen     BIGINT              NULL,

    CONSTRAINT pk_historico     PRIMARY KEY (id_activo, fecha),
    CONSTRAINT fk_hist_activo   FOREIGN KEY (id_activo)
        REFERENCES activo (id_activo)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    INDEX idx_hist_fecha (fecha)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Precios históricos OHLCV por activo';


-- -------------------------------------------------------------
-- 10. EQUITY  — subtipo ISA de ACTIVO
-- Solo existe si activo.tipo_activo = 'EQUITY'.
-- Guarda campos estáticos o de baja frecuencia específicos
-- de acciones: sector, industria, próxima earnings date.
-- Los ratios y precios viven en sus propias tablas.
-- ON DELETE CASCADE: se elimina con su activo padre.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS equity (
	id_equity 		INT				NOT NULL AUTO_INCREMENT,
    id_activo       INT             NOT NULL,
    sector          VARCHAR(100)        NULL,
    industria       VARCHAR(150)        NULL,
    earnings_date   DATE                NULL
                    COMMENT 'Próxima fecha de reporte de resultados',

    CONSTRAINT pk_equity        PRIMARY KEY (id_equity, id_activo),
    CONSTRAINT fk_equity_activo     FOREIGN KEY (id_activo)
        REFERENCES activo (id_activo)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Datos estáticos de acciones — subtipo ISA de ACTIVO';


-- -------------------------------------------------------------
-- 11. BOND  — subtipo ISA de ACTIVO
-- Solo existe si activo.tipo_activo = 'BOND'.
-- Datos específicos de instrumentos de renta fija.
-- ON DELETE CASCADE: se elimina con su activo padre.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bond (
    id_bond				INT				NOT NULL AUTO_INCREMENT,
    id_activo           INT             NOT NULL,
    fecha_maduracion    DATE                NULL COMMENT 'Fecha de vencimiento',
    tasa_cupon          DECIMAL(8,4)        NULL COMMENT 'Tasa anual del cupón',
    frecuencia_pago     ENUM(
                            'MENSUAL',
                            'TRIMESTRAL',
                            'SEMESTRAL',
                            'ANUAL'
                        )                   NULL,
    valor_nominal       DECIMAL(20,2)       NULL COMMENT 'Valor par del bono',
    calificacion        VARCHAR(20)         NULL COMMENT 'AAA, AA+, BBB-...',
    emisor              ENUM(
                            'SOBERANO',
                            'CORPORATIVO'
                        )               NOT NULL,

    CONSTRAINT pk_bond          PRIMARY KEY (id_bond, id_activo),
    CONSTRAINT fk_bond_activo   FOREIGN KEY (id_activo)
        REFERENCES activo (id_activo)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Datos específicos de bonos — subtipo ISA de ACTIVO';
  
  SET FOREIGN_KEY_CHECKS = 1; 
  
  
-- ======================================================================
--							CREATE FUNCTIONS
-- ======================================================================

DELIMITER $$

/*==========================================================
  FUNCIÓN 1
  Calcula el valor total actual del portafolio
==========================================================*/
CREATE FUNCTION fn_total_value(p_id_portafolio INT)
RETURNS DECIMAL(20,2)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_cash DECIMAL(20,2);
    DECLARE v_total_posiciones DECIMAL(20,2);

    SELECT cash
    INTO v_cash
    FROM portafolio
    WHERE id_portafolio = p_id_portafolio;

    SELECT IFNULL(SUM(valor_mercado),0)
    INTO v_total_posiciones
    FROM posicion
    WHERE id_portafolio = p_id_portafolio;

    RETURN IFNULL(v_cash,0) + IFNULL(v_total_posiciones,0);
END$$


/*==========================================================
  FUNCIÓN 2
  Calcula la ganancia/pérdida no realizada del portafolio
==========================================================*/
CREATE FUNCTION fn_unrealized_pnl(p_id_portafolio INT)
RETURNS DECIMAL(20,2)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_resultado DECIMAL(20,2);

    SELECT IFNULL(
        SUM(
            (mm.precio - p.costo_base)
            * p.posicion_actual
        ),
    0)
    INTO v_resultado
    FROM posicion p
    INNER JOIN metricas_mercado mm
        ON p.id_activo = mm.id_activo
    WHERE p.id_portafolio = p_id_portafolio
      AND mm.fecha = (
            SELECT MAX(m2.fecha)
            FROM metricas_mercado m2
            WHERE m2.id_activo = mm.id_activo
      );

    RETURN IFNULL(v_resultado,0);
END$$

DELIMITER ;


-- ======================================================================
--							CREATE TRIGGERS
-- ======================================================================

-- TRIGGERS
-- trigger 1: 
DELIMITER $$
CREATE TRIGGER verificar_equity
BEFORE INSERT ON equity
FOR EACH ROW
BEGIN
    DECLARE n_tipo VARCHAR(15);
    SELECT tipo_activo
    INTO n_tipo
    FROM activo
    WHERE id_activo = NEW.id_activo;

    IF n_tipo <> 'EQUITY' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error: el activo no es tipo equity';
    END IF;
END$$
DELIMITER ;

-- TRIGGERS
-- trigger 2: 
DELIMITER $$
CREATE TRIGGER verificar_bond
BEFORE INSERT ON bond
FOR EACH ROW
BEGIN
    DECLARE n_tipo VARCHAR(15);
    SELECT tipo_activo
    INTO n_tipo
    FROM activo
    WHERE id_activo = NEW.id_activo;

    IF n_tipo <> 'BOND' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error: el activo no es tipo bond';
    END IF;
END$$
DELIMITER ;

-- Trigger 3:
DELIMITER $$
CREATE TRIGGER verificar_limite_movimiento
BEFORE INSERT ON movimiento
FOR EACH ROW
BEGIN
    IF NEW.cantidad <= 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'La cantidad del movimiento debe ser mayor que cero';
    END IF;
END$$
DELIMITER ;


-- ======================================================================
--							CREATE PROCEDURES
-- ======================================================================

DELIMITER $$


CREATE PROCEDURE p_total_portafolio_holdings(
    IN p_portfolio_id INT
)
BEGIN
    SELECT
        a.ticker,
        p.posicion_actual   AS shares,
        p.costo_base        AS avg_cost,
        p.valor_mercado,
        p.unrealized_pnl
    FROM posicion p
    JOIN activo a ON p.id_activo = a.id_activo
    WHERE p.id_portafolio = p_portfolio_id;
END$$


CREATE PROCEDURE p_ajuste_cash(
    IN p_portfolio_id INT,
    IN p_amount DECIMAL(20,2)    -- valor positivo para depósito, negativo para retiro
)
BEGIN
    DECLARE v_cash_actual DECIMAL(20,2);

    START TRANSACTION;

    SELECT cash INTO v_cash_actual
    FROM portafolio
    WHERE id_portafolio = p_portfolio_id
    FOR UPDATE;

    SET v_cash_actual = v_cash_actual + p_amount;

    IF v_cash_actual < 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Operación rechazada: saldo de efectivo insuficiente.';
    END IF;

    UPDATE portafolio
    SET cash = v_cash_actual
    WHERE id_portafolio = p_portfolio_id;

    COMMIT;
END$$


CREATE PROCEDURE p_calcular_daily_pnl(
    IN p_portfolio_id INT,
    IN p_date DATE                -- fecha para la cual se quiere el cálculo
)
BEGIN
    DECLARE v_prev_date DATE;
    DECLARE v_prev_price DECIMAL(18,6);
    DECLARE v_actu_price DECIMAL(18,6);
    DECLARE v_shares      DECIMAL(18,8);
    DECLARE v_avg_cost    DECIMAL(20,6);
    DECLARE v_daily_pnl   DECIMAL(20,2);
    DECLARE v_id_activo   INT;
    DECLARE done INT DEFAULT 0;

    -- Obtener la fecha anterior disponible en metricas_mercado
    SELECT MAX(fecha) INTO v_prev_date
    FROM metricas_mercado
    WHERE fecha < p_date;

    IF v_prev_date IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'No hay datos de precios anteriores para calcular P&L.';
    END IF;

    -- Recorrer cada posición del portafolio y calcular el P&L diario
    BEGIN
        DECLARE cur CURSOR FOR
            SELECT p.id_activo, p.posicion_actual, p.costo_base
            FROM posicion p
            WHERE p.id_portafolio = p_portfolio_id;

        DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

        OPEN cur;
        read_loop: LOOP
            FETCH cur INTO v_id_activo, v_shares, v_avg_cost;
            IF done THEN LEAVE read_loop; END IF;

            -- Precio anterior
            SELECT precio INTO v_prev_price
            FROM metricas_mercado
            WHERE id_activo = v_id_activo AND fecha = v_prev_date
            LIMIT 1;

            -- Precio actual (fecha p_date)
            SELECT precio INTO v_actu_price
            FROM metricas_mercado
            WHERE id_activo = v_id_activo AND fecha = p_date
            LIMIT 1;

            IF v_prev_price IS NULL OR v_actu_price IS NULL THEN
                SET v_daily_pnl = NULL;
            ELSE
                SET v_daily_pnl = (v_actu_price - v_prev_price) * v_shares;
            END IF;

            -- Actualizar la columna daily_pnl en la tabla posición
            UPDATE posicion
            SET daily_pnl = v_daily_pnl,
                ultima_actualizacion = CURRENT_TIMESTAMP
            WHERE id_portafolio = p_portfolio_id
              AND id_activo = v_id_activo;
        END LOOP;
        CLOSE cur;
    END;
END$$


CREATE PROCEDURE p_realizar_transaccion(
    IN p_portfolio_id INT,
    IN p_ticker        VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    IN p_type          ENUM('BUY','SELL'),
    IN p_shares        DECIMAL(18,8),
    IN p_price         DECIMAL(18,6),
    IN p_date          DATETIME
)
BEGIN
    DECLARE v_cash_balance   DECIMAL(20,2);
    DECLARE v_new_cash       DECIMAL(20,2);
    DECLARE v_id_activo      INT;
    DECLARE v_available_shares DECIMAL(18,8);
    START TRANSACTION;
    -- Busca el id del activo una sola vez, se utilizara mas adelante.
    SELECT id_activo INTO v_id_activo
    FROM activo
    WHERE ticker = p_ticker
    FOR UPDATE;
    IF v_id_activo IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Ticker not found in activo table.';
    END IF;
    -- Bloquea la fila del portafolio para actualizar el efectivo de forma segura.
    SELECT cash INTO v_cash_balance
    FROM portafolio
    WHERE id_portafolio = p_portfolio_id
    FOR UPDATE;
    IF p_type = 'BUY' THEN
        SET v_new_cash = v_cash_balance - (p_shares * p_price);
        IF v_new_cash < 0 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Insufficient cash to perform BUY.';
        END IF;
        UPDATE portafolio SET cash = v_new_cash
        WHERE id_portafolio = p_portfolio_id;
    ELSEIF p_type = 'SELL' THEN
        SELECT posicion_actual INTO v_available_shares
        FROM posicion
        WHERE id_portafolio = p_portfolio_id AND id_activo = v_id_activo
        FOR UPDATE;
        IF v_available_shares IS NULL OR v_available_shares < p_shares THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Insufficient shares to perform SELL.';
        END IF;
        SET v_new_cash = v_cash_balance + (p_shares * p_price);
        UPDATE portafolio SET cash = v_new_cash
        WHERE id_portafolio = p_portfolio_id;
    END IF;
    -- Inserta el registro de transacción inmutable.
    INSERT INTO movimiento (
        id_portafolio,
        id_activo,
        tipo_mov,
        cantidad,
        precio_por_accion,
        fee,
        notas,
        fecha_transaccion
    ) VALUES (
        p_portfolio_id,
        v_id_activo,
        p_type,
        p_shares,
        p_price,
        0.0,
        NULL,
        p_date
    );
    COMMIT;
END$$



CREATE PROCEDURE p_procesar_snapshots_diarios(
    IN p_fecha_snapshot DATE
)
BEGIN
    -- Declaración de variables para el cursor explícito
    DECLARE v_id_portafolio    INT;
    DECLARE v_id_activo        INT;
    DECLARE v_posicion_actual DECIMAL(18,8);
    DECLARE v_costo_base       DECIMAL(18,6);
    DECLARE v_precio_cierre    DECIMAL(18,6);
    DECLARE v_valor_mercado    DECIMAL(20,2);
    DECLARE v_unrealized_pnl  DECIMAL(20,2);
    
    -- Control de fin de cursor
    DECLARE v_done INT DEFAULT 0;

    -- CURSOR EXPLÍCITO para recorrer todas las posiciones activas (shares > 0)
    DECLARE cur_posiciones CURSOR FOR
        SELECT id_portafolio, id_activo, posicion_actual, costo_base
        FROM posicion
        WHERE posicion_actual > 0;

    -- Manejador de excepción para el fin de filas en el cursor
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = 1;

    OPEN cur_posiciones;

    read_loop: LOOP
        FETCH cur_posiciones INTO v_id_portafolio, v_id_activo, v_posicion_actual, v_costo_base;
        IF v_done THEN
            LEAVE read_loop;
        END IF;

        -- Bloque anidado para manejar excepciones por cada registro procesado
        BEGIN
            -- Manejador de excepciones inesperadas/previsibles (SQLEXCEPTION) para esta iteración
            DECLARE CONTINUE HANDLER FOR SQLEXCEPTION
            BEGIN
                -- En caso de error (ej. precio no encontrado o violacion de constraint), se captura para no romper el ciclo
                -- Opcional: Registrar error en un log o simplemente omitir el snapshot defectuoso
            END;

            -- 1. Obtener precio de cierre más reciente a la fecha del snapshot
            SELECT precio INTO v_precio_cierre
            FROM metricas_mercado
            WHERE id_activo = v_id_activo AND fecha <= p_fecha_snapshot
            ORDER BY fecha DESC
            LIMIT 1;

            -- 2. Validar que exista un precio válido
            IF v_precio_cierre IS NOT NULL THEN
                SET v_valor_mercado  = v_posicion_actual * v_precio_cierre;
                SET v_unrealized_pnl = (v_precio_cierre - v_costo_base) * v_posicion_actual;

                -- 3. Insertar snapshot (ON DUPLICATE KEY UPDATE si ya fue ejecutado el mismo día)
                INSERT INTO snapshot_posicion (
                    id_portafolio,
                    id_activo,
                    fecha_snapshot,
                    posicion_actual,
                    precio_cierre,
                    costo_base,
                    valor_mercado,
                    unrealized_pnl
                ) VALUES (
                    v_id_portafolio,
                    v_id_activo,
                    p_fecha_snapshot,
                    v_posicion_actual,
                    v_precio_cierre,
                    v_costo_base,
                    v_valor_mercado,
                    v_unrealized_pnl
                )
                ON DUPLICATE KEY UPDATE
                    posicion_actual = VALUES(posicion_actual),
                    precio_cierre   = VALUES(precio_cierre),
                    costo_base      = VALUES(costo_base),
                    valor_mercado   = VALUES(valor_mercado),
                    unrealized_pnl  = VALUES(unrealized_pnl);
            END IF;
        END;

    END LOOP;

    CLOSE cur_posiciones;
END$$

DELIMITER ;
