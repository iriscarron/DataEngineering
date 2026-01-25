import streamlit as st


def render_about():
    st.markdown(
        """
        <div style='background: linear-gradient(135deg, #0c4a6e 0%, #0369a1 100%);
                    padding: 2.5rem 2rem; border-radius: 16px; margin-bottom: 2rem;
                    box-shadow: 0 8px 32px rgba(14, 165, 233, 0.4); text-align: center;'>
            <h1 style='color: white; font-size: 2.5rem; margin: 0;'> À propos de DVF Paris</h1>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Description du projet
    st.markdown(
        """
        <div style='background: linear-gradient(135deg, #0f2f4f 0%, #1a3a52 100%);
                    padding: 2rem; border-radius: 12px; margin-bottom: 1.5rem;
                    border: 1px solid #0ea5e9; box-shadow: 0 4px 12px rgba(14, 165, 233, 0.2);'>
            <p style='color: #e0f2fe; font-size: 1.15rem; line-height: 1.8;'>
                <strong style='color: #0ea5e9;'>DVF Paris</strong> est un tableau de bord interactif 
                construit avec <strong>Streamlit</strong> pour explorer les transactions immobilières 
                à Paris basé sur les données <strong>DVF+</strong> (Demandes de Valeurs Foncières) du Cerema.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Stack technique avec icônes
    st.markdown("### Stack Technique")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(
            """
            <div style='background: #0f2f4f; padding: 1.5rem; border-radius: 10px;
                        border: 1px solid #0ea5e9; margin-bottom: 1rem;'>
                <div style='color: #0ea5e9; font-weight: 700; font-size: 1.1rem; margin-bottom: 1rem;'> Backend</div>
                <div style='color: #cbd5e1; line-height: 2;'>
                     <strong>Python 3.11</strong><br>
                     <strong>PostgreSQL + PostGIS</strong><br>
                     <strong>Elasticsearch 8.11</strong><br>
                     <strong>SQLAlchemy 2.0</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            """
            <div style='background: #0f2f4f; padding: 1.5rem; border-radius: 10px;
                        border: 1px solid #06b6d4; margin-bottom: 1rem;'>
                <div style='color: #06b6d4; font-weight: 700; font-size: 1.1rem; margin-bottom: 1rem;'> Frontend</div>
                <div style='color: #cbd5e1; line-height: 2;'>
                     <strong>Streamlit</strong><br>
                     <strong>Plotly Express</strong><br>
                     <strong>Mapbox</strong><br>
                     <strong>Design System moderne</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Fonctionnalités
    st.markdown("### Fonctionnalités")
    
    features = [
        ("•", "7 types de visualisations", "Timeline, prix par arrondissement, distribution, boxplot, pie chart..."),
        ("•", "Cartes interactives", "Carte choroplèthe et points géolocalisés avec Mapbox"),
        ("•", "Recherche Elasticsearch", "Moteur de recherche intelligent avec fuzzy matching"),
        ("•", "Filtres avancés", "Date, arrondissement, type de bien, nature de vente, prix"),
        ("•", "Scraping automatique", "Pipeline ETL automatisé au lancement avec retry"),
        ("•", "Architecture Docker", "3 services orchestrés avec docker-compose + healthchecks"),
    ]
    
    col_f1, col_f2 = st.columns(2)
    
    for i, (marker, titre, desc) in enumerate(features):
        col = col_f1 if i % 2 == 0 else col_f2
        with col:
            st.markdown(
                f"""
                <div style='background: #0f2f4f; padding: 1rem; border-radius: 8px;
                            border-left: 3px solid #0ea5e9; margin-bottom: 0.8rem;'>
                    <div style='color: #0ea5e9; font-weight: 700; font-size: 1rem;'>{marker} {titre}</div>
                    <div style='color: #94a3b8; font-size: 0.85rem; margin-top: 0.3rem;'>{desc}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
    
    # Source des données
    st.markdown("### Source des Données")
    st.markdown(
        """
        <div style='background: linear-gradient(90deg, #0f2f4f 0%, #1a3a52 100%);
                    padding: 1.5rem; border-radius: 10px;
                    border: 1px solid #06b6d4;'>
            <div style='color: #e0f2fe; line-height: 1.8;'>
                <strong style='color: #06b6d4;'>API DVF+ du Cerema</strong><br>
                 <a href='https://datafoncier.cerema.fr' target='_blank' style='color: #0ea5e9;'>https://datafoncier.cerema.fr</a><br>
                 Mise à jour: 2 fois par an (avril et octobre)<br>
                 Couverture: Transactions immobilières en France depuis 2014<br>
                 Licence: Licence Ouverte / Open Licence (Etalab)
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Auteurs
    st.markdown(
        """
        <div style='text-align: center; padding: 2rem; background: #0f2f4f;
                    border-radius: 12px; border: 1px solid #0ea5e9;'>
            <div style='color: #0ea5e9; font-size: 1.3rem; font-weight: 700; margin-bottom: 0.5rem;'> Équipe</div>
            <div style='color: #cbd5e1; font-size: 1.1rem;'>
                Iris Carron & Cléo Detrez
            </div>
            <div style='color: #94a3b8; font-size: 0.9rem; margin-top: 0.5rem;'>
                Projet Data Engineering - 2026
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
