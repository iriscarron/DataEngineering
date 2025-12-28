CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    date_mutation DATE,
    valeur_fonciere NUMERIC,
    surface_reelle_bati NUMERIC,
    prix_m2 NUMERIC,
    type_local TEXT,
    code_postal TEXT,
    arrondissement TEXT,
    latitude NUMERIC,
    longitude NUMERIC,
    source_file TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date_mutation);
CREATE INDEX IF NOT EXISTS idx_transactions_cp ON transactions(code_postal);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type_local);
