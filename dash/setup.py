"""Page de vérification rapide de la configuration et des données."""

import streamlit as st


def render_setup(df, df_filtre):
    """Affiche des métriques de couverture et des conseils d'utilisation."""

    st.header("Configuration et etat des donnees")

    total = len(df)
    visibles = len(df_filtre)
    couverture = 0 if total == 0 else visibles / total

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Lignes en base", f"{total:,}")
    with col2:
        st.metric("Lignes apres filtres", f"{visibles:,}")
    with col3:
        st.metric("Couverture visible", f"{couverture*100:.1f}%")

    st.progress(min(max(couverture, 0), 1))

    st.subheader("conseils")
    st.markdown(
        """
        - Lancez `docker-compose up -d` pour demarrer Postgres avant d'ouvrir le dashboard.
        - Si aucune donnee n'apparait, executez `python etl/scraper.py`
        ou relancez `python main.py` pour declencher le scraping automatique.
        - Ajustez les filtres dans la barre laterale pour affiner les visualisations.
        """
    )
