# -*- coding: utf-8 -*-
"""
Scraper BDNB - Base de Donnees Nationale des Batiments
Recupere les informations des batiments depuis l'API BDNB
https://bdnb.io
"""
import os
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

# URLs des APIs
BDNB_API_URL = "https://api.bdnb.io/v1/bdnb/donnees/batiment_groupe_complet"
RNB_API_URL = "https://rnb-api.beta.gouv.fr/api/alpha/buildings"

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dvf:dvf@localhost:5432/dvf")


def creer_session_http():
    """Cree une session HTTP avec retry automatique"""
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504, 429],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def creer_table_batiments(engine):
    """Cree la table batiments si elle n'existe pas"""
    with engine.connect() as conn:
        conn.execute(text("""
            DROP TABLE IF EXISTS batiments CASCADE;

            CREATE TABLE batiments (
                id SERIAL PRIMARY KEY,
                batiment_groupe_id TEXT UNIQUE,
                id_parcelle TEXT,
                annee_construction INTEGER,
                hauteur_mean NUMERIC,
                nb_logements INTEGER,
                classe_dpe TEXT,
                conso_energie_m2 NUMERIC,
                emission_ges_m2 NUMERIC,
                materiau_mur TEXT,
                materiau_toit TEXT,
                adresse TEXT,
                code_postal TEXT,
                commune TEXT,
                latitude NUMERIC,
                longitude NUMERIC,
                surface_facade NUMERIC,
                nb_etages INTEGER,
                chauffage_type TEXT,
                geom_json TEXT,
                scraped_at TIMESTAMPTZ DEFAULT NOW()
            );

            CREATE INDEX idx_batiments_parcelle ON batiments(id_parcelle);
            CREATE INDEX idx_batiments_dpe ON batiments(classe_dpe);
            CREATE INDEX idx_batiments_annee ON batiments(annee_construction);
        """))
        conn.commit()
    print("Table batiments creee")


def get_batiments_par_departement(code_dept="75", limit=1000, offset=0, session=None):
    """
    Recupere les batiments d'un departement depuis l'API BDNB
    """
    if session is None:
        session = creer_session_http()

    params = {
        "code_departement_insee": f"eq.{code_dept}",
        "limit": limit,
        "offset": offset,
        "select": ",".join([
            "batiment_groupe_id",
            "l_parcelle_id",
            "annee_construction",
            "hauteur_mean",
            "nb_log",
            "classe_bilan_dpe",
            "conso_5_usages_ep_m2",
            "emission_ges_5_usages_m2",
            "mat_mur_txt",
            "mat_toit_txt",
            "libelle_adr_principale_ban",
            "code_commune_insee",
            "libelle_commune_insee",
            "geom_groupe"
        ])
    }

    try:
        response = session.get(BDNB_API_URL, params=params, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erreur API BDNB: {e}")
        return []


def get_batiments_par_parcelle(id_parcelle, session=None):
    """
    Recupere les batiments d'une parcelle depuis l'API RNB
    """
    if session is None:
        session = creer_session_http()

    url = f"{RNB_API_URL}/plot/{id_parcelle}/"

    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])
    except requests.exceptions.RequestException as e:
        return []


def transformer_donnees_bdnb(batiments):
    """
    Transforme les donnees BDNB en format pour la base
    """
    records = []

    for bat in batiments:
        # Extraire le premier id_parcelle de la liste
        parcelles = bat.get("l_parcelle_id", [])
        id_parcelle = parcelles[0] if parcelles else None

        # Extraire les coordonnees du centroide
        geom = bat.get("geom_groupe")
        lat, lon = None, None
        if geom and geom.get("coordinates"):
            try:
                # MultiPolygon - calculer le centroide approximatif
                coords = geom["coordinates"][0][0]  # Premier anneau du premier polygone
                if coords:
                    lons = [c[0] for c in coords]
                    lats = [c[1] for c in coords]
                    # Convertir de Lambert 93 (EPSG:2154) vers WGS84 si necessaire
                    # Pour l'instant on garde les coords brutes
            except (IndexError, TypeError):
                pass

        record = {
            "batiment_groupe_id": bat.get("batiment_groupe_id"),
            "id_parcelle": id_parcelle,
            "annee_construction": bat.get("annee_construction"),
            "hauteur_mean": bat.get("hauteur_mean"),
            "nb_logements": bat.get("nb_log"),
            "classe_dpe": bat.get("classe_bilan_dpe"),
            "conso_energie_m2": bat.get("conso_5_usages_ep_m2"),
            "emission_ges_m2": bat.get("emission_ges_5_usages_m2"),
            "materiau_mur": bat.get("mat_mur_txt"),
            "materiau_toit": bat.get("mat_toit_txt"),
            "adresse": bat.get("libelle_adr_principale_ban"),
            "code_postal": str(bat.get("code_commune_insee", ""))[:5] if bat.get("code_commune_insee") else None,
            "commune": bat.get("libelle_commune_insee"),
            "geom_json": str(geom) if geom else None
        }
        records.append(record)

    return records


