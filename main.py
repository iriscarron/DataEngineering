"""
Dashboard DVF Paris
Application Streamlit pour visualiser les transactions immobilieres a Paris
"""
import os
import sys
import subprocess

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dvf:dvf@localhost:5432/dvf")


def verifier_donnees_existantes():
    """Verifie si des donnees existent deja dans la base"""
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM transactions"))
            count = result.scalar()
            return count > 0
    except Exception:
        return False


def lancer_scraping():
    """Lance le scraping des donnees DVF"""
    print("Pas de donnees en base, lancement du scraping...")
    from etl.scraper import run_scraper
    run_scraper(annee_min="2023", annee_max="2024")


# Si on lance avec "python main.py", on verifie les donnees et on lance streamlit
if __name__ == "__main__" and "streamlit" not in sys.modules:
    if not verifier_donnees_existantes():
        lancer_scraping()
    print("Lancement du dashboard Streamlit...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", __file__])
    sys.exit(0)

# A partir d'ici, c'est le code Streamlit
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import create_engine

st.set_page_config(page_title="DVF Paris", layout="wide")


@st.cache_data(show_spinner=False)
def charger_donnees():
    """
    Charge les donnees depuis PostgreSQL
    """
    try:
        engine = create_engine(DATABASE_URL)
        query = """
            SELECT
                date_mutation, valeur_fonciere, surface_reelle_bati,
                prix_m2, nb_pieces, type_local, nature_mutation,
                code_postal, arrondissement, latitude, longitude
            FROM transactions
            WHERE valeur_fonciere IS NOT NULL
            ORDER BY date_mutation DESC
        """
        df = pd.read_sql(query, engine)
        df["date_mutation"] = pd.to_datetime(df["date_mutation"])
        return df
    except Exception as e:
        st.error(f"Erreur de connexion a la base: {e}")
        return pd.DataFrame()


def graphique_timeline(df):
    """
    Graphique: quand les appartements ont ete achetes (timeline)
    """
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
        labels={"mois": "Mois", "nb_transactions": "Nombre de transactions"}
    )
    fig.update_layout(xaxis_tickangle=-45)
    return fig


def graphique_grosses_ventes(df, seuil_percentile=95):
    """
    Indicateur des grosses ventes (au dessus d'un certain seuil)
    """
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
        title=f"Grosses ventes (> {seuil/1e6:.1f}M euros - top {100-seuil_percentile}%)",
        labels={
            "date_mutation": "Date",
            "valeur_fonciere": "Prix (euros)",
            "arrondissement": "Arrondissement"
        }
    )
    return fig


def graphique_prix_arrondissement(df):
    """
    Prix median par arrondissement
    """
    if df.empty:
        return None

    agg = df.groupby("arrondissement").agg({
        "valeur_fonciere": "median",
        "prix_m2": "median"
    }).reset_index()

    # Trier par numero d'arrondissement
    agg["arr_num"] = pd.to_numeric(agg["arrondissement"], errors="coerce")
    agg = agg.sort_values("arr_num")

    fig = px.bar(
        agg,
        x="arrondissement",
        y="valeur_fonciere",
        title="Prix median par arrondissement",
        labels={
            "arrondissement": "Arrondissement",
            "valeur_fonciere": "Prix median (euros)"
        },
        color="valeur_fonciere",
        color_continuous_scale="Reds"
    )
    return fig


def graphique_evolution_prix(df):
    """
    Evolution des prix dans le temps
    """
    if df.empty:
        return None

    ts = df.copy()
    ts["mois"] = ts["date_mutation"].dt.to_period("M").astype(str)

    agg = ts.groupby("mois").agg({
        "valeur_fonciere": "median",
        "prix_m2": "median"
    }).reset_index()

    fig = px.line(
        agg,
        x="mois",
        y="prix_m2",
        title="Evolution du prix median au m2",
        labels={"mois": "Mois", "prix_m2": "Prix median au m2 (euros)"},
        markers=True
    )
    fig.update_layout(xaxis_tickangle=-45)
    return fig


def graphique_prix_m2(df):
    """
    Distribution du prix au m2 par arrondissement
    """
    if df.empty:
        return None

    # Filtrer valeurs aberrantes
    df_filtre = df[
        (df["prix_m2"] > 1000) &
        (df["prix_m2"] < 50000)
    ].copy()

    fig = px.box(
        df_filtre,
        x="arrondissement",
        y="prix_m2",
        color="arrondissement",
        title="Distribution du prix au m2 par arrondissement",
        labels={
            "arrondissement": "Arrondissement",
            "prix_m2": "Prix au m2 (euros)"
        }
    )
    fig.update_layout(showlegend=False)
    return fig


def graphique_type_bien(df):
    """
    Prix median par type de bien
    """
    if df.empty:
        return None

    agg = df.groupby("type_local").agg({
        "valeur_fonciere": ["median", "count"],
        "prix_m2": "median"
    }).reset_index()
    agg.columns = ["type_local", "prix_median", "nb_ventes", "prix_m2_median"]

    fig = px.bar(
        agg,
        x="type_local",
        y="prix_median",
        color="nb_ventes",
        title="Prix median par type de bien",
        labels={
            "type_local": "Type de bien",
            "prix_median": "Prix median (euros)",
            "nb_ventes": "Nombre de ventes"
        },
        text="nb_ventes"
    )
    fig.update_traces(textposition="outside")
    return fig


