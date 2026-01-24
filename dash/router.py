import streamlit as st

from dash import about, carte, home, navbar, setup, simplepage
from dash import layout


def render_app():
    layout.configure_page()
    layout.apply_theme()

    st.title("DVF Paris - Transactions Immobilieres")
    st.caption("Donnees scrapees depuis l'API DVF+ du Cerema")

    df = layout.charger_donnees()
    if df.empty:
        st.warning("Aucune donnee disponible. Lancez le scraper ou verifiez la base.")
        st.info("Commandes utiles: docker-compose up -d puis python etl/scraper.py")
        return

    df_filtre, filters = layout.render_filters(df)

    pages = {
        "Accueil": lambda: home.render_home(df_filtre, filters),
        "Transactions": lambda: home.render_transactions(df_filtre, filters),
        "Prix": lambda: home.render_prix(df_filtre),
        "Carte": lambda: carte.render_carte(df_filtre),
        "Setup": lambda: setup.render_setup(df, df_filtre),
        "Simple": lambda: simplepage.render_simple(df_filtre),
        "A propos": about.render_about,
    }

    choix = navbar.navbar(list(pages.keys()))
    pages.get(choix, pages["Accueil"])()
