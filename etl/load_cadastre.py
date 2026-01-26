"""Charge les données cadastrales des bâtiments de Paris dans PostgreSQL."""

import json
import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dvf:dvf@localhost:5432/dvf")


def load_batiments():
    """Charge les bâtiments cadastraux de Paris dans PostGIS."""
    engine = create_engine(DATABASE_URL)

    print("Création de la table batiments...")
    with engine.connect() as conn:
        # Supprimer la table si elle existe
        conn.execute(text("DROP TABLE IF EXISTS batiments CASCADE"))
        conn.commit()

        # Créer la table avec géométrie
        conn.execute(text("""
            CREATE TABLE batiments (
                id SERIAL PRIMARY KEY,
                type VARCHAR(10),
                nom VARCHAR(255),
                commune VARCHAR(10),
                created DATE,
                updated DATE,
                geom GEOMETRY(MultiPolygon, 4326)
            )
        """))
        conn.commit()

        # Créer un index spatial
        conn.execute(text("""
            CREATE INDEX idx_batiments_geom ON batiments USING GIST(geom)
        """))
        conn.commit()

    print("Chargement du fichier GeoJSON...")
    with open("data/cadastre/cadastre-75-batiments.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    features = data["features"]
    print(f"Insertion de {len(features):,} bâtiments...")

    batch_size = 1000
    with engine.connect() as conn:
        for i in range(0, len(features), batch_size):
            batch = features[i:i + batch_size]
            if i % 10000 == 0:
                print(f"  {i:,}/{len(features):,} bâtiments insérés...")

            for feature in batch:
                geom = json.dumps(feature["geometry"])
                props = feature["properties"]

                conn.execute(text("""
                    INSERT INTO batiments (type, nom, commune, created, updated, geom)
                    VALUES (:type, :nom, :commune, :created, :updated,
                            ST_SetSRID(ST_GeomFromGeoJSON(:geom), 4326))
                """), {
                    "type": props.get("type"),
                    "nom": props.get("nom"),
                    "commune": props.get("commune"),
                    "created": props.get("created"),
                    "updated": props.get("updated"),
                    "geom": geom
                })

            conn.commit()

    print("Création de l'index sur commune...")
    with engine.connect() as conn:
        conn.execute(text("CREATE INDEX idx_batiments_commune ON batiments(commune)"))
        conn.commit()

    print("✓ Chargement terminé !")

    # Statistiques
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM batiments"))
        count = result.scalar()
        print(f"Total: {count:,} bâtiments chargés")


if __name__ == "__main__":
    load_batiments()
