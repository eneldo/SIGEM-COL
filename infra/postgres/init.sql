-- SIGEM Colombia - Inicialización de PostgreSQL

-- Habilitar extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Función para generar UUIDv7 (aproximación)
CREATE OR REPLACE FUNCTION generate_uuid_v7()
RETURNS UUID AS $$
DECLARE
    timestamp_ms BIGINT;
    random_bytes BYTEA;
BEGIN
    -- Obtener timestamp en milisegundos
    timestamp_ms := EXTRACT(EPOCH FROM clock_timestamp()) * 1000;
    
    -- Generar bytes aleatorios
    random_bytes := gen_random_bytes(10);
    
    -- Construir UUID v7 (aproximación)
    -- Primeros 8 bytes: timestamp
    -- Siguientes 6 bytes: aleatorios
    RETURN encode(
        substring(
            int8send(timestamp_ms) from 3 for 6
        ) || substring(random_bytes from 1 for 6),
        'hex'
    )::UUID;
END;
$$ LANGUAGE plpgsql;

-- Configurar zona horaria
SET timezone = 'America/Bogota';

-- Crear esquema si es necesario
CREATE SCHEMA IF NOT EXISTS sigem;

-- Mensaje de éxito
DO $$
BEGIN
    RAISE NOTICE 'SIGEM Colombia - Base de datos inicializada correctamente';
END $$;
