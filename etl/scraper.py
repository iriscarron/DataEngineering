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
API_GEOMUTATIONS_URL = "https://apidf-preprod.cerema.fr/dvf_opendata/geomutations/"

# Coordonnees approximatives des arrondissements de Paris (centre)
COORDS_ARRONDISSEMENTS = {
    "1": (48.8600, 2.3470), "2": (48.8680, 2.3410), "3": (48.8650, 2.3610),
    "4": (48.8540, 2.3570), "5": (48.8460, 2.3500), "6": (48.8490, 2.3340),
    "7": (48.8560, 2.3150), "8": (48.8740, 2.3110), "9": (48.8770, 2.3370),
    "10": (48.8760, 2.3590), "11": (48.8600, 2.3790), "12": (48.8400, 2.3880),
    "13": (48.8310, 2.3550), "14": (48.8330, 2.3270), "15": (48.8420, 2.2990),
    "16": (48.8630, 2.2760), "17": (48.8870, 2.3030), "18": (48.8920, 2.3440),
    "19": (48.8820, 2.3820), "20": (48.8640, 2.3980),
}


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
                time.sleep(0.1)
                break

            except requests.exceptions.RequestException as e:
                print(f"  Tentative {attempt+1}/{max_retries} echouee pour {code_insee}: {type(e).__name__}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    print(f"  Abandon pour {code_insee} apres {max_retries} tentatives")
                    return resultats

    return resultats


def get_geomutations_commune(code_insee, annee_min="2020", annee_max="2024", session=None):
    """
    Recupere les mutations avec geometrie des parcelles depuis l'API DVF+ geomutations
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
                response = session.get(API_GEOMUTATIONS_URL, params=params, timeout=90)
                response.raise_for_status()
                data = response.json()

                features = data.get("features", [])
                if not features:
                    return resultats

                resultats.extend(features)
                print(f"  Page {page}: {len(features)} parcelles pour {code_insee}")

                if not data.get("next"):
                    return resultats

                page += 1
                time.sleep(0.15)
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

        time.sleep(0.2)

    print("-" * 50)
    print(f"Total mutations: {len(toutes_mutations)}")

    if not toutes_mutations:
        return pd.DataFrame()

    df = pd.DataFrame(toutes_mutations)
    return df


def scrape_paris_geo(annee_min="2020", annee_max="2024"):
    """
    Scrape les donnees DVF avec geometries des parcelles pour Paris
    """
    toutes_features = []
    session = creer_session_http()

    print(f"Debut du scraping GEOMUTATIONS pour Paris ({len(PARIS_INSEE_CODES)} arrondissements)")
    print(f"Periode: {annee_min} - {annee_max}")
    print("-" * 50)

    for i, code_insee in enumerate(PARIS_INSEE_CODES, 1):
        arr_num = int(code_insee[-2:])
        print(f"[{i}/20] Arrondissement {arr_num} ({code_insee})...")

        features = get_geomutations_commune(code_insee, annee_min, annee_max, session)
        toutes_features.extend(features)

        time.sleep(0.3)

    print("-" * 50)
    print(f"Total parcelles avec geometrie: {len(toutes_features)}")

    return toutes_features


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

    # Coordonnees GPS (basees sur l'arrondissement avec decalage aleatoire)
    import random
    def get_coords_arr(arr):
        if arr and str(arr) in COORDS_ARRONDISSEMENTS:
            lat, lon = COORDS_ARRONDISSEMENTS[str(arr)]
            # Ajouter un decalage aleatoire (environ 500m)
            lat += random.uniform(-0.004, 0.004)
            lon += random.uniform(-0.005, 0.005)
            return lat, lon
        return None, None

    if "arrondissement" in transformed.columns:
        coords = transformed["arrondissement"].apply(get_coords_arr)
        transformed["latitude"] = coords.apply(lambda x: x[0])
        transformed["longitude"] = coords.apply(lambda x: x[1])

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


def transformer_donnees_geo(features):
    """
    Transforme les features GeoJSON de l'API geomutations vers notre schema
    """
    import json

    if not features:
        return pd.DataFrame()

    records = []
    for feature in features:
        props = feature.get("properties", {})
        geom = feature.get("geometry", {})

        # Calculer le centroid pour latitude/longitude
        coords = geom.get("coordinates", [[]])
        if geom.get("type") == "Polygon" and coords and coords[0]:
            # Centroid approximatif du polygone
            all_coords = coords[0]
            if all_coords:
                lat = sum(c[1] for c in all_coords) / len(all_coords)
                lon = sum(c[0] for c in all_coords) / len(all_coords)
            else:
                lat, lon = None, None
        elif geom.get("type") == "MultiPolygon" and coords:
            # Centroid du premier polygone
            first_poly = coords[0][0] if coords[0] else []
            if first_poly:
                lat = sum(c[1] for c in first_poly) / len(first_poly)
                lon = sum(c[0] for c in first_poly) / len(first_poly)
            else:
                lat, lon = None, None
        else:
            lat, lon = None, None

        # Extraire l'arrondissement du code INSEE
        code_insee = props.get("l_codinsee", [""])[0] if isinstance(props.get("l_codinsee"), list) else str(props.get("l_codinsee", ""))
        if code_insee and len(code_insee) >= 2:
            arrondissement = str(int(code_insee[-2:]))
            code_postal = f"750{code_insee[-2:]}"
        else:
            arrondissement = None
            code_postal = None

        # Calculer le prix au m2
        valeur = props.get("valeurfonc")
        surface = props.get("sbati")
        if valeur and surface and float(surface) > 0:
            prix_m2 = float(valeur) / float(surface)
        else:
            prix_m2 = None

        record = {
            "id_mutation": props.get("idmutinvar"),
            "date_mutation": props.get("datemut"),
            "nature_mutation": props.get("libnatmut"),
            "valeur_fonciere": float(valeur) if valeur else None,
            "surface_reelle_bati": float(surface) if surface else None,
            "surface_terrain": float(props.get("sterr")) if props.get("sterr") else None,
            "prix_m2": prix_m2,
            "nb_pieces": int(props.get("nbpiece")) if props.get("nbpiece") else None,
            "type_local": props.get("libtypbien"),
            "code_postal": code_postal,
            "code_insee": code_insee,
            "arrondissement": arrondissement,
            "latitude": lat,
            "longitude": lon,
            "vefa": props.get("vefa", False),
            "geom_json": json.dumps(geom) if geom else None,
            "l_idpar": json.dumps(props.get("l_idpar", [])),
            "scraped_at": datetime.now()
        }
        records.append(record)

    df = pd.DataFrame(records)

    # Convertir les dates
    if "date_mutation" in df.columns:
        df["date_mutation"] = pd.to_datetime(df["date_mutation"], errors="coerce")

    # Supprimer les lignes sans donnees essentielles
    df = df.dropna(subset=["valeur_fonciere", "date_mutation"])

    return df


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


def indexer_elasticsearch(df):
    """
    Indexe les donnees dans Elasticsearch
    """
    try:
        from etl.elasticsearch_utils import attendre_elasticsearch, creer_index, indexer_transactions

        print("\n[4/4] Indexation Elasticsearch...")
        if attendre_elasticsearch(max_tentatives=10, delai=3):
            creer_index()
            indexer_transactions(df)
        else:
            print("Elasticsearch non disponible, indexation ignoree")
    except ImportError:
        print("Module Elasticsearch non disponible")
    except Exception as e:
        print(f"Erreur indexation Elasticsearch: {e}")


def run_scraper(annee_min="2020", annee_max="2024", vider_avant=True):
    """
    Fonction principale pour executer le pipeline ETL complet (sans geometries)
    """
    print("=" * 60)
    print("DVF+ Paris Scraper")
    print("=" * 60)

    print("\n[1/4] Scraping depuis l'API DVF+...")
    raw_df = scrape_paris(annee_min, annee_max)

    if raw_df.empty:
        print("Aucune donnee recuperee.")
        return

    print("\n[2/4] Transformation des donnees...")
    transformed_df = transformer_donnees(raw_df)
    print(f"{len(transformed_df)} enregistrements valides")

    print("\n[3/4] Chargement en base de donnees PostgreSQL...")
    if vider_avant:
        vider_table()
    charger_en_bdd(transformed_df)

    indexer_elasticsearch(transformed_df)

    print("\n" + "=" * 60)
    print("Scraping termine!")
    print("=" * 60)

    return transformed_df


def run_scraper_geo(annee_min="2020", annee_max="2024", vider_avant=True):
    """
    Fonction principale pour executer le pipeline ETL avec geometries des parcelles
    """
    print("=" * 60)
    print("DVF+ Paris Scraper - AVEC GEOMETRIES PARCELLES")
    print("=" * 60)

    print("\n[1/4] Scraping depuis l'API DVF+ geomutations...")
    features = scrape_paris_geo(annee_min, annee_max)

    if not features:
        print("Aucune donnee recuperee.")
        return

    print("\n[2/4] Transformation des donnees GeoJSON...")
    transformed_df = transformer_donnees_geo(features)
    print(f"{len(transformed_df)} enregistrements valides avec geometries")

    print("\n[3/4] Chargement en base de donnees PostgreSQL...")
    if vider_avant:
        vider_table()
    charger_en_bdd(transformed_df)

    indexer_elasticsearch(transformed_df)

    print("\n" + "=" * 60)
    print("Scraping termine!")
    print("=" * 60)

    return transformed_df


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--geo":
        run_scraper_geo(annee_min="2024", annee_max="2024")
    else:
        run_scraper(annee_min="2024", annee_max="2024")
