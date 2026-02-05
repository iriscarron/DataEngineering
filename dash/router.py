"""Router principal des pages Streamlit de l'application DVF Paris."""

import streamlit as st

from dash import about, carte, home, navbar, setup, recherche, splash
from dash import layout


def render_app():
    """configure la page, applique le theme et route vers la vue choisie."""

    layout.configure_page()
    layout.apply_theme()

    # Initialiser l'état de navigation
    if "show_splash" not in st.session_state:
        st.session_state.show_splash = True

    if "current_page" not in st.session_state:
        st.session_state.current_page = "Accueil"

    # Afficher la page d'accueil (splash screen) en premier
    if st.session_state.show_splash:
        splash.render_splash()
        return

    # Navigation standard après la splash screen
    pages = ["Accueil", "Transactions", "Prix", "Carte", "Recherche", "À propos"]

    # Bouton pour revenir à la splash screen
    col1, col2, col3 = st.columns([1, 6, 1])
    with col2:
        if st.button("Revenir à la page d'accueil", help="Retour à l'accueil", use_container_width=True):
            st.session_state.show_splash = True
            st.rerun()

    choix = navbar.navbar(pages)

    df = layout.charger_donnees()
    if df.empty:
        st.warning("aucune donnée disponible. lancez le scraper ou vérifiez la base.")
        st.info("commandes utiles: docker-compose up -d puis python etl/scraper.py")
        return

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