def scraper_bdnb_paris(limit_total=50000):
    """
    Scrape les batiments de Paris depuis l'API BDNB
    """
    print("=" * 60)
    print("Scraping BDNB - Base de Donnees Nationale des Batiments")
    print("=" * 60)

    engine = create_engine(DATABASE_URL)
    creer_table_batiments(engine)

    session = creer_session_http()

    all_records = []
    offset = 0
    batch_size = 1000

    while offset < limit_total:
        print(f"Recuperation batch {offset}-{offset+batch_size}...")

        batiments = get_batiments_par_departement(
            code_dept="75",
            limit=batch_size,
            offset=offset,
            session=session
        )

        if not batiments:
            print("Plus de donnees disponibles")
            break

        records = transformer_donnees_bdnb(batiments)
        all_records.extend(records)

        print(f"  -> {len(batiments)} batiments recuperes")

        offset += batch_size
        time.sleep(0.5)  # Rate limiting

    # Inserer en base
    if all_records:
        df = pd.DataFrame(all_records)
        print(f"\nInsertion de {len(df)} batiments en base...")

        df.to_sql(
            "batiments",
            engine,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=1000
        )

        print("Insertion terminee")

    # Stats
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM batiments"))
        count = result.scalar()

        result_dpe = conn.execute(text("""
            SELECT classe_dpe, COUNT(*) as n
            FROM batiments
            WHERE classe_dpe IS NOT NULL
            GROUP BY classe_dpe
            ORDER BY classe_dpe
        """))
        dpe_stats = result_dpe.fetchall()

    print(f"\n{'=' * 60}")
    print(f"Scraping termine: {count} batiments en base")
    print("\nRepartition DPE:")
    for classe, n in dpe_stats:
        print(f"  {classe}: {n}")
    print("=" * 60)


def enrichir_parcelles_avec_bdnb():
    """
    Enrichit la table parcelles avec les donnees BDNB
    """
    print("Enrichissement des parcelles avec donnees BDNB...")

    engine = create_engine(DATABASE_URL)

    # Ajouter colonnes si elles n'existent pas
    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE parcelles
            ADD COLUMN IF NOT EXISTS annee_construction INTEGER,
            ADD COLUMN IF NOT EXISTS classe_dpe TEXT,
            ADD COLUMN IF NOT EXISTS nb_logements INTEGER,
            ADD COLUMN IF NOT EXISTS hauteur_batiment NUMERIC,
            ADD COLUMN IF NOT EXISTS materiau_mur TEXT
        """))
        conn.commit()

        # Mettre a jour avec jointure
        result = conn.execute(text("""
            UPDATE parcelles p
            SET
                annee_construction = b.annee_construction,
                classe_dpe = b.classe_dpe,
                nb_logements = b.nb_logements,
                hauteur_batiment = b.hauteur_mean,
                materiau_mur = b.materiau_mur
            FROM batiments b
            WHERE p.id_parcelle = b.id_parcelle
        """))
        conn.commit()

        print(f"  -> {result.rowcount} parcelles enrichies")


def run():
    """Execute le scraping complet"""
    scraper_bdnb_paris(limit_total=50000)
    enrichir_parcelles_avec_bdnb()


if __name__ == "__main__":
    run()
