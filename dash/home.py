"""Dashboard pages: home, transactions, price analysis and charts."""
import pandas as pd
import plotly.express as px
import streamlit as st

from dash.layout import PRIMARY_COLOR, SECONDARY_COLOR, styliser_fig


def _ensure_data(df):
    """Vérifie que le dataframe contient des données, sinon affiche un message."""
    if df.empty:
        st.warning("Aucune donnee disponible. Lancez d'abord le scraper.")
        return False
    return True


def afficher_kpis(df):
    """Affiche les indicateurs clés avec design premium et animations."""
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(
            f"""
            <div style='background: linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%);
                        padding: 1.5rem; border-radius: 12px; text-align: center;
                        box-shadow: 0 4px 16px rgba(14, 165, 233, 0.4);
                        transition: transform 0.2s;'>
                <div style='font-size: 0.85rem; color: #e0f2fe; font-weight: 500;
                            margin-bottom: 0.5rem;'>Transactions</div>
                <div style='font-size: 2.2rem; font-weight: 800; color: white;'>
                    {len(df):,}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        prix_moyen = df["valeur_fonciere"].mean()
        st.markdown(
            f"""
            <div style='background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
                        padding: 1.5rem; border-radius: 12px; text-align: center;
                        box-shadow: 0 4px 16px rgba(37, 99, 235, 0.4);'>
                <div style='font-size: 0.85rem; color: #dbeafe; font-weight: 500; margin-bottom: 0.5rem;'>Prix moyen</div>
                <div style='font-size: 2.2rem; font-weight: 800; color: white;'>
                    {prix_moyen/1e6:.2f}M€
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        prix_m2_median = df["prix_m2"].median()
        st.markdown(
            f"""
            <div style='background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
                        padding: 1.5rem; border-radius: 12px; text-align: center;
                        box-shadow: 0 4px 16px rgba(6, 182, 212, 0.4);'>
                <div style='font-size: 0.85rem; color: #cffafe; font-weight: 500;
                            margin-bottom: 0.5rem;'>
                    Prix m² médian
                </div>
                <div style='font-size: 2.2rem; font-weight: 800; color: white;'>
                    {prix_m2_median:,.0f}€
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:
        surface_moyenne = df["surface_reelle_bati"].mean()
        st.markdown(
            f"""
            <div style='background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
                        padding: 1.5rem; border-radius: 12px; text-align: center;
                        box-shadow: 0 4px 16px rgba(2, 132, 199, 0.4);'>
                <div style='font-size: 0.85rem; color: #bae6fd; font-weight: 500;
                            margin-bottom: 0.5rem;'>
                    Surface moyenne
                </div>
                <div style='font-size: 2.2rem; font-weight: 800; color: white;'>
                    {surface_moyenne:.0f}m²
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col5:
        seuil_grosse_vente = df["valeur_fonciere"].quantile(0.95)
        nb_grosses = len(df[df["valeur_fonciere"] >= seuil_grosse_vente])
        st.markdown(
            f"""
            <div style='background: linear-gradient(135deg, #0c4a6e 0%, #075985 100%);
                        padding: 1.5rem; border-radius: 12px; text-align: center;
                        box-shadow: 0 4px 16px rgba(12, 74, 110, 0.4);'>
                <div style='font-size: 0.85rem; color: #bae6fd; font-weight: 500; margin-bottom: 0.5rem;'>Grosses ventes</div>
                <div style='font-size: 2.2rem; font-weight: 800; color: white;'>{nb_grosses}</div>
                <div style='font-size: 0.7rem; color: #bae6fd; margin-top: 0.3rem;'>Top 5%</div>
            </div>
            """,
            unsafe_allow_html=True
        )


def graphique_timeline(df):
    """Bar chart du nombre de transactions par mois."""
    if df.empty:
        return None

    ts = df.copy()
    ts["mois"] = ts["date_mutation"].dt.to_period("M").astype(str)
    agg = ts.groupby("mois").size().reset_index(name="nb_transactions")

    fig = px.bar(
        agg,
        x="mois",
        y="nb_transactions",
        title="Nombre de transactions par mois",
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
    """Scatter des grosses ventes au-dessus d'un seuil percentile."""
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
        title=f"Grosses ventes (> {seuil/1e6:.1f}M€ - top {100-seuil_percentile}%)",
        labels={
            "date_mutation": "Date",
            "valeur_fonciere": "Prix (€)",
            "arrondissement": "Arr.",
        },
    )
    fig.update_traces(
        marker={
            "opacity": 0.8,
            "line": {"width": 1, "color": "white"},
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
        title="Prix médian par arrondissement",
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
    """Courbe d'évolution du prix médian au m² par mois."""
    if df.empty:
        return None

    ts = df.copy()
    ts["mois"] = ts["date_mutation"].dt.to_period("M").astype(str)

    agg = ts.groupby("mois").agg({"valeur_fonciere": "median", "prix_m2": "median"}).reset_index()

    fig = px.line(
        agg,
        x="mois",
        y="prix_m2",
        title="Évolution du prix médian au m²",
        labels={"mois": "Mois", "prix_m2": "Prix médian/m² (€)"},
        markers=True,
    )
    fig.update_layout(xaxis_tickangle=-45)
    fig.update_traces(
        line_width=4,
        line_color=SECONDARY_COLOR,
        marker={
            "size": 8,
            "color": PRIMARY_COLOR,
            "line": {"width": 2, "color": "white"},
        },
        hovertemplate='<b>%{x}</b><br>Prix/m²: %{y:,.0f}€<extra></extra>'
    )
    return styliser_fig(fig)


def graphique_prix_m2(df):
    """Box plot du prix/m² par arrondissement."""
    if df.empty:
        return None

    df_filtre = df[(df["prix_m2"] > 1000) & (df["prix_m2"] < 50000)].copy()

    fig = px.box(
        df_filtre,
        x="arrondissement",
        y="prix_m2",
        color="arrondissement",
        title="Distribution du prix/m² par arrondissement",
        labels={"arrondissement": "Arrondissement", "prix_m2": "Prix/m² (€)"},
    )
    fig.update_layout(showlegend=False)
    fig.update_traces(
        marker={"opacity": 0.6, "size": 3},
        line={"width": 2}
    )
    return styliser_fig(fig)


def graphique_type_bien(df):
    """Bar chart du prix médian et nombre de ventes par type de bien."""
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
        color="nb_ventes",
        title="Prix médian par type de bien",
        labels={"type_local": "Type", "prix_median": "Prix médian (€)", "nb_ventes": "Nb ventes"},
        text="nb_ventes",
        color_continuous_scale="Viridis",
        height=750
    )
    fig.update_traces(
        textposition="outside",
        marker_line_width=0,
        texttemplate='%{text:,.0f}',
        hovertemplate='<b>%{x}</b><br>Prix: %{y:,.0f}€<br>Ventes: %{text}<extra></extra>'
    )
    return styliser_fig(fig)


def graphique_nature_mutation(df):
    """Camembert de la répartition par nature de mutation."""
    if df.empty:
        return None

    agg = df.groupby("nature_mutation").size().reset_index(name="count")

    fig = px.pie(
        agg,
        values="count",
        names="nature_mutation",
        title="Répartition par type de vente",
        hole=0.4,
        color_discrete_sequence=[
            "#0ea5e9",  # blue
            "#2563eb",  # royal blue
            "#6d28d9",  # violet
            "#8b5cf6",  # light violet
            "#10b981",  # green
            "#22c55e",  # bright green
        ]
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        textfont_size=13,
        marker={"line": {"color": "white", "width": 2}},
        hovertemplate='<b>%{label}</b><br>Nombre: '
        '%{value:,.0f}<br>Pourcentage: %{percent}<extra></extra>'
    )
    return styliser_fig(fig)


def render_home(df, _filters):
    """Page d'accueil: vue d'ensemble avec design moderne."""
    # Hero section
    st.markdown(
        """
        <div style='background: linear-gradient(135deg, #0c4a6e 0%, #0369a1 50%,
                    #0ea5e9 100%);
                    padding: 3rem 2rem; border-radius: 16px; margin-bottom: 2rem;
                    box-shadow: 0 8px 32px rgba(14, 165, 233, 0.4); text-align: center;'>
            <h1 style='color: white; font-size: 2.5rem; margin: 0; font-weight: 800;
                       text-shadow: 0 2px 8px rgba(0,0,0,0.3);'>
                Bienvenue sur DVF Paris Analytics
            </h1>
            <p style='color: #e0f2fe; font-size: 1.2rem; margin-top: 1rem; font-weight: 400;'>
                Analyse intelligente des transactions immobilières parisiennes
            </p>
            <div style='margin-top: 1.5rem;'>
                <span style='background: rgba(255,255,255,0.2); padding: 0.5rem 1rem;
                            border-radius: 20px; color: white; font-size: 0.9rem;
                            margin: 0 0.5rem;'>
                    API DVF+ Cerema
                </span>
                <span style='background: rgba(255,255,255,0.2); padding: 0.5rem 1rem;
                            border-radius: 20px; color: white; font-size: 0.9rem;
                            margin: 0 0.5rem;'>
                    Elasticsearch
                </span>
                <span style='background: rgba(255,255,255,0.2); padding: 0.5rem 1rem;
                            border-radius: 20px; color: white; font-size: 0.9rem;
                            margin: 0 0.5rem;'>
                    20 Arrondissements
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    # KPIs améliorés
    afficher_kpis(df)
    st.markdown("<br>", unsafe_allow_html=True)
    # Fonctionnalités en cartes
    st.markdown("### Explorez les données")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            """
            <div style='background: linear-gradient(135deg, #0f2f4f 0%, #1a3a52 100%);
                        padding: 1.5rem; border-radius: 12px; border: 1px solid #0ea5e9;
                        box-shadow: 0 4px 12px rgba(14, 165, 233, 0.2); height: 180px;'>
                <div style='color: #0ea5e9; font-weight: 800; font-size: 1.3rem;
                            margin-bottom: 0.3rem;'>
                    Transactions
                </div>
                <div style='color: #94a3b8; font-size: 0.85rem; margin-top: 0.5rem;'>
                    Volume mensuel, grosses ventes et tendances temporelles
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            """
            <div style='background: linear-gradient(135deg, #0f2f4f 0%, #1a3a52 100%);
                        padding: 1.5rem; border-radius: 12px; border: 1px solid #06b6d4;
                        box-shadow: 0 4px 12px rgba(6, 182, 212, 0.2); height: 180px;'>
                <div style='color: #0ea5e9; font-weight: 800; font-size: 1.3rem;
                            margin-bottom: 0.3rem;'>
                    Analyse Prix
                </div>
                <div style='color: #94a3b8; font-size: 0.85rem; margin-top: 0.5rem;'>
                    Médianes, évolution et distribution par arrondissement
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            """
            <div style='background: linear-gradient(135deg, #0f2f4f 0%, #1a3a52 100%);
                        padding: 1.5rem; border-radius: 12px; border: 1px solid #2563eb;
                        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2); height: 180px;'>
                <div style='color: #0ea5e9; font-weight: 800; font-size: 1.3rem;
                            margin-bottom: 0.3rem;'>
                    Carte Interactive
                </div>
                <div style='color: #94a3b8; font-size: 0.85rem; margin-top: 0.5rem;'>
                    Visualisation géographique et choroplèthe
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col4:
        st.markdown(
            """
            <div style='background: linear-gradient(135deg, #0f2f4f 0%, #1a3a52 100%);
                        padding: 1.5rem; border-radius: 12px; border: 1px solid #0891b2;
                        box-shadow: 0 4px 12px rgba(8, 145, 178, 0.2); height: 180px;'>
                <div style='color: #0ea5e9; font-weight: 800; font-size: 1.3rem;
                            margin-bottom: 0.3rem;'>
                    Recherche IA
                </div>
                <div style='color: #94a3b8; font-size: 0.85rem; margin-top: 0.5rem;'>
                    Moteur Elasticsearch avec fuzzy matching
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    st.markdown("<br>", unsafe_allow_html=True)
    # Instructions stylisées
    st.markdown(
        """
        <div style='background: linear-gradient(90deg, #0f2f4f 0%, #1a3a52 100%);
                    padding: 1.5rem; border-radius: 12px; margin-top: 1.5rem;
                    border-left: 4px solid #0ea5e9;'>
            <div style='color: #0ea5e9; font-weight: 700; font-size: 1.2rem;
                        margin-bottom: 1rem;'>
                Guide rapide
            </div>
            <div style='color: #cbd5e1;'>
                <div style='margin-bottom: 0.5rem;'>
                    <strong>Navigation:</strong> Utilisez les onglets ci-dessus pour
                    explorer les différentes vues
                </div>
                <div style='margin-bottom: 0.5rem;'>
                    <strong>Filtres:</strong> Sidebar à gauche pour affiner par date,
                    arrondissement, type et prix
                </div>
                <div style='margin-bottom: 0.5rem;'>
                    <strong>Recherche:</strong> Trouvez des transactions spécifiques
                    avec le moteur Elasticsearch
                </div>
                <div>
                    <strong>Visualisations:</strong> 7 graphiques interactifs + cartes
                    géolocalisées
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_transactions(df, filters):
    """Section transactions: KPIs, timeline, grosses ventes et répartition."""
    if not _ensure_data(df):
        return

    # En-tête de section
    st.markdown(
        """
        <div style='background: linear-gradient(135deg, #0f2f4f 0%, #1a3a52 100%);
                    padding: 1.2rem; border-radius: 12px; margin-bottom: 1.5rem;
                    border: 1px solid #0ea5e9;'>
            <h2 style='color: #0ea5e9; margin: 0;'> Analyse des Transactions</h2>
        </div>
        """,
        unsafe_allow_html=True
    )
    # KPIs spécifiques aux transactions
    afficher_kpis(df)
    st.markdown("<br>", unsafe_allow_html=True)
    seuil_percentile = filters.get("seuil_percentile", 95)

    col1, col2 = st.columns([2, 1])
    with col1:
        fig = graphique_timeline(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = graphique_grosses_ventes(df, seuil_percentile)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    fig = graphique_nature_mutation(df)
    if fig:
        st.plotly_chart(fig, use_container_width=True)


def render_prix(df):
    """Section prix: KPIs et analyses de prix par plusieurs graphiques."""
    if not _ensure_data(df):
        return
    # En-tête de section
    st.markdown(
        """
        <div style='background: linear-gradient(135deg, #0f2f4f 0%, #1a3a52 100%);
                    padding: 1.2rem; border-radius: 12px; margin-bottom: 1.5rem;
                    border: 1px solid #0ea5e9;'>
            <h2 style='color: #0ea5e9; margin: 0;'> Analyse des Prix</h2>
        </div>
        """,
        unsafe_allow_html=True
    )
    # KPIs prix
    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    with col_k1:
        prix_min = df["valeur_fonciere"].min()
        st.markdown(
            f"""
            <div style='background: linear-gradient(135deg, #059669 0%, #10b981 100%);
                        padding: 1.2rem; border-radius: 10px; text-align: center;
                        box-shadow: 0 4px 12px rgba(5, 150, 105, 0.3);'>
                <div style='font-size: 0.75rem; color: #d1fae5; margin-bottom: 0.3rem;'>
                    MIN
                </div>
                <div style='font-size: 1.5rem; font-weight: 700; color: white;'>
                    {prix_min/1e6:.2f}M€
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_k2:
        prix_q1 = df["valeur_fonciere"].quantile(0.25)
        st.markdown(
            f"""
            <div style='background: linear-gradient(135deg, #0891b2 0%, #06b6d4 100%);
                        padding: 1.2rem; border-radius: 10px; text-align: center;
                        box-shadow: 0 4px 12px rgba(8, 145, 178, 0.3);'>
                <div style='font-size: 0.75rem; color: #cffafe; margin-bottom: 0.3rem;'>
                    Q1 (25%)
                </div>
                <div style='font-size: 1.5rem; font-weight: 700; color: white;'>
                    {prix_q1/1e6:.2f}M€
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_k3:
        prix_q3 = df["valeur_fonciere"].quantile(0.75)
        st.markdown(
            f"""
            <div style='background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
                        padding: 1.2rem; border-radius: 10px; text-align: center;
                        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);'>
                <div style='font-size: 0.75rem; color: #dbeafe; margin-bottom: 0.3rem;'>
                    Q3 (75%)
                </div>
                <div style='font-size: 1.5rem; font-weight: 700; color: white;'>
                    {prix_q3/1e6:.2f}M€
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_k4:
        prix_max = df["valeur_fonciere"].max()
        st.markdown(
            f"""
            <div style='background: linear-gradient(135deg, #6d28d9 0%, #8b5cf6 100%);
                        padding: 1.2rem; border-radius: 10px; text-align: center;
                        box-shadow: 0 4px 12px rgba(109, 40, 217, 0.3);'>
                <div style='font-size: 0.75rem; color: #ede9fe; margin-bottom: 0.3rem;'>
                    MAX
                </div>
                <div style='font-size: 1.5rem; font-weight: 700; color: white;'>
                    {prix_max/1e6:.2f}M€
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        fig = graphique_prix_arrondissement(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = graphique_evolution_prix(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns([1, 1])
    with col3:
        fig = graphique_prix_m2(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with col4:
        fig = graphique_type_bien(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
