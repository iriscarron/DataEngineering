"""Page d'accueil (splash screen) pour DVF Paris Analytics."""

import streamlit as st


def render_splash():
    """Affiche la page d'accueil avec introduction et flèche interactive."""

    # Style CSS personnalisé pour la page d'accueil
    st.markdown("""
        <style>
        /* Style global */
        html, body {
            margin: 0;
            padding: 0;
        }

        /* Titre principal */
        h1 {
            color: #2c5f2d !important;
            font-size: 3.5em !important;
            font-weight: 700 !important;
            margin-bottom: 20px !important;
            letter-spacing: -1px !important;
            text-align: center !important;
        }

        /* Sous-titre */
        h2 {
            color: #4a7c59 !important;
            font-size: 1.3em !important;
            font-weight: 500 !important;
            margin-bottom: 40px !important;
            text-align: center !important;
            line-height: 1.6 !important;
        }

        /* Paragraphes */
        p {
            color: #2d3436 !important;
            font-size: 1.1em !important;
            line-height: 1.8 !important;
            text-align: center !important;
            margin-bottom: 60px !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Titre principal
    st.markdown("<h1>🏠 DVF Paris Analytics</h1>", unsafe_allow_html=True)

    # Sous-titre
    st.markdown("<h2>Explorez les transactions immobilières de Paris</h2>", unsafe_allow_html=True)

    # Description
    st.markdown("""
    <p>
        Découvrez les tendances du marché immobilier parisien avec nos visualisations
        interactives. Analysez les prix, les volumes de transactions et explorez
        les données géographiques en temps réel.
    </p>
    """, unsafe_allow_html=True)

    # Espacement
    st.markdown("<br>", unsafe_allow_html=True)

    # Features en colonnes
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style='background: white; padding: 25px; border-radius: 12px;
                    box-shadow: 0 2px 8px rgba(44, 95, 45, 0.1);
                    border-left: 4px solid #97bc62; margin-bottom: 20px;'>
            <div style='font-size: 2.5em; margin-bottom: 10px;'>📊</div>
            <div style='color: #2c5f2d; font-size: 1.1em; font-weight: 600; margin-bottom: 8px;'>Graphiques Dynamiques</div>
            <div style='color: #555; font-size: 0.95em; line-height: 1.5;'>
                Visualisez les tendances des prix et volumes avec des graphiques interactifs
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style='background: white; padding: 25px; border-radius: 12px;
                    box-shadow: 0 2px 8px rgba(44, 95, 45, 0.1);
                    border-left: 4px solid #97bc62;'>
            <div style='font-size: 2.5em; margin-bottom: 10px;'>🔍</div>
            <div style='color: #2c5f2d; font-size: 1.1em; font-weight: 600; margin-bottom: 8px;'>Recherche Avancée</div>
            <div style='color: #555; font-size: 0.95em; line-height: 1.5;'>
                Trouvez les transactions spécifiques avec nos filtres puissants
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style='background: white; padding: 25px; border-radius: 12px;
                    box-shadow: 0 2px 8px rgba(44, 95, 45, 0.1);
                    border-left: 4px solid #97bc62; margin-bottom: 20px;'>
            <div style='font-size: 2.5em; margin-bottom: 10px;'>🗺️</div>
            <div style='color: #2c5f2d; font-size: 1.1em; font-weight: 600; margin-bottom: 8px;'>Carte Interactive</div>
            <div style='color: #555; font-size: 0.95em; line-height: 1.5;'>
                Explorez les quartiers de Paris sur une carte détaillée
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style='background: white; padding: 25px; border-radius: 12px;
                    box-shadow: 0 2px 8px rgba(44, 95, 45, 0.1);
                    border-left: 4px solid #97bc62;'>
            <div style='font-size: 2.5em; margin-bottom: 10px;'>📈</div>
            <div style='color: #2c5f2d; font-size: 1.1em; font-weight: 600; margin-bottom: 8px;'>Statistiques</div>
            <div style='color: #555; font-size: 0.95em; line-height: 1.5;'>
                Consultez les KPIs et les analyses détaillées du marché
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Espacement
    st.markdown("<br><br><br>", unsafe_allow_html=True)

    # Bouton pour accéder au dashboard
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("➜ Accéder au dashboard", use_container_width=True, key="splash-button"):
            st.session_state.show_splash = False
            st.rerun()
