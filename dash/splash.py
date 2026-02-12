"""Page d'accueil (splash screen) pour DVF Paris Analytics."""

import streamlit as st


def render_splash():
    """affiche la page d'accueil interactive avec description et navigation."""

    nav_param = ""
    if hasattr(st, "query_params"):
        nav_param = st.query_params.get("nav", "")
    else:
        params = st.experimental_get_query_params()
        nav_param = params.get("nav", [""])[0]

    if nav_param in {"Accueil", "Transactions", "Prix", "Carte", "Recherche", "À propos"}:
        if hasattr(st, "query_params"):
            st.query_params.clear()
        else:
            st.experimental_set_query_params()
        st.session_state["nav"] = nav_param
        st.session_state["show_splash"] = False
        st.rerun()

    st.markdown("\n".join([
        "<link rel='stylesheet' href='https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'>",
        "<style>",
        ".landing-container { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 2rem; }",
        ".landing-title { font-family: 'Poppins', sans-serif; font-weight: 700; font-size: 2.8rem; color: #3d2817; text-align: center; margin-bottom: 2rem; line-height: 1.3; }",
        ".landing-description { font-size: 1.05rem; color: #555; max-width: 900px; margin: 0 auto 2rem; line-height: 1.8; background: rgba(255, 255, 255, 0.5); padding: 1.5rem; border-radius: 12px; border-left: 4px solid #97bc62; text-align: center; }",
        ".landing-nav { display: flex; flex-direction: column; gap: 1rem; width: 100%; max-width: 600px; }",
        ".landing-card-form { margin: 0 0 1rem 0; }",
        ".landing-card-button { background: linear-gradient(135deg, #f5f1e8 0%, #e6dfd4 100%); padding: 1.3rem 2rem; border-radius: 12px; border: 2px solid #d4c5b0; display: block; transition: all 0.2s; width: 100%; cursor: pointer; text-align: left; }",
        ".landing-card-button:hover { transform: translateY(-2px); box-shadow: 0 6px 12px rgba(0,0,0,0.08); border-color: #0f766e; }",
        ".landing-card-button:focus { outline: none; }",
        ".landing-card-button * { text-decoration: none; }",
        ".landing-nav-item { display: flex; align-items: center; gap: 1.2rem; }",
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

    st.markdown("\n".join([
        "<div class='landing-description'>",
        "<strong>Bonjour !</strong>",
        "<br><br>",
        "Ce dashboard permet de visualiser les ventes immobilieres a Paris.",
        "<br><br>",
        "Vous pouvez :",
        "<br>",
        "- Voir l'evolution des prix par arrondissement",
        "<br>",
        "- Explorer les transactions sur une carte",
        "<br>",
        "- Rechercher des biens specifiques",
        "<br>",
        "- Comparer les prix au m2",
        "<br><br>",
        "<em>Donnees : base DVF (Demandes de Valeurs Foncieres) et cadastre francais.</em>",
        "</div>",
    ]), unsafe_allow_html=True)

    pad1, col1, col2, col3, pad2 = st.columns([1, 2, 2, 2, 1])
    with col1:
        st.markdown("\n".join([
            "<form class='landing-card-form' method='get'>",
            "<input type='hidden' name='nav' value='Accueil' />",
            "<button type='submit' class='landing-card-button'>",
            "<div class='landing-nav-item'>",
            "<div class='landing-nav-icon'><i class='fa-solid fa-book'></i></div>",
            "<div class='landing-nav-content'>",
            "<div class='landing-nav-text'>Accueil</div>",
            "<div class='landing-nav-desc'>Vocabulaire et concepts clés du marché immobilier</div>",
            "</div>",
            "</div>",
            "</button>",
            "</form>",
        ]), unsafe_allow_html=True)

    with col2:
        st.markdown("\n".join([
            "<form class='landing-card-form' method='get'>",
            "<input type='hidden' name='nav' value='Transactions' />",
            "<button type='submit' class='landing-card-button'>",
            "<div class='landing-nav-item'>",
            "<div class='landing-nav-icon'><i class='fa-solid fa-building'></i></div>",
            "<div class='landing-nav-content'>",
            "<div class='landing-nav-text'>Transactions</div>",
            "<div class='landing-nav-desc'>Volumes, tendances et mutations par période et arrondissement</div>",
            "</div>",
            "</div>",
            "</button>",
            "</form>",
        ]), unsafe_allow_html=True)

    with col3:
        st.markdown("\n".join([
            "<form class='landing-card-form' method='get'>",
            "<input type='hidden' name='nav' value='Prix' />",
            "<button type='submit' class='landing-card-button'>",
            "<div class='landing-nav-item'>",
            "<div class='landing-nav-icon'><i class='fa-solid fa-euro-sign'></i></div>",
            "<div class='landing-nav-content'>",
            "<div class='landing-nav-text'>Prix</div>",
            "<div class='landing-nav-desc'>Évolution des prix au m² et statistiques par arrondissement</div>",
            "</div>",
            "</div>",
            "</button>",
            "</form>",
        ]), unsafe_allow_html=True)

    pad3, col4, col5, col6, pad4 = st.columns([1, 2, 2, 2, 1])
    with col4:
        st.markdown("\n".join([
            "<form class='landing-card-form' method='get'>",
            "<input type='hidden' name='nav' value='Carte' />",
            "<button type='submit' class='landing-card-button'>",
            "<div class='landing-nav-item'>",
            "<div class='landing-nav-icon'><i class='fa-solid fa-map'></i></div>",
            "<div class='landing-nav-content'>",
            "<div class='landing-nav-text'>Carte</div>",
            "<div class='landing-nav-desc'>Visualisations géographiques interactives des transactions</div>",
            "</div>",
            "</div>",
            "</button>",
            "</form>",
        ]), unsafe_allow_html=True)

    with col5:
        st.markdown("\n".join([
            "<form class='landing-card-form' method='get'>",
            "<input type='hidden' name='nav' value='Recherche' />",
            "<button type='submit' class='landing-card-button'>",
            "<div class='landing-nav-item'>",
            "<div class='landing-nav-icon'><i class='fa-solid fa-magnifying-glass'></i></div>",
            "<div class='landing-nav-content'>",
            "<div class='landing-nav-text'>Recherche</div>",
            "<div class='landing-nav-desc'>Filtrez et cherchez des transactions spécifiques</div>",
            "</div>",
            "</div>",
            "</button>",
            "</form>",
        ]), unsafe_allow_html=True)

    with col6:
        st.markdown("\n".join([
            "<form class='landing-card-form' method='get'>",
            "<input type='hidden' name='nav' value='À propos' />",
            "<button type='submit' class='landing-card-button'>",
            "<div class='landing-nav-item'>",
            "<div class='landing-nav-icon'><i class='fa-solid fa-star'></i></div>",
            "<div class='landing-nav-content'>",
            "<div class='landing-nav-text'>À propos</div>",
            "<div class='landing-nav-desc'>Informations sur le projet et ses sources</div>",
            "</div>",
            "</div>",
            "</button>",
            "</form>",
        ]), unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1.5, 1, 1.5])
    with col2:
        if st.button("Accéder au Dashboard", use_container_width=True, key="btn-start"):
            st.session_state["nav"] = "Accueil"
            st.session_state["show_splash"] = False
            st.rerun()

