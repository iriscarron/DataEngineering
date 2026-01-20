import streamlit as st


def render_about():
    st.header("A propos")
    st.markdown(
        """
        **DVF Paris** est un tableau de bord interactif construit avec Streamlit
        pour explorer les transactions immobilieres a Paris (donnees DVF+ du Cerema).

        - Visualisations: timeline, prix par arrondissement, distribution par type de bien, cartes interactives.
        - Stack: Python, Streamlit, Plotly, PostgreSQL, SQLAlchemy.
        - Donnees: mises a jour via le scraper DVF+ fourni dans le projet.

        _Auteur: Projet etl / dashboard Streamlit._
        """
    )
