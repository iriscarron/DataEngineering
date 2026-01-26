"""
Dashboard DVF Paris
Application Streamlit pour visualiser les transactions immobilieres a Paris
"""
import os
import sys
import time
import subprocess
import importlib
from urllib.parse import urlparse


def _normalize_db_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.hostname or ""
    # For exécution locale, force IPv4 loopback to éviter ::1 et les resets sur Windows
    if host == "localhost":
        url = url.replace("localhost", "127.0.0.1")
    # Ajoute un connect_timeout pour éviter de bloquer trop longtemps
    if "?" in url:
        if "connect_timeout" not in url:
            url += "&connect_timeout=5"
    else:
        url += "?connect_timeout=5"
    return url


DATABASE_URL = _normalize_db_url(os.getenv("DATABASE_URL", "postgresql://dvf:dvf@127.0.0.1:5432/dvf"))




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


def ensure_db_driver():
    """S'assure que psycopg2 est install; installe psycopg2-binary si manquant en local."""
    try:
        importlib.import_module("psycopg2")
        return
    except ModuleNotFoundError:
        print("psycopg2 absent, tentative d'installation (psycopg2-binary)...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "psycopg2-binary"], check=True)
        importlib.import_module("psycopg2")
        print("psycopg2-binary install")
    except Exception as exc:  # pylint: disable=broad-except
        print(f"Echec d'installation de psycopg2-binary: {exc}")
        sys.exit(1)


def lancer_docker_compose():
    """Demarre docker-compose en detach pour garantir que Postgres tourne."""
    try:
        print("Demarrage des services Docker (docker-compose up -d)...")
        subprocess.run(["docker-compose", "up", "-d"], check=True)
    except FileNotFoundError:
        print("docker-compose introuvable. Installez Docker Desktop et assurez-vous que docker-compose est dans le PATH.")
        sys.exit(1)
    except subprocess.CalledProcessError as exc:
        print(f"Echec docker-compose up -d: {exc}")
        sys.exit(1)



def verifier_connexion_base(retries=5, delay=3):
    """Valide que la base est joignable avant de lancer des traitements lourds."""
    from sqlalchemy import create_engine, text

    for tentative in range(1, retries + 1):
        try:
            engine = create_engine(DATABASE_URL, pool_pre_ping=True)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"Base accessible (tentative {tentative}/{retries})")
            return True
        except Exception as exc:  # pylint: disable=broad-except
            print(f"Base indisponible (tentative {tentative}/{retries}): {exc}")
            time.sleep(delay)

    print("Impossible de joindre la base. Assurez-vous que Docker/PostgreSQL sont démarrés (docker-compose up -d).")
    return False




def lancer_scraping():
    """Lance le scraping des donnees DVF."""
    print("Pas de donnees en base, lancement du scraping...")
    from etl.scraper import run_scraper


    run_scraper(annee_min="2023", annee_max="2024")




# Si on lance avec "python main.py", on verifie les donnees et on lance Streamlit
if __name__ == "__main__" and "streamlit" not in sys.modules:
    ensure_db_driver()
    lancer_docker_compose()

    if not verifier_connexion_base():
        sys.exit(1)

    if not verifier_donnees_existantes():
        try:
            lancer_scraping()
        except Exception as exc:  # pylint: disable=broad-except
            print(f"Echec du scraping/chargement: {exc}")
            sys.exit(1)
    print("Lancement du dashboard Streamlit...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", __file__])
    sys.exit(0)


# A partir d'ici, c'est l'application Streamlit modularisee
import streamlit as st
from dash.router import render_app




if __name__ == "__main__":
    render_app()

