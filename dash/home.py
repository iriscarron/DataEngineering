import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st

from dash.layout import PRIMARY_COLOR, SECONDARY_COLOR, ACCENT_COLOR, styliser_fig


def afficher_kpis(df):
    """Affiche les indicateurs cles en haut du dashboard."""
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Transactions", f"{len(df):,}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        prix_moyen = df["valeur_fonciere"].mean()
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Prix moyen", f"{prix_moyen/1e6:.2f}M")
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        prix_m2_median = df["prix_m2"].median()
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Prix m2 median", f"{prix_m2_median:,.0f} euros")
        st.markdown('</div>', unsafe_allow_html=True)

    with col4:
        surface_moyenne = df["surface_reelle_bati"].mean()
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Surface moyenne", f"{surface_moyenne:.0f} m2")
        st.markdown('</div>', unsafe_allow_html=True)

    with col5:
        seuil_grosse_vente = df["valeur_fonciere"].quantile(0.95)
        nb_grosses = len(df[df["valeur_fonciere"] >= seuil_grosse_vente])
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Grosses ventes (top 5%)", f"{nb_grosses}")
        st.markdown('</div>', unsafe_allow_html=True)


def graphique_timeline(df):
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
    fig.update_traces(marker_color=PRIMARY_COLOR)
    return styliser_fig(fig)


def graphique_grosses_ventes(df, seuil_percentile=95):
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
        title=f"Grosses ventes (> {seuil/1e6:.1f}M euros - top {100-seuil_percentile}% )",
        labels={
            "date_mutation": "Date",
            "valeur_fonciere": "Prix (euros)",
            "arrondissement": "Arrondissement",
        },
    )
    fig.update_traces(marker=dict(opacity=0.7, line=dict(width=0)))
    return styliser_fig(fig)


def graphique_prix_arrondissement(df):
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
        title="Prix median par arrondissement",
        labels={"arrondissement": "Arrondissement", "valeur_fonciere": "Prix median (euros)"},
        color="valeur_fonciere",
        color_continuous_scale="Reds",
    )
    fig.update_traces(marker_line_width=0)
    return styliser_fig(fig)


def graphique_evolution_prix(df):
    if df.empty:
        return None

    ts = df.copy()
    ts["mois"] = ts["date_mutation"].dt.to_period("M").astype(str)

    agg = ts.groupby("mois").agg({"valeur_fonciere": "median", "prix_m2": "median"}).reset_index()

    fig = px.line(
        agg,
        x="mois",
        y="prix_m2",
        title="Evolution du prix median au m2",
        labels={"mois": "Mois", "prix_m2": "Prix median au m2 (euros)"},
        markers=True,
    )
    fig.update_layout(xaxis_tickangle=-45)
    fig.update_traces(line_width=3)
    return styliser_fig(fig)


def graphique_prix_m2(df):
    if df.empty:
        return None

    df_filtre = df[(df["prix_m2"] > 1000) & (df["prix_m2"] < 50000)].copy()

    fig = px.box(
        df_filtre,
        x="arrondissement",
        y="prix_m2",
        color="arrondissement",
        title="Distribution du prix au m2 par arrondissement",
        labels={"arrondissement": "Arrondissement", "prix_m2": "Prix au m2 (euros)"},
    )
    fig.update_layout(showlegend=False)
    fig.update_traces(marker_color=SECONDARY_COLOR)
    return styliser_fig(fig)


def graphique_type_bien(df):
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
        title="Prix median par type de bien",
        labels={"type_local": "Type de bien", "prix_median": "Prix median (euros)", "nb_ventes": "Nombre de ventes"},
        text="nb_ventes",
    )
    fig.update_traces(textposition="outside")
    return styliser_fig(fig)


def graphique_nature_mutation(df):
    if df.empty:
        return None

    agg = df.groupby("nature_mutation").size().reset_index(name="count")

    fig = px.pie(
        agg,
        values="count",
        names="nature_mutation",
        title="Repartition par type de vente",
        hole=0.3,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return styliser_fig(fig)


def render_home(df, filters):
    """Rend la page principale avec KPIs et graphiques."""
    if df.empty:
        st.warning("Aucune donnee disponible. Lancez d'abord le scraper.")
        return

    seuil_percentile = filters.get("seuil_percentile", 95)

    afficher_kpis(df)
    st.divider()

    col1, col2 = st.columns([2, 1])
    with col1:
        fig = graphique_timeline(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = graphique_grosses_ventes(df, seuil_percentile)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        fig = graphique_prix_arrondissement(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with col4:
        fig = graphique_evolution_prix(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    col5, col6 = st.columns(2)
    with col5:
        fig = graphique_prix_m2(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with col6:
        fig = graphique_type_bien(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    col7, col8 = st.columns([1, 2])
    with col7:
        fig = graphique_nature_mutation(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with col8:
        st.subheader("Apercu des donnees")
        st.dataframe(df.head(100), use_container_width=True, hide_index=True)
