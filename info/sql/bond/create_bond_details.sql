INSERT INTO bond (
    id_activo,
    id_bond,
    fecha_maduracion,
    tasa_cupon,
    frecuencia_pago,
    valor_nominal,
    calificacion,
    emisor
) VALUES (
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s
);