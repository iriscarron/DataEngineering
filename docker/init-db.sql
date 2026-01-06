-- Schema de base de donnees pour DVF+ Paris
-- Extension PostGIS pour les donnees geographiques
CREATE EXTENSION IF NOT EXISTS postgis;

-- Table principale des transactions immobilieres
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    id_mutation TEXT,
    date_mutation DATE,
    nature_mutation TEXT,
    valeur_fonciere NUMERIC,
    surface_reelle_bati NUMERIC,
    surface_terrain NUMERIC,
    prix_m2 NUMERIC,
    nb_pieces INTEGER,
    type_local TEXT,
    code_postal TEXT,
    code_insee TEXT,
    arrondissement TEXT,
    latitude NUMERIC,
    longitude NUMERIC,
    vefa BOOLEAN DEFAULT FALSE,
    scraped_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index pour accelerer les requetes
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date_mutation);
CREATE INDEX IF NOT EXISTS idx_transactions_arrondissement ON transactions(arrondissement);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type_local);
CREATE INDEX IF NOT EXISTS idx_transactions_nature ON transactions(nature_mutation);
CREATE INDEX IF NOT EXISTS idx_transactions_prix ON transactions(valeur_fonciere);
