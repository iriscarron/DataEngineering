"""Router principal des pages Streamlit de l'application DVF Paris."""

import streamlit as st

from dash import about, carte, home, navbar, setup, recherche, lexique
from dash import layout


def render_app():
    """configure la page, applique le theme et route vers la vue choisie."""

    layout.configure_page()
    layout.apply_theme()

    # titre en haut centré
    st.markdown("<h1 style='text-align: center;'>dvf paris - transactions immobilières</h1>", unsafe_allow_html=True)

    # navbar juste en dessous
    pages = ["accueil", "transactions", "prix", "carte", "recherche", "lexique", "à propos"]
    choix = navbar.navbar(pages)

    # chargement des donnees
    df = layout.charger_donnees()
    if df.empty:
        st.warning("aucune donnée disponible. lancez le scraper ou vérifiez la base.")
        st.info("commandes utiles: docker-compose up -d puis python etl/scraper.py")
        return

    # routage vers les pages (chaque page gere ses propres filtres)
    if choix == "accueil":
        home.render_home(df)
    elif choix == "transactions":
        home.render_transactions(df)
    elif choix == "prix":
        home.render_prix(df)
    elif choix == "carte":
        carte.render_carte(df)
    elif choix == "recherche":
        recherche.render_recherche(df)
    elif choix == "lexique":
        lexique.render_lexique()
    elif choix == "à propos":
        about.render_about()
