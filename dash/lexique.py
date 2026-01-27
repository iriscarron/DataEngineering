"""Page lexique pour expliquer les termes utilisés dans le dashboard."""

import streamlit as st


def render_lexique():
    """affiche le lexique des termes."""
    st.markdown("## Lexique")
    st.markdown("---")

    st.markdown("### Types d'habitation")
    st.markdown("""
    - **Appartement** : logement situé dans un immeuble collectif
    - **Maison** : construction individuelle destinée à l'habitation
    - **Dépendance** : bâtiment annexe (garage, cave, cellier, etc.)
    - **Local industriel** : bâtiment à usage industriel ou artisanal
    """)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### Types de vente")
    st.markdown("""
    - **Vente** : transaction classique entre un vendeur et un acheteur
    - **Vente en l'état futur d'achèvement (VEFA)** : achat sur plan d'un bien en construction
    - **Adjudication** : vente aux enchères publiques
    - **Expropriation** : acquisition forcée par une autorité publique
    - **Vente de terrain à bâtir** : vente d'un terrain nu destiné à la construction
    """)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### Indicateurs")
    st.markdown("""
    - **Valeur foncière** : prix de vente total du bien en euros
    - **Prix au m²** : prix de vente divisé par la surface habitable
    - **Surface réelle bâtie** : surface habitable du bien en m²
    - **Nombre de pièces** : nombre de pièces principales (hors cuisine et salle de bain)
    - **Arrondissement** : division administrative de Paris (1er au 20ème)
    """)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### Source des données")
    st.markdown("""
    Les données proviennent de la base **Demandes de Valeurs Foncières (DVF)**
    publiée par la Direction Générale des Finances Publiques (DGFiP).

    Les données cadastrales des bâtiments proviennent du **cadastre Etalab**
    et de la **Base de Données Nationale des Bâtiments (BDNB)**.
    """)
