"""Page lexique pour expliquer les termes utilisés dans le dashboard."""

import streamlit as st


def render_lexique():
    """affiche le lexique des termes."""
    st.markdown("## lexique")
    st.markdown("---")

    st.markdown("### types d'habitation")
    st.markdown("""
    - **appartement** : logement situé dans un immeuble collectif
    - **maison** : construction individuelle destinée à l'habitation
    - **dépendance** : bâtiment annexe (garage, cave, cellier, etc.)
    - **local industriel** : bâtiment à usage industriel ou artisanal
    """)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### types de vente")
    st.markdown("""
    - **vente** : transaction classique entre un vendeur et un acheteur
    - **vente en l'état futur d'achèvement (VEFA)** : achat sur plan d'un bien en construction
    - **adjudication** : vente aux enchères publiques
    - **expropriation** : acquisition forcée par une autorité publique
    - **vente de terrain à bâtir** : vente d'un terrain nu destiné à la construction
    """)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### indicateurs")
    st.markdown("""
    - **valeur foncière** : prix de vente total du bien en euros
    - **prix au m²** : prix de vente divisé par la surface habitable
    - **surface réelle bâtie** : surface habitable du bien en m²
    - **nombre de pièces** : nombre de pièces principales (hors cuisine et salle de bain)
    - **arrondissement** : division administrative de Paris (1er au 20ème)
    """)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### source des données")
    st.markdown("""
    Les données proviennent de la base **Demandes de Valeurs Foncières (DVF)**
    publiée par la Direction Générale des Finances Publiques (DGFiP).

    Les données cadastrales des bâtiments proviennent du **cadastre Etalab**
    et de la **Base de Données Nationale des Bâtiments (BDNB)**.
    """)
