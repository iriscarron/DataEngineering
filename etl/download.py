"""
Telechargement rapide des donnees DVF depuis data.gouv.fr
Methode CSV directe - beaucoup plus rapide que l'API
"""
import os
import gzip
import requests
import pandas as pd
from io import BytesIO
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

# URL des fichiers DVF par departement sur data.gouv.fr
DVF_URL_TEMPLATE = "https://files.data.gouv.fr/geo-dvf/latest/csv/{annee}/departements/75.csv.gz"


def telecharger_dvf_paris(annees=None):
    """
    Telecharge les donnees DVF pour Paris (departement 75)
    Retourne un DataFrame avec toutes les annees
    """
    if annees is None:
        annees = ["2024", "2023"]

    tous_les_df = []

    for annee in annees:
        url = DVF_URL_TEMPLATE.format(annee=annee)
        print(f"Telechargement DVF Paris {annee}...")

        try:
            response = requests.get(url, timeout=120)
            response.raise_for_status()

            # Decompresser et lire le CSV
            with gzip.GzipFile(fileobj=BytesIO(response.content)) as f:
                df = pd.read_csv(f, low_memory=False)

            print(f"  {len(df)} lignes pour {annee}")
            tous_les_df.append(df)

        except Exception as e:
            print(f"  Erreur pour {annee}: {e}")

    if tous_les_df:
        df_final = pd.concat(tous_les_df, ignore_index=True)
        print(f"Total: {len(df_final)} lignes")
        return df_final

    return pd.DataFrame()


def transformer_csv_vers_schema(df):
    """
    Transforme les donnees CSV vers notre schema de BDD
    """
    if df.empty:
        return df

    # Filtrer uniquement Paris (codes postaux 75XXX)
    df = df[df["code_postal"].astype(str).str.startswith("75")].copy()

    transformed = pd.DataFrame()

    # Mapping des colonnes CSV vers notre schema
    transformed["date_mutation"] = pd.to_datetime(df["date_mutation"], errors="coerce")
    transformed["valeur_fonciere"] = pd.to_numeric(
        df["valeur_fonciere"].astype(str).str.replace(",", "."),
        errors="coerce"
    )
    transformed["surface_reelle_bati"] = pd.to_numeric(df["surface_reelle_bati"], errors="coerce")

    # Prix au m2
    transformed["prix_m2"] = (
        transformed["valeur_fonciere"] / transformed["surface_reelle_bati"]
    ).replace([float("inf"), float("-inf")], None)

    # Autres colonnes
    transformed["nb_pieces"] = pd.to_numeric(df["nombre_pieces_principales"], errors="coerce")
    transformed["type_local"] = df["type_local"]
    transformed["nature_mutation"] = df["nature_mutation"]
    transformed["code_postal"] = df["code_postal"].astype(str)

    # Arrondissement (extrait du code postal)
    transformed["arrondissement"] = transformed["code_postal"].apply(
        lambda x: str(int(x[-2:])) if pd.notna(x) and len(str(x)) >= 2 else None
    )

    # Coordonnees GPS
    transformed["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    transformed["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    # ID mutation
    if "id_mutation" in df.columns:
        transformed["id_mutation"] = df["id_mutation"]

    # Supprimer lignes sans donnees essentielles
    transformed = transformed.dropna(subset=["valeur_fonciere", "date_mutation"])

    # Filtrer valeurs aberrantes
    transformed = transformed[
        (transformed["valeur_fonciere"] > 1000) &
        (transformed["valeur_fonciere"] < 100000000)
    ]

    return transformed


def run_download_pipeline(annees=None, vider_avant=True):
    """
    Pipeline complet : telechargement CSV + transformation + chargement BDD
    """
    from sqlalchemy import create_engine, text

    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dvf:dvf@localhost:5432/dvf")

    print("=" * 60)
    print("DVF Paris - Telechargement CSV (methode rapide)")
    print("=" * 60)

    # Etape 1: Telecharger
    print("\n[1/4] Telechargement des fichiers CSV...")
    df_raw = telecharger_dvf_paris(annees)

    if df_raw.empty:
        print("Aucune donnee telechargee")
        return None

    # Etape 2: Transformer
    print("\n[2/4] Transformation des donnees...")
    df_transformed = transformer_csv_vers_schema(df_raw)
    print(f"  {len(df_transformed)} transactions Paris valides")

    # Etape 3: Charger en BDD
    print("\n[3/4] Chargement en base PostgreSQL...")
    engine = create_engine(DATABASE_URL)

    if vider_avant:
        with engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE transactions RESTART IDENTITY"))
            conn.commit()
        print("  Table videe")

    df_transformed["scraped_at"] = datetime.now()
    df_transformed.to_sql(
        "transactions",
        engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000
    )
    print(f"  {len(df_transformed)} enregistrements charges")

    # Etape 4: Indexer Elasticsearch
    try:
        from etl.elasticsearch_utils import attendre_elasticsearch, creer_index, indexer_transactions

        print("\n[4/4] Indexation Elasticsearch...")
        if attendre_elasticsearch(max_tentatives=10, delai=3):
            creer_index()
            indexer_transactions(df_transformed)
        else:
            print("  Elasticsearch non disponible")
    except Exception as e:
        print(f"  Erreur ES: {e}")

    print("\n" + "=" * 60)
    print("Telechargement termine!")
    print("=" * 60)

    return df_transformed


if __name__ == "__main__":
    run_download_pipeline(annees=["2024", "2023"])
