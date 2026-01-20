# -*- coding: utf-8 -*-
"""
Dashboard DVF Paris
Application Streamlit pour visualiser les transactions immobilieres a Paris
"""
import os
import sys
import subprocess

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dvf:dvf@localhost:5432/dvf")


def verifier_donnees_existantes():
    """Verifie si des donnees existent deja dans la base."""
    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM transactions"))
            count = result.scalar()
            return count > 0
    except Exception:  # pylint: disable=broad-except
        return False


def lancer_scraping():
    """Lance le scraping des donnees DVF."""
    print("Pas de donnees en base, lancement du scraping...")
    from etl.scraper import run_scraper

    run_scraper(annee_min="2023", annee_max="2024")
=======



# Si on lance avec "python main.py", on verifie les donnees et on lance Streamlit
if __name__ == "__main__" and "streamlit" not in sys.modules:
    if not verifier_donnees_existantes():
        lancer_scraping()
    print("Lancement du dashboard Streamlit...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", __file__])
    sys.exit(0)
