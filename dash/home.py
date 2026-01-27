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
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Transactions", f"{len(df):,}")

    with col2:
        prix_moyen = df["valeur_fonciere"].mean()
        st.metric("Prix moyen", f"{prix_moyen/1e6:.2f}M€")

    with col3:
        prix_m2_median = df["prix_m2"].median()
        st.metric("Prix m² médian", f"{prix_m2_median:,.0f}€")

    with col4:
        surface_moyenne = df["surface_reelle_bati"].mean()
        st.metric("Surface moyenne", f"{surface_moyenne:.0f}m²")

    with col5:
        seuil_grosse_vente = df["valeur_fonciere"].quantile(0.95)
        nb_grosses = len(df[df["valeur_fonciere"] >= seuil_grosse_vente])
        st.metric("Grosses ventes (top 5%)", nb_grosses)




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
        title="Évolution du prix médian au m²",
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
    """Répartition des natures de mutation (camembert)."""
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
        hovertemplate=
        '<b>%{label}</b><br>Nombre: %{value:,.0f}<br>Pourcentage: %{percent}<extra></extra>'
    )
    return styliser_fig(fig)




def render_home(df):
    """page d'accueil: vue d'ensemble."""

    # layout: filtres a gauche, contenu a droite
    col_filtre, col_contenu = st.columns([1, 3])

    with col_filtre:
        df_filtre = layout.render_filters_sidebar(df, show_percentile=False)

    with col_contenu:
        st.markdown("## Vue d'ensemble")
        st.markdown("---")

        # kpis
        afficher_kpis(df_filtre)




def render_transactions(df):
    """section transactions: volume, grosses ventes et repartition."""
    if not _ensure_data(df):
        return

    # layout: filtres a gauche, contenu a droite
    col_filtre, col_contenu = st.columns([1, 3])

    with col_filtre:
        df_filtre = layout.render_filters_sidebar(df, show_percentile=True)

    with col_contenu:
        st.markdown("## Analyse des transactions")
        st.markdown("---")

        # kpis specifiques aux transactions
        afficher_kpis(df_filtre)

        st.markdown("<br>", unsafe_allow_html=True)

        col1, col2 = st.columns([2, 1])
        with col1:
            fig = graphique_timeline(df_filtre)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = graphique_grosses_ventes(df_filtre, 95)
            if fig:
                st.plotly_chart(fig, use_container_width=True)

        fig = graphique_nature_mutation(df_filtre)
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
        st.markdown("## Analyse des prix")
        st.markdown("---")

        # kpis prix
        col_k1, col_k2, col_k3, col_k4 = st.columns(4)

        with col_k1:
            prix_min = df_filtre["valeur_fonciere"].min()
            st.metric("Prix min", f"{prix_min/1e6:.2f}M€")

        with col_k2:
            prix_q1 = df_filtre["valeur_fonciere"].quantile(0.25)
            st.metric("Q1 (25%)", f"{prix_q1/1e6:.2f}M€")

        with col_k3:
            prix_q3 = df_filtre["valeur_fonciere"].quantile(0.75)
            st.metric("Q3 (75%)", f"{prix_q3/1e6:.2f}M€")

        with col_k4:
            prix_max = df_filtre["valeur_fonciere"].max()
            st.metric("Prix max", f"{prix_max/1e6:.2f}M€")

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

        col3, col4 = st.columns([1, 1])
        with col3:
            fig = graphique_prix_m2(df_filtre)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        with col4:
            fig = graphique_type_bien(df_filtre)
            if fig:
                st.plotly_chart(fig, use_container_width=True)


