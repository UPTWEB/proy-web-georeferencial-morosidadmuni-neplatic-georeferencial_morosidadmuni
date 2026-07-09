import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from src.models.database import SessionLocal

sql_script = """
SET search_path TO neplatic, public;

DO $$
DECLARE
    v_id_noti INT;
    v_id_ruta_hoy INT;
    v_id_ruta_manana INT;
    v_deuda RECORD;
    v_orden INT;
BEGIN
    -- 1. Obtener ID de notificador3
    SELECT id_usuario INTO v_id_noti
    FROM usuario
    WHERE username = 'notificador3'
    LIMIT 1;

    IF v_id_noti IS NULL THEN
        RAISE EXCEPTION 'El usuario notificador3 no existe.';
    END IF;

    -- Limpiar rutas existentes para hoy y manana para este notificador para evitar errores de clave unica
    DELETE FROM ruta_detalle WHERE id_ruta IN (
        SELECT id_ruta FROM ruta_notificacion WHERE id_usuario = v_id_noti AND fecha_ruta IN (CURRENT_DATE, CURRENT_DATE + INTERVAL '1 day')
    );
    DELETE FROM ruta_notificacion WHERE id_usuario = v_id_noti AND fecha_ruta IN (CURRENT_DATE, CURRENT_DATE + INTERVAL '1 day');

    -- 2. Crear ruta para HOY
    INSERT INTO ruta_notificacion (id_usuario, fecha_ruta, estado_ruta, total_deudas, deudas_atendidas, distancia_estimada_km)
    VALUES (v_id_noti, CURRENT_DATE, 'PLANIFICADA', 5, 0, 2.5)
    RETURNING id_ruta INTO v_id_ruta_hoy;

    -- Asignar 5 deudas aleatorias para HOY (asegurando que el lote tenga coordenadas para probar el mapa)
    v_orden := 1;
    FOR v_deuda IN (
        SELECT d.id_deuda 
        FROM deuda d
        JOIN lote l ON d.id_lote = l.id_lote
        WHERE l.latitud IS NOT NULL AND l.longitud IS NOT NULL
        ORDER BY RANDOM() LIMIT 5
    ) LOOP
        INSERT INTO ruta_detalle (id_ruta, id_deuda, orden_visita, visitado)
        VALUES (v_id_ruta_hoy, v_deuda.id_deuda, v_orden, false);
        v_orden := v_orden + 1;
    END LOOP;

    -- Actualizar total real asignado hoy
    UPDATE ruta_notificacion SET total_deudas = v_orden - 1 WHERE id_ruta = v_id_ruta_hoy;

    -- 3. Crear ruta para MAÑANA
    INSERT INTO ruta_notificacion (id_usuario, fecha_ruta, estado_ruta, total_deudas, deudas_atendidas, distancia_estimada_km)
    VALUES (v_id_noti, CURRENT_DATE + INTERVAL '1 day', 'PLANIFICADA', 5, 0, 3.1)
    RETURNING id_ruta INTO v_id_ruta_manana;

    -- Asignar otras 5 deudas aleatorias para MAÑANA (con coordenadas)
    v_orden := 1;
    FOR v_deuda IN (
        SELECT d.id_deuda 
        FROM deuda d
        JOIN lote l ON d.id_lote = l.id_lote
        WHERE l.latitud IS NOT NULL AND l.longitud IS NOT NULL
        AND d.id_deuda NOT IN (SELECT id_deuda FROM ruta_detalle WHERE id_ruta = v_id_ruta_hoy)
        ORDER BY RANDOM() LIMIT 5
    ) LOOP
        INSERT INTO ruta_detalle (id_ruta, id_deuda, orden_visita, visitado)
        VALUES (v_id_ruta_manana, v_deuda.id_deuda, v_orden, false);
        v_orden := v_orden + 1;
    END LOOP;

    -- Actualizar total real asignado mañana
    UPDATE ruta_notificacion SET total_deudas = v_orden - 1 WHERE id_ruta = v_id_ruta_manana;

    RAISE NOTICE '¡Éxito! Rutas asignadas para hoy y mañana a notificador3 (aprox 5 deudas c/u).';
END $$;
"""

def run():
    db = SessionLocal()
    try:
        db.execute(text(sql_script))
        db.commit()
        print("Script ejecutado correctamente.")
    except Exception as e:
        db.rollback()
        print(f"Error al ejecutar el script: {e}")
    finally:
        db.close()

if __name__ == '__main__':
    run()
