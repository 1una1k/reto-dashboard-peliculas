-- Ejecutar conectado a la base guests. No elimina datos existentes.
CREATE TABLE IF NOT EXISTS public.people (
    email VARCHAR(254) NOT NULL CHECK (length(btrim(email)) > 0),
    comment TEXT NOT NULL CHECK (length(btrim(comment)) BETWEEN 1 AND 2000)
);
