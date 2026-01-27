"""Router principal des pages Streamlit de l'application DVF Paris."""

import streamlit as st

from dash import about, carte, home, navbar, setup, recherche
from dash import layout


def render_app():
    """configure la page, applique le theme et route vers la vue choisie."""

    layout.configure_page()
    layout.apply_theme()

    # titre en haut centré
    st.markdown("""
        <link href='https://fonts.googleapis.com/css2?family=Poppins:wght@700&display=swap' rel='stylesheet'>
        <h1 style='text-align: center; font-family: "Poppins", sans-serif; font-weight: 700; font-size: 2.5rem; color: #3d2817;'>
            Dashboard Transactions Immobilières à Paris
        </h1>
    """, unsafe_allow_html=True)

    # navbar juste en dessous avec icônes
    pages = ["Accueil", "Transactions", "Prix", "Carte", "Recherche", "À propos"]
    icons = {
        "Accueil": "home",
        "Transactions": "building",
        "Prix": "euro",
        "Carte": "map",
        "Recherche": "search",
        "À propos": "star"
    }
    choix = navbar.navbar(pages, icons=icons)

    # chargement des donnees
    df = layout.charger_donnees()
    if df.empty:
        st.warning("aucune donnée disponible. lancez le scraper ou vérifiez la base.")
        st.info("commandes utiles: docker-compose up -d puis python etl/scraper.py")
        return

    # routage vers les pages (chaque page gere ses propres filtres)
    if choix == "Accueil":
        home.render_home(df)
    elif choix == "Transactions":
        home.render_transactions(df)
    elif choix == "Prix":
        home.render_prix(df)
    elif choix == "Carte":
        carte.render_carte(df)
    elif choix == "Recherche":
        recherche.render_recherche(df)
    elif choix == "À propos":
        about.render_about()
