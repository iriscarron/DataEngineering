"""Clean DVF CSV and load into Postgres.
Assumes a table `transactions` already exists (see docker/init-db.sql).
"""
import os
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dvf:dvf@localhost:5432/dvf")
RAW_FILE = Path("data/raw/dvf.csv")
CHUNKSIZE = 50_000


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    cols = {c.lower(): c for c in df.columns}
    df = df.rename(columns=cols)
    if "date_mutation" in df.columns:
        df["date_mutation"] = pd.to_datetime(df["date_mutation"], errors="coerce").dt.date
    if "valeur_fonciere" in df.columns and "surface_reelle_bati" in df.columns:
        df["prix_m2"] = df["valeur_fonciere"] / df["surface_reelle_bati"].replace(0, pd.NA)
    if "numero_disposition" in df.columns:
        df = df.drop(columns=["numero_disposition"], errors="ignore")
    keep = [
        "date_mutation",
        "valeur_fonciere",
        "surface_reelle_bati",
        "prix_m2",
        "type_local",
        "code_postal",
        "arrondissement",
        "latitude",
        "longitude",
    ]
    for col in keep:
        if col not in df.columns:
            df[col] = pd.NA
    return df[keep]


def load():
    if not RAW_FILE.exists():
        raise FileNotFoundError(f"Missing {RAW_FILE}")

    engine = create_engine(DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))

    for chunk in pd.read_csv(RAW_FILE, chunksize=CHUNKSIZE, low_memory=False):
        clean = preprocess(chunk)
        clean.to_sql("transactions", engine, if_exists="append", index=False)
        print(f"Inserted {len(clean)} rows")


if __name__ == "__main__":
    load()
