"""
Scraper DVF+ pour Paris
Recupere les donnees de transactions immobilieres depuis l'API DVF+ du Cerema
"""
import os
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

# URL de base de l'API DVF+
API_BASE_URL = "https://apidf-preprod.cerema.fr/dvf_opendata/mutations/"


def creer_session_http():
    """Cree une session HTTP avec retry automatique"""
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

# Codes INSEE des 20 arrondissements de Paris
PARIS_INSEE_CODES = [f"751{str(i).zfill(2)}" for i in range(1, 21)]

# Connexion base de donnees
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dvf:dvf@localhost:5432/dvf")


def get_mutations_commune(code_insee, annee_min="2020", annee_max="2024", session=None):
    """
    Recupere les mutations pour une commune depuis l'API DVF+
    """
    if session is None:
        session = creer_session_http()

    resultats = []
    page = 1
    page_size = 500
    max_retries = 3

    while True:
        params = {
            "code_insee": code_insee,
            "anneemut_min": annee_min,
            "anneemut_max": annee_max,
            "page": page,
            "page_size": page_size,
        }

        for attempt in range(max_retries):
            try:
                response = session.get(API_BASE_URL, params=params, timeout=60)
                response.raise_for_status()
                data = response.json()

                results = data.get("results", [])
                if not results:
                    return resultats

                resultats.extend(results)
                print(f"  Page {page}: {len(results)} mutations pour {code_insee}")

                if not data.get("next"):
                    return resultats

                page += 1
                time.sleep(0.5)
                break

            except requests.exceptions.RequestException as e:
                print(f"  Tentative {attempt+1}/{max_retries} echouee pour {code_insee}: {type(e).__name__}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    print(f"  Abandon pour {code_insee} apres {max_retries} tentatives")
                    return resultats

    return resultats


def scrape_paris(annee_min="2020", annee_max="2024"):
    """
    Scrape les donnees DVF pour tous les arrondissements de Paris
    """
    toutes_mutations = []
    session = creer_session_http()

    print(f"Debut du scraping pour Paris ({len(PARIS_INSEE_CODES)} arrondissements)")
    print(f"Periode: {annee_min} - {annee_max}")
    print("-" * 50)

    for i, code_insee in enumerate(PARIS_INSEE_CODES, 1):
        arr_num = int(code_insee[-2:])
        print(f"[{i}/20] Arrondissement {arr_num} ({code_insee})...")

        mutations = get_mutations_commune(code_insee, annee_min, annee_max, session)
        toutes_mutations.extend(mutations)

        time.sleep(1)

    print("-" * 50)
    print(f"Total mutations: {len(toutes_mutations)}")

    if not toutes_mutations:
        return pd.DataFrame()

    df = pd.DataFrame(toutes_mutations)
    return df


def transformer_donnees(df):
    """
    Transforme les donnees brutes de l'API vers notre schema de BDD
    """
    if df.empty:
        return df

    transformed = pd.DataFrame()

    # Date de mutation
    if "datemut" in df.columns:
        transformed["date_mutation"] = pd.to_datetime(df["datemut"], errors="coerce")

    # Valeur fonciere
    if "valeurfonc" in df.columns:
        transformed["valeur_fonciere"] = pd.to_numeric(df["valeurfonc"], errors="coerce")

    # Surface batie
    if "sbati" in df.columns:
        transformed["surface_reelle_bati"] = pd.to_numeric(df["sbati"], errors="coerce")

    # Surface terrain
    if "sterr" in df.columns:
        transformed["surface_terrain"] = pd.to_numeric(df["sterr"], errors="coerce")

    # Calcul prix au m2
    transformed["prix_m2"] = (
        transformed["valeur_fonciere"] / transformed["surface_reelle_bati"]
    ).replace([float("inf"), float("-inf")], None)

    # Type de bien
    if "libtypbien" in df.columns:
        transformed["type_local"] = df["libtypbien"]
    elif "codtypbien" in df.columns:
        type_mapping = {
            "111": "Maison",
            "121": "Appartement",
            "10": "Local industriel",
            "20": "Local commercial",
            "30": "Local activite",
        }
        transformed["type_local"] = df["codtypbien"].astype(str).map(type_mapping).fillna("Autre")

    # Nature de la mutation (type de vente)
    if "libnatmut" in df.columns:
        transformed["nature_mutation"] = df["libnatmut"]

    # Code INSEE et arrondissement
    if "l_codinsee" in df.columns:
        transformed["code_insee"] = df["l_codinsee"].apply(
            lambda x: x[0] if isinstance(x, list) and len(x) > 0 else str(x)
        )
        transformed["arrondissement"] = transformed["code_insee"].apply(
            lambda x: str(int(str(x)[-2:])) if pd.notna(x) and len(str(x)) >= 2 else None
        )

    # Code postal
    if "l_codinsee" in df.columns:
        transformed["code_postal"] = transformed["code_insee"].apply(
            lambda x: f"750{str(x)[-2:]}" if pd.notna(x) else None
        )

    # Coordonnees GPS
    if "latitude" in df.columns:
        transformed["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    if "longitude" in df.columns:
        transformed["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    # ID mutation
    if "idmutation" in df.columns:
        transformed["id_mutation"] = df["idmutation"]

    # Nombre de pieces
    if "nbpiece" in df.columns:
        transformed["nb_pieces"] = pd.to_numeric(df["nbpiece"], errors="coerce")

    # VEFA (vente en etat futur d'achevement)
    if "vefa" in df.columns:
        transformed["vefa"] = df["vefa"].astype(bool) if df["vefa"].notna().any() else False

    # Metadonnees
    transformed["scraped_at"] = datetime.now()

    # Supprimer les lignes sans donnees essentielles
    transformed = transformed.dropna(subset=["valeur_fonciere", "date_mutation"])

    return transformed


def charger_en_bdd(df, table_name="transactions"):
    """
    Charge les donnees transformees dans PostgreSQL
    """
    if df.empty:
        print("Pas de donnees a charger.")
        return

    engine = create_engine(DATABASE_URL)

    df.to_sql(
        table_name,
        engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000
    )

    print(f"Charge {len(df)} enregistrements dans {table_name}")


def vider_table(table_name="transactions"):
    """Vide la table existante"""
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        conn.execute(text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY"))
        conn.commit()
    print(f"Table {table_name} videe")


def run_scraper(annee_min="2020", annee_max="2024", vider_avant=True):
    """
    Fonction principale pour executer le pipeline ETL complet
    """
    print("=" * 60)
    print("DVF+ Paris Scraper")
    print("=" * 60)

    # Etape 1: Scraper les donnees
    print("\n[1/3] Scraping depuis l'API DVF+...")
    raw_df = scrape_paris(annee_min, annee_max)

    if raw_df.empty:
        print("Aucune donnee recuperee.")
        return

    # Etape 2: Transformer les donnees
    print("\n[2/3] Transformation des donnees...")
    transformed_df = transformer_donnees(raw_df)
    print(f"{len(transformed_df)} enregistrements valides")

    # Etape 3: Charger en BDD
    print("\n[3/3] Chargement en base de donnees...")
    if vider_avant:
        vider_table()
    charger_en_bdd(transformed_df)

    print("\n" + "=" * 60)
    print("Scraping termine!")
    print("=" * 60)

    return transformed_df


if __name__ == "__main__":
    run_scraper(annee_min="2020", annee_max="2024")
