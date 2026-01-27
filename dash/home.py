"""Page d'accueil et graphiques pour DVF Paris Analytics."""


import pandas as pd
import plotly.express as px
import streamlit as st

from dash import layout
from dash.layout import PRIMARY_COLOR, SECONDARY_COLOR, styliser_fig




def _ensure_data(df):
    """Vérifie que le DataFrame n'est pas vide et affiche un avertissement."""
    if df.empty:
        st.warning("Aucune donnee disponible. Lancez d'abord le scraper.")
        return False
    return True




def afficher_kpis(df):
    """affiche les indicateurs cles."""
    prix_moyen = df["valeur_fonciere"].mean()
    prix_m2_median = df["prix_m2"].median()
    surface_moyenne = df["surface_reelle_bati"].mean()
    seuil_grosse_vente = df["valeur_fonciere"].quantile(0.95)
    nb_grosses = len(df[df["valeur_fonciere"] >= seuil_grosse_vente])

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #7c5295 0%, #9575b3 100%); padding: 15px; border-radius: 10px; text-align: center; height: 110px; display: flex; flex-direction: column; align-items: center; justify-content: center;'>
            <h4 style='color: white; margin: 0 0 8px 0; font-size: 14px;'>Transactions</h4>
            <h2 style='color: white; margin: 0; font-size: 28px;'>{len(df):,}</h2>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #4b8ba6 0%, #6aa6bb 100%); padding: 15px; border-radius: 10px; text-align: center; height: 110px; display: flex; flex-direction: column; align-items: center; justify-content: center;'>
            <h4 style='color: white; margin: 0 0 8px 0; font-size: 14px;'>Prix moyen</h4>
            <h2 style='color: white; margin: 0; font-size: 28px;'>{prix_moyen/1e6:.2f}M€</h2>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #5a9a6f 0%, #78b38a 100%); padding: 15px; border-radius: 10px; text-align: center; height: 110px; display: flex; flex-direction: column; align-items: center; justify-content: center;'>
            <h4 style='color: white; margin: 0 0 8px 0; font-size: 14px;'>Prix m² médian</h4>
            <h2 style='color: white; margin: 0; font-size: 28px;'>{prix_m2_median:,.0f}€</h2>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #c17a4a 0%, #d99668 100%); padding: 15px; border-radius: 10px; text-align: center; height: 110px; display: flex; flex-direction: column; align-items: center; justify-content: center;'>
            <h4 style='color: white; margin: 0 0 8px 0; font-size: 14px;'>Surface moyenne</h4>
            <h2 style='color: white; margin: 0; font-size: 28px;'>{surface_moyenne:.0f}m²</h2>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #b05d7a 0%, #c77a95 100%); padding: 15px; border-radius: 10px; text-align: center; height: 110px; display: flex; flex-direction: column; align-items: center; justify-content: center;'>
            <h4 style='color: white; margin: 0 0 8px 0; font-size: 14px;'>Grosses ventes (top 5%)</h4>
            <h2 style='color: white; margin: 0; font-size: 28px;'>{nb_grosses}</h2>
        </div>
        """, unsafe_allow_html=True)




def graphique_timeline(df):
    """Bar chart du volume de transactions par mois."""
    if df.empty:
        return None


    ts = df.copy()
    ts["mois"] = ts["date_mutation"].dt.to_period("M").astype(str)
    agg = ts.groupby("mois").size().reset_index(name="nb_transactions")


    fig = px.bar(
        agg,
        x="mois",
        y="nb_transactions",
        title="Évolution mensuelle du volume de transactions immobilières à Paris",
        labels={"mois": "Mois", "nb_transactions": "Nombre de transactions"},
    )
    fig.update_layout(xaxis_tickangle=-45)
    fig.update_traces(
        marker_color=PRIMARY_COLOR,
        marker_line_color='rgba(255,255,255,0.2)',
        marker_line_width=1,
        hovertemplate='<b>%{x}</b><br>Transactions: %{y:,.0f}<extra></extra>'
    )
    return styliser_fig(fig)




def graphique_grosses_ventes(df, seuil_percentile=95):
    """Scatter des grosses ventes (au-dessus d'un seuil percentile)."""
    if df.empty:
        return None


    seuil = df["valeur_fonciere"].quantile(seuil_percentile / 100)
    grosses_ventes = df[df["valeur_fonciere"] >= seuil].copy()


    fig = px.scatter(
        grosses_ventes,
        x="date_mutation",
        y="valeur_fonciere",
        color="arrondissement",
        size="surface_reelle_bati",
        hover_data=["type_local", "prix_m2"],
        title=f"Transactions les plus importantes par arrondissement (seuil: {seuil/1e6:.1f}M€)",
        labels={
            "date_mutation": "Date de la transaction",
            "valeur_fonciere": "Prix de vente (€)",
            "arrondissement": "Arrondissement",
        },
        color_discrete_sequence=["#7c5295", "#4b8ba6", "#5a9a6f", "#c17a4a", "#b05d7a", "#4a9a9a", "#8c6bb1", "#6ba3b8", "#70ad82", "#cf8f5c", "#c07090", "#5cafaf", "#9775c2", "#7eb5ca", "#85bf94", "#dda46e", "#ce83a5", "#6ec4c4", "#a280d0", "#8fc7dc"],
        height=500
    )
    fig.update_traces(
        marker={
            "opacity": 0.7,
            "line": {"width": 1, "color": "white"}
        }
    )
    return styliser_fig(fig)




def graphique_prix_arrondissement(df):
    """Bar chart du prix médian par arrondissement."""
    if df.empty:
        return None


    agg = df.groupby("arrondissement").agg({
        "valeur_fonciere": "median",
        "prix_m2": "median",
    }).reset_index()
    agg["arr_num"] = pd.to_numeric(agg["arrondissement"], errors="coerce")
    agg = agg.sort_values("arr_num")


    fig = px.bar(
        agg,
        x="arrondissement",
        y="valeur_fonciere",
        title="Prix médian de vente par arrondissement parisien",
        labels={"arrondissement": "Arrondissement", "valeur_fonciere": "Prix médian (€)"},
        color="valeur_fonciere",
        color_continuous_scale="Viridis",
        text="valeur_fonciere"
    )
    fig.update_traces(
        marker_line_width=0,
        texttemplate='%{text:,.0f}€',
        textposition='outside',
        hovertemplate='<b>Arr. %{x}</b><br>Prix: %{y:,.0f}€<extra></extra>'
    )
    return styliser_fig(fig)




def graphique_evolution_prix(df):
    """Courbe d'évolution du prix médian au m²."""
    if df.empty:
        return None


    ts = df.copy()
    ts["mois"] = ts["date_mutation"].dt.to_period("M").astype(str)


    agg = ts.groupby("mois").agg({"valeur_fonciere": "median", "prix_m2": "median"}).reset_index()


    fig = px.line(
        agg,
        x="mois",
        y="prix_m2",
        title="Évolution temporelle du prix médian au m² à Paris",
        labels={"mois": "Mois", "prix_m2": "Prix médian/m² (€)"},
        markers=True,
    )
    fig.update_layout(xaxis_tickangle=-45)
    fig.update_traces(
        line_width=4,
        line_color=SECONDARY_COLOR,
        marker={"size": 8, "color": PRIMARY_COLOR, "line": {"width": 2, "color": "white"}},
        hovertemplate='<b>%{x}</b><br>Prix/m²: %{y:,.0f}€<extra></extra>'
    )
    return styliser_fig(fig)




def graphique_prix_m2(df):
    """Boîte à moustaches du prix/m² par arrondissement."""
    if df.empty:
        return None


    df_filtre = df[(df["prix_m2"] > 1000) & (df["prix_m2"] < 50000)].copy()

    # Trier par ordre d'arrondissement
    df_filtre["arr_num"] = pd.to_numeric(df_filtre["arrondissement"], errors="coerce")
    df_filtre = df_filtre.sort_values("arr_num")


    fig = px.box(
        df_filtre,
        x="arrondissement",
        y="prix_m2",
        color="arrondissement",
        title="Distribution statistique du prix au m² par arrondissement parisien",
        labels={"arrondissement": "Arrondissement", "prix_m2": "Prix/m² (€)"},
        category_orders={"arrondissement": sorted(df_filtre["arrondissement"].unique(), key=lambda x: int(x) if str(x).isdigit() else 0)}
    )
    fig.update_layout(showlegend=False)
    fig.update_traces(
        marker={"opacity": 0.6, "size": 3},
        line={"width": 2}
    )
    return styliser_fig(fig)




def graphique_type_bien(df):
    """Prix médian par type de bien avec comptage en texte."""
    if df.empty:
        return None


    agg = df.groupby("type_local").agg({
        "valeur_fonciere": ["median", "count"],
        "prix_m2": "median",
    }).reset_index()
    agg.columns = ["type_local", "prix_median", "nb_ventes", "prix_m2_median"]


    fig = px.bar(
        agg,
        x="type_local",
        y="prix_median",
        color="type_local",
        title="Prix médian de vente selon le type de bien immobilier",
        labels={"type_local": "Type de bien", "prix_median": "Prix médian (€)", "nb_ventes": "Nombre de ventes"},
        text="nb_ventes",
        color_discrete_sequence=["#7c5295", "#4b8ba6", "#5a9a6f", "#c17a4a", "#b05d7a", "#4a9a9a"],
        height=450
    )
    fig.update_layout(showlegend=False)
    fig.update_traces(
        textposition="outside",
        marker_line_width=0,
        texttemplate='%{text:,.0f}',
        hovertemplate='<b>%{x}</b><br>Prix: %{y:,.0f}€<br>Ventes: %{text}<extra></extra>'
    )
    return styliser_fig(fig)




def graphique_nature_mutation(df):
    """Répartition des natures de mutation (camembert)."""
    if df.empty:
        return None


    agg = df.groupby("nature_mutation").size().reset_index(name="count")


    fig = px.pie(
        agg,
        values="count",
        names="nature_mutation",
        title="Répartition des transactions par type de mutation",
        hole=0.4,
        height=400,
        color_discrete_sequence=[
            "#7c5295",  # violet doux
            "#4b8ba6",  # bleu canard doux
            "#5a9a6f",  # vert doux
            "#c17a4a",  # orange doux
            "#b05d7a",  # rose doux
            "#4a9a9a",  # turquoise doux
        ]
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        textfont_size=11,
        marker={"line": {"width": 0}},
        hovertemplate=
        '<b>%{label}</b><br>Nombre: %{value:,.0f}<br>Pourcentage: %{percent}<extra></extra>'
    )
    return styliser_fig(fig)




def render_home(df):
    """page d'accueil epuree pour accueillir l'utilisateur."""

    # CSS et HTML pour la page d'accueil
    st.markdown("""
    <link rel='stylesheet' href='https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'>
    <style>
    .landing-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 60vh;
        padding: 2rem;
    }
    .landing-title {
        font-family: "Poppins", sans-serif;
        font-weight: 700;
        font-size: 2.8rem;
        color: #3d2817;
        text-align: center;
        margin-bottom: 3rem;
        line-height: 1.3;
    }
    .landing-nav {
        display: flex;
        flex-direction: column;
        gap: 1rem;
        width: 100%;
        max-width: 600px;
    }
    .landing-nav-item {
        background: linear-gradient(135deg, #f5f1e8 0%, #e6dfd4 100%);
        padding: 1.3rem 2rem;
        border-radius: 12px;
        border: 2px solid #d4c5b0;
        display: flex;
        align-items: center;
        gap: 1.2rem;
        transition: all 0.2s;
    }
    .landing-nav-item:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.08);
        border-color: #0f766e;
    }
    .landing-nav-icon {
        font-size: 1.8rem;
        color: #3d2817;
        min-width: 40px;
        text-align: center;
    }
    .landing-nav-content {
        flex: 1;
    }
    .landing-nav-text {
        font-size: 1.2rem;
        font-weight: 600;
        color: #3d2817;
        margin: 0;
    }
    .landing-nav-desc {
        font-size: 0.85rem;
        color: #666;
        margin: 0.2rem 0 0 0;
    }
    .landing-arrow {
        position: fixed;
        bottom: 2.5rem;
        right: 2.5rem;
        width: 55px;
        height: 55px;
        background: linear-gradient(135deg, #0f766e 0%, #14b8a6 100%);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 1000;
    }
    .landing-arrow i {
        color: white;
        font-size: 1.3rem;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class='landing-container'>
        <div class='landing-title'>
            Dashboard Transactions Immobilières<br>à Paris
        </div>
        <div class='landing-nav'>
            <div class='landing-nav-item' id='nav-trans'>
                <div class='landing-nav-icon'><i class='fa-solid fa-building'></i></div>
                <div class='landing-nav-content'>
                    <div class='landing-nav-text'>Transactions</div>
                    <div class='landing-nav-desc'>Explorez les ventes immobilieres</div>
                </div>
            </div>
            <div class='landing-nav-item' id='nav-prix'>
                <div class='landing-nav-icon'><i class='fa-solid fa-euro-sign'></i></div>
                <div class='landing-nav-content'>
                    <div class='landing-nav-text'>Prix</div>
                    <div class='landing-nav-desc'>Analysez les prix au m2</div>
                </div>
            </div>
            <div class='landing-nav-item' id='nav-carte'>
                <div class='landing-nav-icon'><i class='fa-solid fa-map'></i></div>
                <div class='landing-nav-content'>
                    <div class='landing-nav-text'>Carte</div>
                    <div class='landing-nav-desc'>Visualisez les donnees geographiques</div>
                </div>
            </div>
            <div class='landing-nav-item' id='nav-rech'>
                <div class='landing-nav-icon'><i class='fa-solid fa-magnifying-glass'></i></div>
                <div class='landing-nav-content'>
                    <div class='landing-nav-text'>Recherche</div>
                    <div class='landing-nav-desc'>Trouvez des transactions specifiques</div>
                </div>
            </div>
            <div class='landing-nav-item' id='nav-about'>
                <div class='landing-nav-icon'><i class='fa-solid fa-star'></i></div>
                <div class='landing-nav-content'>
                    <div class='landing-nav-text'>A propos</div>
                    <div class='landing-nav-desc'>Informations sur le projet</div>
                </div>
            </div>
        </div>
    </div>
    <div class='landing-arrow'>
        <i class='fa-solid fa-arrow-right'></i>
    </div>
    """, unsafe_allow_html=True)

    # Boutons invisibles pour la navigation
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("Transactions", key="nav-btn-trans", help="Voir les transactions"):
            st.session_state["nav"] = "Transactions"
            st.rerun()
        if st.button("Prix", key="nav-btn-prix", help="Voir les prix"):
            st.session_state["nav"] = "Prix"
            st.rerun()
    with col2:
        if st.button("Carte", key="nav-btn-carte", help="Voir la carte"):
            st.session_state["nav"] = "Carte"
            st.rerun()
        if st.button("Recherche", key="nav-btn-rech", help="Rechercher"):
            st.session_state["nav"] = "Recherche"
            st.rerun()
    with col3:
        if st.button("A propos", key="nav-btn-about", help="A propos"):
            st.session_state["nav"] = "À propos"
            st.rerun()
        if st.button("Commencer", key="nav-btn-arrow", help="Commencer"):
            st.session_state["nav"] = "Transactions"
            st.rerun()




def render_transactions(df):
    """section transactions: volume, grosses ventes et repartition."""
    if not _ensure_data(df):
        return

    # layout: filtres a gauche, contenu a droite
    col_filtre, col_contenu = st.columns([1, 3])

    with col_filtre:
        df_filtre = layout.render_filters_sidebar(df, show_percentile=True)

    with col_contenu:

        # kpis specifiques aux transactions
        afficher_kpis(df_filtre)

        st.markdown("<br>", unsafe_allow_html=True)

        col1, col2 = st.columns([3, 2])
        with col1:
            fig = graphique_timeline(df_filtre)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = graphique_nature_mutation(df_filtre)
            if fig:
                st.plotly_chart(fig, use_container_width=True)

        fig = graphique_grosses_ventes(df_filtre, 95)
        if fig:
            st.plotly_chart(fig, use_container_width=True)




def render_prix(df):
    """section prix: median par arrondissement, evolution et distribution."""
    if not _ensure_data(df):
        return

    # layout: filtres a gauche, contenu a droite
    col_filtre, col_contenu = st.columns([1, 3])

    with col_filtre:
        df_filtre = layout.render_filters_sidebar(df, show_percentile=False)

    with col_contenu:

        # kpis prix
        prix_min = df_filtre["valeur_fonciere"].min()
        prix_q1 = df_filtre["valeur_fonciere"].quantile(0.25)
        prix_q3 = df_filtre["valeur_fonciere"].quantile(0.75)
        prix_max = df_filtre["valeur_fonciere"].max()

        col_k1, col_k2, col_k3, col_k4 = st.columns(4)

        with col_k1:
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #4b8ba6 0%, #6aa6bb 100%); padding: 15px; border-radius: 10px; text-align: center; height: 110px; display: flex; flex-direction: column; align-items: center; justify-content: center;'>
                <h4 style='color: white; margin: 0 0 8px 0; font-size: 14px;'>Prix min</h4>
                <h2 style='color: white; margin: 0; font-size: 28px;'>{prix_min/1e6:.2f}M€</h2>
            </div>
            """, unsafe_allow_html=True)

        with col_k2:
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #5a9a6f 0%, #78b38a 100%); padding: 15px; border-radius: 10px; text-align: center; height: 110px; display: flex; flex-direction: column; align-items: center; justify-content: center;'>
                <h4 style='color: white; margin: 0 0 8px 0; font-size: 14px;'>Q1 (25%)</h4>
                <h2 style='color: white; margin: 0; font-size: 28px;'>{prix_q1/1e6:.2f}M€</h2>
            </div>
            """, unsafe_allow_html=True)

        with col_k3:
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #c17a4a 0%, #d99668 100%); padding: 15px; border-radius: 10px; text-align: center; height: 110px; display: flex; flex-direction: column; align-items: center; justify-content: center;'>
                <h4 style='color: white; margin: 0 0 8px 0; font-size: 14px;'>Q3 (75%)</h4>
                <h2 style='color: white; margin: 0; font-size: 28px;'>{prix_q3/1e6:.2f}M€</h2>
            </div>
            """, unsafe_allow_html=True)

        with col_k4:
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #b05d7a 0%, #c77a95 100%); padding: 15px; border-radius: 10px; text-align: center; height: 110px; display: flex; flex-direction: column; align-items: center; justify-content: center;'>
                <h4 style='color: white; margin: 0 0 8px 0; font-size: 14px;'>Prix max</h4>
                <h2 style='color: white; margin: 0; font-size: 28px;'>{prix_max/1e6:.2f}M€</h2>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            fig = graphique_prix_arrondissement(df_filtre)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = graphique_evolution_prix(df_filtre)
            if fig:
                st.plotly_chart(fig, use_container_width=True)

        fig = graphique_prix_m2(df_filtre)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

        fig = graphique_type_bien(df_filtre)
        if fig:
            st.plotly_chart(fig, use_container_width=True)


