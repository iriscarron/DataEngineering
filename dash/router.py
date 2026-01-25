"""Router principal des pages Streamlit de l'application DVF Paris."""

import streamlit as st

from dash import about, carte, home, navbar, setup, recherche
from dash import layout


def render_app():
    """Configure la page, applique le thème et route vers la vue choisie."""

    layout.configure_page()
    layout.apply_theme()

    # En-tête avec design amélioré
    st.markdown(
        """
        <div style='text-align: center; padding: 1.5rem 0 1rem 0;'>
            <h1 style='color: #0ea5e9; font-size: 2.8rem; font-weight: 800; margin: 0;
                       text-shadow: 0 2px 4px rgba(14, 165, 233, 0.3);'>
                DVF Paris - Transactions Immobilières
            </h1>
            <p style='color: #94a3b8; font-size: 1.1rem; margin-top: 0.5rem;'>
                Données scrapées depuis l'API DVF+ du Cerema<br>
                Analyse intelligente avec Elasticsearch
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    df = layout.charger_donnees()
    if df.empty:
        st.warning("Aucune donnée disponible. Lancez le scraper ou vérifiez la base.")
        st.info("Commandes utiles: docker-compose up -d puis python etl/scraper.py")
        return

    df_filtre, filters = layout.render_filters(df)

    pages = {
        "Accueil": lambda: home.render_home(df_filtre, filters),
        "Transactions": lambda: home.render_transactions(df_filtre, filters),
        "Prix": lambda: home.render_prix(df_filtre),
        "Carte": lambda: carte.render_carte(df_filtre),
        "Recherche": lambda: recherche.render_recherche(df),
        "Setup": lambda: setup.render_setup(df, df_filtre),
        "À propos": about.render_about,
    }

    choix = navbar.navbar(list(pages.keys()))
    pages.get(choix, pages["Accueil"])()
