"""
Script pour charger le cadastre complet de Paris avec les donnees DVF
Fusionne les parcelles cadastrales avec les transactions DVF
"""
import os
import gzip
import json
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dvf:dvf@localhost:5432/dvf")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def charger_cadastre(fichier_gz):
    """Charge le fichier GeoJSON cadastre"""
    print(f"Chargement du cadastre depuis {fichier_gz}...")

    with gzip.open(fichier_gz, 'rt', encoding='utf-8') as f:
        data = json.load(f)

    parcelles = {}
    for feature in data['features']:
        id_parcelle = feature['id']
        parcelles[id_parcelle] = {
            'geometry': feature['geometry'],
            'commune': feature['properties'].get('commune'),
            'prefixe': feature['properties'].get('prefixe'),
            'section': feature['properties'].get('section'),
            'numero': feature['properties'].get('numero')
        }

    print(f"  -> {len(parcelles)} parcelles chargees")
    return parcelles


def charger_dvf(fichier_gz):
    """Charge le fichier CSV DVF geolocalize"""
    print(f"Chargement des DVF depuis {fichier_gz}...")

    with gzip.open(fichier_gz, 'rt', encoding='utf-8') as f:
        df = pd.read_csv(f, low_memory=False)

    print(f"  -> {len(df)} lignes chargees")
    return df


def fusionner_donnees(parcelles, df_dvf):
    """Fusionne les parcelles cadastrales avec les transactions DVF"""
    print("Fusion des donnees...")

    # Grouper les transactions par parcelle
    dvf_par_parcelle = {}
    for _, row in df_dvf.iterrows():
        id_parcelle = row.get('id_parcelle')
        if pd.isna(id_parcelle):
            continue

        if id_parcelle not in dvf_par_parcelle:
            dvf_par_parcelle[id_parcelle] = []

        dvf_par_parcelle[id_parcelle].append({
            'id_mutation': row.get('id_mutation'),
            'date_mutation': row.get('date_mutation'),
            'nature_mutation': row.get('nature_mutation'),
            'valeur_fonciere': row.get('valeur_fonciere'),
            'type_local': row.get('type_local'),
            'surface_reelle_bati': row.get('surface_reelle_bati'),
            'nombre_pieces_principales': row.get('nombre_pieces_principales'),
            'adresse': f"{row.get('adresse_numero', '')} {row.get('adresse_nom_voie', '')}".strip(),
            'code_postal': row.get('code_postal'),
            'latitude': row.get('latitude'),
            'longitude': row.get('longitude')
        })

    print(f"  -> {len(dvf_par_parcelle)} parcelles avec transactions")

    # Creer les enregistrements finaux
    records = []
    for id_parcelle, info in parcelles.items():
        transactions = dvf_par_parcelle.get(id_parcelle, [])

        # Prendre la derniere transaction si disponible
        if transactions:
            # Trier par date et prendre la plus recente
            transactions_valides = [t for t in transactions if t.get('valeur_fonciere')]
            if transactions_valides:
                derniere = max(transactions_valides,
                              key=lambda x: x.get('date_mutation', '1900-01-01'))

                # Calculer prix au m2
                surface = derniere.get('surface_reelle_bati')
                valeur = derniere.get('valeur_fonciere')
                prix_m2 = valeur / surface if surface and surface > 0 else None

                record = {
                    'id_parcelle': id_parcelle,
                    'geom_json': json.dumps(info['geometry']),
                    'commune': info['commune'],
                    'section': info['section'],
                    'numero': info['numero'],
                    'has_transaction': True,
                    'id_mutation': derniere.get('id_mutation'),
                    'date_mutation': derniere.get('date_mutation'),
                    'nature_mutation': derniere.get('nature_mutation'),
                    'valeur_fonciere': valeur,
                    'type_local': derniere.get('type_local'),
                    'surface_reelle_bati': surface,
                    'nb_pieces': derniere.get('nombre_pieces_principales'),
                    'adresse': derniere.get('adresse'),
                    'code_postal': derniere.get('code_postal'),
                    'prix_m2': prix_m2,
                    'latitude': derniere.get('latitude'),
                    'longitude': derniere.get('longitude'),
                    'nb_transactions': len(transactions_valides)
                }
            else:
                record = {
                    'id_parcelle': id_parcelle,
                    'geom_json': json.dumps(info['geometry']),
                    'commune': info['commune'],
                    'section': info['section'],
                    'numero': info['numero'],
                    'has_transaction': False
                }
        else:
            # Parcelle sans transaction
            record = {
                'id_parcelle': id_parcelle,
                'geom_json': json.dumps(info['geometry']),
                'commune': info['commune'],
                'section': info['section'],
                'numero': info['numero'],
                'has_transaction': False
            }

        records.append(record)

    df = pd.DataFrame(records)

    # Extraire l'arrondissement du code commune
    df['arrondissement'] = df['commune'].apply(
        lambda x: str(int(str(x)[-2:])) if pd.notna(x) else None
    )

    print(f"  -> {len(df)} parcelles totales")
    print(f"  -> {df['has_transaction'].sum()} avec transactions")

    return df


