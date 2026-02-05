"""Page d'accueil (splash screen) pour DVF Paris Analytics."""

import streamlit as st


def render_splash():
    """Affiche la page d'accueil interactive avec description et navigation."""

    # CSS pour la page d'accueil (style landing)
    st.markdown("\n".join([
        "<link rel='stylesheet' href='https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'>",
        "<style>",
        ".landing-container { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 2rem; }",
        ".landing-title { font-family: 'Poppins', sans-serif; font-weight: 700; font-size: 2.8rem; color: #3d2817; text-align: center; margin-bottom: 2rem; line-height: 1.3; }",
        ".landing-description { font-size: 1.05rem; color: #555; max-width: 900px; margin: 0 auto 2rem; line-height: 1.8; background: rgba(255, 255, 255, 0.5); padding: 1.5rem; border-radius: 12px; border-left: 4px solid #97bc62; text-align: center; }",
        ".landing-nav { display: flex; flex-direction: column; gap: 1rem; width: 100%; max-width: 600px; }",
        ".landing-nav-item { background: linear-gradient(135deg, #f5f1e8 0%, #e6dfd4 100%); padding: 1.3rem 2rem; border-radius: 12px; border: 2px solid #d4c5b0; display: flex; align-items: center; gap: 1.2rem; transition: all 0.2s; }",
        ".landing-nav-item:hover { transform: translateY(-2px); box-shadow: 0 6px 12px rgba(0,0,0,0.08); border-color: #0f766e; }",
        ".landing-nav-icon { font-size: 1.8rem; color: #3d2817; min-width: 40px; text-align: center; }",
        ".landing-nav-content { flex: 1; }",
        ".landing-nav-text { font-size: 1.2rem; font-weight: 600; color: #3d2817; margin: 0; }",
        ".landing-nav-desc { font-size: 0.85rem; color: #666; margin: 0.2rem 0 0 0; }",
        ".landing-cta { text-align: center; margin: 2rem 0; color: #999; font-size: 0.95rem; }",
        "</style>",
    ]), unsafe_allow_html=True)

    st.markdown("\n".join([
        "<div class='landing-container'>",
        "<div class='landing-title'>Dashboard Transactions Immobilières<br>à Paris</div>",
        "</div>",
    ]), unsafe_allow_html=True)

    # Description du dashboard
    st.markdown("\n".join([
        "<div class='landing-description'>",
        "<strong>Bienvenue dans DVF Paris Analytics</strong> — votre analyse complète du marché immobilier parisien.",
        "<br><br>",
        "Ce dashboard vous permet d'explorer les données de transactions immobilières à Paris avec des visualisations",
        "interactives et puissantes. Découvrez les tendances des prix au fil du temps, analysez les volumes de ventes",
        "par arrondissement et période, et identifiez les opportunités du marché avec nos cartes et graphiques dynamiques.",
        "<br><br>",
        "<strong>Les données proviennent de :</strong> la base DVF (Demandes de Valeurs Foncières) publiée par la",
        "Direction Générale des Finances Publiques, et du cadastre français.",
        "</div>",
    ]), unsafe_allow_html=True)

    st.markdown("\n".join([
        "<div class='landing-container'>",
        "<div class='landing-nav'>",
        "<div class='landing-nav-item'>",
        "<div class='landing-nav-icon'><i class='fa-solid fa-book'></i></div>",
        "<div class='landing-nav-content'>",
        "<div class='landing-nav-text'>Accueil</div>",
        "<div class='landing-nav-desc'>Vocabulaire et concepts clés du marché immobilier</div>",
        "</div>",
        "</div>",
        "<div class='landing-nav-item'>",
        "<div class='landing-nav-icon'><i class='fa-solid fa-building'></i></div>",
        "<div class='landing-nav-content'>",
        "<div class='landing-nav-text'>Transactions</div>",
        "<div class='landing-nav-desc'>Volumes, tendances et mutations par période et arrondissement</div>",
        "</div>",
        "</div>",
        "<div class='landing-nav-item'>",
        "<div class='landing-nav-icon'><i class='fa-solid fa-euro-sign'></i></div>",
        "<div class='landing-nav-content'>",
        "<div class='landing-nav-text'>Prix</div>",
        "<div class='landing-nav-desc'>Évolution des prix au m² et statistiques par arrondissement</div>",
        "</div>",
        "</div>",
        "<div class='landing-nav-item'>",
        "<div class='landing-nav-icon'><i class='fa-solid fa-map'></i></div>",
        "<div class='landing-nav-content'>",
        "<div class='landing-nav-text'>Carte</div>",
        "<div class='landing-nav-desc'>Visualisations géographiques interactives des transactions</div>",
        "</div>",
        "</div>",
        "<div class='landing-nav-item'>",
        "<div class='landing-nav-icon'><i class='fa-solid fa-magnifying-glass'></i></div>",
        "<div class='landing-nav-content'>",
        "<div class='landing-nav-text'>Recherche</div>",
        "<div class='landing-nav-desc'>Filtrez et cherchez des transactions spécifiques</div>",
        "</div>",
        "</div>",
        "<div class='landing-nav-item'>",
        "<div class='landing-nav-icon'><i class='fa-solid fa-star'></i></div>",
        "<div class='landing-nav-content'>",
        "<div class='landing-nav-text'>À propos</div>",
        "<div class='landing-nav-desc'>Informations sur le projet et ses sources</div>",
        "</div>",
        "</div>",
        "</div>",
        "</div>",
    ]), unsafe_allow_html=True)

    # Boutons cliquables pour la navigation
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📖 Accueil", use_container_width=True, key="nav-btn-accueil"):
            st.session_state["nav"] = "Accueil"
            st.rerun()
        if st.button("🏢 Transactions", use_container_width=True, key="nav-btn-trans"):
            st.session_state["nav"] = "Transactions"
            st.rerun()

    with col2:
        if st.button("💰 Prix", use_container_width=True, key="nav-btn-prix"):
            st.session_state["nav"] = "Prix"
            st.rerun()
        if st.button("🗺️ Carte", use_container_width=True, key="nav-btn-carte"):
            st.session_state["nav"] = "Carte"
            st.rerun()

    with col3:
        if st.button("🔍 Recherche", use_container_width=True, key="nav-btn-rech"):
            st.session_state["nav"] = "Recherche"
            st.rerun()
        if st.button("⭐ À propos", use_container_width=True, key="nav-btn-about"):
            st.session_state["nav"] = "À propos"
            st.rerun()

    st.markdown("<div class='landing-cta'>👇 Cliquez sur une section ou un bouton pour commencer</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1.5, 1, 1.5])
    with col2:
        if st.button("🚀 Commencer", use_container_width=True, key="btn-start"):
            st.session_state["nav"] = "Transactions"
            st.rerun()

