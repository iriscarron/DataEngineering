"""Page lexique pour expliquer les termes utilisés dans le dashboard."""

import streamlit as st


def render_lexique():
    """affiche le lexique des termes."""

    # Types d'habitation
    st.markdown("""
    <div style='background-color: #D4A76A; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
        <h3 style='color: #fff; margin-top: 0;'>Types d'habitation</h3>
        <ul style='color: #fff; font-size: 16px;'>
            <li><strong>Appartement</strong> : logement situé dans un immeuble collectif</li>
            <li><strong>Maison</strong> : construction individuelle destinée à l'habitation</li>
            <li><strong>Dépendance</strong> : bâtiment annexe (garage, cave, cellier, etc.)</li>
            <li><strong>Local industriel</strong> : bâtiment à usage industriel ou artisanal</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # Types de vente
    st.markdown("""
    <div style='background-color: #A0826D; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
        <h3 style='color: #fff; margin-top: 0;'>Types de vente</h3>
        <ul style='color: #fff; font-size: 16px;'>
            <li><strong>Vente</strong> : transaction classique entre un vendeur et un acheteur</li>
            <li><strong>Vente en l'état futur d'achèvement (VEFA)</strong> : achat sur plan d'un bien en construction</li>
            <li><strong>Adjudication</strong> : vente aux enchères publiques</li>
            <li><strong>Expropriation</strong> : acquisition forcée par une autorité publique</li>
            <li><strong>Vente de terrain à bâtir</strong> : vente d'un terrain nu destiné à la construction</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # Indicateurs
    st.markdown("""
    <div style='background-color: #8B7355; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
        <h3 style='color: #fff; margin-top: 0;'>Indicateurs clés</h3>
        <ul style='color: #fff; font-size: 16px;'>
            <li><strong>Valeur foncière</strong> : prix de vente total du bien en euros</li>
            <li><strong>Prix au m²</strong> : prix de vente divisé par la surface habitable</li>
            <li><strong>Surface réelle bâtie</strong> : surface habitable du bien en m²</li>
            <li><strong>Nombre de pièces</strong> : nombre de pièces principales (hors cuisine et salle de bain)</li>
            <li><strong>Arrondissement</strong> : division administrative de Paris (1er au 20ème)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # Source des données
    st.markdown("""
    <div style='background-color: #6B8E23; padding: 20px; border-radius: 10px;'>
        <h3 style='color: #fff; margin-top: 0;'>Source des données</h3>
        <p style='color: #fff; font-size: 16px;'>
            Les données proviennent de la base <strong>Demandes de Valeurs Foncières (DVF)</strong>
            publiée par la Direction Générale des Finances Publiques (DGFiP).
        </p>
        <p style='color: #fff; font-size: 16px;'>
            Les données cadastrales des bâtiments proviennent du <strong>cadastre Etalab</strong>
            et de la <strong>Base de Données Nationale des Bâtiments (BDNB)</strong>.
        </p>
    </div>
    """, unsafe_allow_html=True)