def creer_table_parcelles(engine):
    """Cree la table parcelles si elle n'existe pas"""
    with engine.connect() as conn:
        conn.execute(text("""
            DROP TABLE IF EXISTS parcelles CASCADE;

            CREATE TABLE parcelles (
                id SERIAL PRIMARY KEY,
                id_parcelle TEXT UNIQUE,
                geom_json TEXT,
                commune TEXT,
                section TEXT,
                numero TEXT,
                arrondissement TEXT,
                has_transaction BOOLEAN DEFAULT FALSE,
                id_mutation TEXT,
                date_mutation DATE,
                nature_mutation TEXT,
                valeur_fonciere NUMERIC,
                type_local TEXT,
                surface_reelle_bati NUMERIC,
                nb_pieces INTEGER,
                adresse TEXT,
                code_postal TEXT,
                prix_m2 NUMERIC,
                latitude NUMERIC,
                longitude NUMERIC,
                nb_transactions INTEGER DEFAULT 0
            );

            CREATE INDEX idx_parcelles_id ON parcelles(id_parcelle);
            CREATE INDEX idx_parcelles_commune ON parcelles(commune);
            CREATE INDEX idx_parcelles_arr ON parcelles(arrondissement);
            CREATE INDEX idx_parcelles_has_tx ON parcelles(has_transaction);
        """))
        conn.commit()
    print("Table parcelles creee")


def charger_en_bdd(df, engine):
    """Charge les donnees dans PostgreSQL"""
    print(f"Chargement de {len(df)} parcelles en base...")

    df.to_sql(
        'parcelles',
        engine,
        if_exists='append',
        index=False,
        method='multi',
        chunksize=5000
    )

    print("Chargement termine")


def run():
    """Execute le chargement complet"""
    print("=" * 60)
    print("Chargement Cadastre + DVF Paris")
    print("=" * 60)

    cadastre_file = os.path.join(DATA_DIR, "cadastre-75-parcelles.json.gz")
    dvf_file = os.path.join(DATA_DIR, "dvf-paris-2024.csv.gz")

    if not os.path.exists(cadastre_file):
        print(f"ERREUR: Fichier cadastre non trouve: {cadastre_file}")
        return

    if not os.path.exists(dvf_file):
        print(f"ERREUR: Fichier DVF non trouve: {dvf_file}")
        return

    # Charger les donnees
    parcelles = charger_cadastre(cadastre_file)
    df_dvf = charger_dvf(dvf_file)

    # Fusionner
    df_final = fusionner_donnees(parcelles, df_dvf)

    # Charger en base
    engine = create_engine(DATABASE_URL)
    creer_table_parcelles(engine)
    charger_en_bdd(df_final, engine)

    print("\n" + "=" * 60)
    print("Chargement termine!")
    print("=" * 60)


if __name__ == "__main__":
    run()
