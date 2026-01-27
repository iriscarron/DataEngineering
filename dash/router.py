"""Router principal des pages Streamlit de l'application DVF Paris."""

import streamlit as st

from dash import about, carte, home, navbar, setup, recherche, lexique
from dash import layout


def render_app():
    """configure la page, applique le theme et route vers la vue choisie."""

    layout.configure_page()
    layout.apply_theme()

    # titre en haut centré
    st.markdown("<h1 style='text-align: center;'>DVF Paris - Transactions Immobilières</h1>", unsafe_allow_html=True)

    # navbar juste en dessous
    pages = ["Accueil", "Transactions", "Prix", "Carte", "Recherche", "Lexique", "À propos"]
    choix = navbar.navbar(pages)

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
    elif choix == "Lexique":
        lexique.render_lexique()
    elif choix == "À propos":
        about.render_about()