def graphique_nature_mutation(df):
    """
    Repartition par type de vente (nature de mutation)
    """
    if df.empty:
        return None

    agg = df.groupby("nature_mutation").size().reset_index(name="count")

    fig = px.pie(
        agg,
        values="count",
        names="nature_mutation",
        title="Repartition par type de vente",
        hole=0.3
    )
    return fig


def afficher_kpis(df):
    """
    Affiche les indicateurs cles en haut du dashboard
    """
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Transactions", f"{len(df):,}")

    with col2:
        prix_moyen = df["valeur_fonciere"].mean()
        st.metric("Prix moyen", f"{prix_moyen/1e6:.2f}M")

    with col3:
        prix_m2_moyen = df["prix_m2"].median()
        st.metric("Prix m2 median", f"{prix_m2_moyen:,.0f} euros")

    with col4:
        surface_moyenne = df["surface_reelle_bati"].mean()
        st.metric("Surface moyenne", f"{surface_moyenne:.0f} m2")

    with col5:
        seuil_grosse_vente = df["valeur_fonciere"].quantile(0.95)
        nb_grosses = len(df[df["valeur_fonciere"] >= seuil_grosse_vente])
        st.metric("Grosses ventes (top 5%)", f"{nb_grosses}")


def main():
    st.title("DVF Paris - Transactions Immobilieres")
    st.caption("Donnees scrapees depuis l'API DVF+ du Cerema")

    df = charger_donnees()

    if df.empty:
        st.warning("Aucune donnee disponible. Lancez d'abord le scraper avec: python etl/scraper.py")
        st.info("Ou utilisez docker-compose up pour lancer l'application complete")
        return

    with st.sidebar:     # Sidebar filtres
        st.header("Filtres")

        min_date = df["date_mutation"].min().date() #filtre date
        max_date = df["date_mutation"].max().date()

        date_range = st.date_input(
            "Periode",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

        arrondissements = sorted(df["arrondissement"].dropna().unique(), key=lambda x: int(x) if x.isdigit() else 0)
        arr_selected = st.multiselect(
            "Arrondissements", # Filtre arrondissements
            arrondissements,
            default=arrondissements
        )

        types = sorted(df["type_local"].dropna().unique())        # Filtre type de bien
        types_selected = st.multiselect(
            "Type de bien",
            types,
            default=types
        )

        if "nature_mutation" in df.columns:        # Filtre nature mutation (type de vente)
            natures = sorted(df["nature_mutation"].dropna().unique())
            natures_selected = st.multiselect(
                "Type de vente",
                natures,
                default=natures
            )
        else:
            natures_selected = []

        st.subheader("Filtres prix")         # Filtre prix
        prix_min, prix_max = st.slider(
            "Plage de prix (euros)",
            min_value=0,
            max_value=int(df["valeur_fonciere"].max()),
            value=(0, int(df["valeur_fonciere"].quantile(0.99)))
        )

        seuil_percentile = st.slider(         # Seuil grosses ventes
            "Seuil grosses ventes (percentile)",
            min_value=80,
            max_value=99,
            value=95
        )

    if len(date_range) == 2:     # Appliquer les filtres
        mask = (
            (df["date_mutation"].dt.date >= date_range[0]) &
            (df["date_mutation"].dt.date <= date_range[1]) &
            (df["arrondissement"].isin(arr_selected)) &
            (df["type_local"].isin(types_selected)) &
            (df["valeur_fonciere"] >= prix_min) &
            (df["valeur_fonciere"] <= prix_max)
        )

        if natures_selected and "nature_mutation" in df.columns:
            mask = mask & (df["nature_mutation"].isin(natures_selected))

        df_filtre = df[mask].copy()
    else:
        df_filtre = df.copy()

    afficher_kpis(df_filtre)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        fig = graphique_timeline(df_filtre)
        if fig:
            st.plotly_chart(fig, width='stretch')

    with col2:
        fig = graphique_grosses_ventes(df_filtre, seuil_percentile)
        if fig:
            st.plotly_chart(fig, width='stretch')

    col3, col4 = st.columns(2)

    with col3:
        fig = graphique_prix_arrondissement(df_filtre)
        if fig:
            st.plotly_chart(fig, width='stretch')

    with col4:
        fig = graphique_evolution_prix(df_filtre)
        if fig:
            st.plotly_chart(fig, width='stretch')

    col5, col6 = st.columns(2)

    with col5:
        fig = graphique_prix_m2(df_filtre)
        if fig:
            st.plotly_chart(fig, width='stretch')

    with col6:
        fig = graphique_type_bien(df_filtre)
        if fig:
            st.plotly_chart(fig, width='stretch')

    col7, col8 = st.columns(2)

    with col7:
        fig = graphique_nature_mutation(df_filtre)
        if fig:
            st.plotly_chart(fig, width='stretch')

    with col8:
        st.subheader("Apercu des donnees")
        st.dataframe(
            df_filtre.head(100),
            width='stretch',
            hide_index=True
        )


if __name__ == "__main__":
    main()
