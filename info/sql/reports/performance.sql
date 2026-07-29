-- Resumen de performance, reutilizando fn_total_value y fn_unrealized_pnl
-- que ya existen en el schema.
-- Parametros (el mismo id_portafolio dos veces): id_portafolio, id_portafolio
SELECT
    fn_total_value(%s) AS valor_total,
    fn_unrealized_pnl(%s) AS ganancia_no_realizada;
