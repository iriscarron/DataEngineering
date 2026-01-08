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
    """Lance le scraping des donnees DVF depuis l'API"""
    print("Pas de donnees en base, lancement du scraping...")
    from etl.scraper import run_scraper
    run_scraper(annee_min="2024", annee_max="2024")


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


def carte_interactive(df):
    """
    Carte interactive des transactions immobilieres
    """
    if df.empty:
        return None

    # Filtrer les lignes avec coordonnees valides
    df_carte = df.dropna(subset=["latitude", "longitude"]).copy()

    if df_carte.empty:
        return None

    # Limiter le nombre de points pour les performances
    if len(df_carte) > 2000:
        df_carte = df_carte.sample(n=2000, random_state=42)

    # Formater le prix pour l'affichage
    df_carte["prix_affiche"] = df_carte["valeur_fonciere"].apply(
        lambda x: f"{x/1e6:.2f}M" if x >= 1e6 else f"{x/1e3:.0f}k"
    )

    fig = px.scatter_mapbox(
        df_carte,
        lat="latitude",
        lon="longitude",
        color="prix_m2",
        size="valeur_fonciere",
        color_continuous_scale="RdYlGn_r",
        size_max=15,
        zoom=11,
        center={"lat": 48.8566, "lon": 2.3522},
        hover_name="type_local",
        hover_data={
            "arrondissement": True,
            "prix_affiche": True,
            "surface_reelle_bati": True,
            "prix_m2": ":.0f",
            "latitude": False,
            "longitude": False,
            "valeur_fonciere": False
        },
        labels={
            "prix_m2": "Prix/m2",
            "arrondissement": "Arr.",
            "prix_affiche": "Prix",
            "surface_reelle_bati": "Surface"
        },
        title="Carte des transactions immobilieres a Paris"
    )

    fig.update_layout(
        mapbox_style="open-street-map",
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        height=500
    )

    return fig


@st.cache_data(show_spinner=False)
def charger_geojson_arrondissements():
    """
    Charge le GeoJSON des arrondissements de Paris depuis OpenDataSoft
    """
    import requests
    url = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/arrondissements/exports/geojson"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


def carte_choropleth(df):
    """
    Carte choroplethe des prix au m2 par arrondissement
    """
    if df.empty:
        return None

    geojson = charger_geojson_arrondissements()
    if geojson is None:
        return None

    # Agreger les donnees par arrondissement
    agg = df.groupby("arrondissement").agg({
        "prix_m2": "median",
        "valeur_fonciere": ["median", "count"],
        "surface_reelle_bati": "median"
    }).reset_index()
    agg.columns = ["arrondissement", "prix_m2_median", "prix_median", "nb_transactions", "surface_mediane"]

    # Formater le numero d'arrondissement pour correspondre au GeoJSON
    agg["c_ar"] = agg["arrondissement"].apply(lambda x: str(int(x)) if pd.notna(x) else None)

    # Formater les valeurs pour l'affichage
    agg["prix_m2_affiche"] = agg["prix_m2_median"].apply(lambda x: f"{x:,.0f} euros/m2" if pd.notna(x) else "N/A")
    agg["prix_affiche"] = agg["prix_median"].apply(lambda x: f"{x/1e6:.2f}M euros" if pd.notna(x) else "N/A")

    fig = px.choropleth_mapbox(
        agg,
        geojson=geojson,
        locations="c_ar",
        featureidkey="properties.c_ar",
        color="prix_m2_median",
        color_continuous_scale="RdYlGn_r",
        range_color=[agg["prix_m2_median"].quantile(0.1), agg["prix_m2_median"].quantile(0.9)],
        mapbox_style="open-street-map",
        zoom=11,
        center={"lat": 48.8566, "lon": 2.3522},
        opacity=0.7,
        hover_name="arrondissement",
        hover_data={
            "c_ar": False,
            "prix_m2_median": False,
            "prix_m2_affiche": True,
            "prix_affiche": True,
            "nb_transactions": True,
            "surface_mediane": ":.0f"
        },
        labels={
            "prix_m2_affiche": "Prix/m2",
            "prix_affiche": "Prix median",
            "nb_transactions": "Transactions",
            "surface_mediane": "Surface med."
        },
        title="Prix median au m2 par arrondissement"
    )

    fig.update_layout(
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        height=500,
        coloraxis_colorbar=dict(
            title="Prix/m2",
            tickformat=",d"
        )
    )

    return fig


def moteur_recherche():
    """
    Interface de recherche Elasticsearch
    """
    try:
        from etl.elasticsearch_utils import rechercher_transactions, elasticsearch_disponible

        if not elasticsearch_disponible():
            st.info("Moteur de recherche en cours d'initialisation...")
            return

        st.subheader("Recherche avancee")

        col_search, col_filters = st.columns([2, 1])

        with col_search:
            query = st.text_input(
                "Rechercher",
                placeholder="Ex: appartement 16eme, maison 5 pieces, vente terrain...",
                key="es_search"
            )

        with col_filters:
            prix_range = st.select_slider(
                "Budget max",
                options=[100000, 250000, 500000, 750000, 1000000, 2000000, 5000000, 10000000],
                value=2000000,
                format_func=lambda x: f"{x/1e6:.1f}M" if x >= 1e6 else f"{x/1e3:.0f}k"
            )

        if query or st.button("Rechercher", key="btn_search"):
            filtres = {"prix_max": prix_range}
            resultats = rechercher_transactions(query, filtres=filtres, taille=50)

            if resultats:
                st.success(f"{len(resultats)} resultats trouves")

                # Afficher les resultats sous forme de tableau
                df_resultats = pd.DataFrame(resultats)

                # Formater les colonnes pour l'affichage
                colonnes_affichage = []
                if "date_mutation" in df_resultats.columns:
                    df_resultats["date_mutation"] = pd.to_datetime(df_resultats["date_mutation"]).dt.strftime("%d/%m/%Y")
                    colonnes_affichage.append("date_mutation")

                if "type_local" in df_resultats.columns:
                    colonnes_affichage.append("type_local")

                if "arrondissement" in df_resultats.columns:
                    df_resultats["arrondissement"] = df_resultats["arrondissement"].apply(lambda x: f"{x}eme" if x else "")
                    colonnes_affichage.append("arrondissement")

                if "valeur_fonciere" in df_resultats.columns:
                    df_resultats["prix"] = df_resultats["valeur_fonciere"].apply(
                        lambda x: f"{x/1e6:.2f}M" if x and x >= 1e6 else f"{x/1e3:.0f}k" if x else ""
                    )
                    colonnes_affichage.append("prix")

                if "surface_reelle_bati" in df_resultats.columns:
                    df_resultats["surface"] = df_resultats["surface_reelle_bati"].apply(
                        lambda x: f"{x:.0f} m2" if x else ""
                    )
                    colonnes_affichage.append("surface")

                if "prix_m2" in df_resultats.columns:
                    df_resultats["prix_m2_affiche"] = df_resultats["prix_m2"].apply(
                        lambda x: f"{x:,.0f} euros/m2" if x else ""
                    )
                    colonnes_affichage.append("prix_m2_affiche")

                if "nature_mutation" in df_resultats.columns:
                    colonnes_affichage.append("nature_mutation")

                st.dataframe(
                    df_resultats[colonnes_affichage],
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "date_mutation": "Date",
                        "type_local": "Type",
                        "arrondissement": "Arr.",
                        "prix": "Prix",
                        "surface": "Surface",
                        "prix_m2_affiche": "Prix/m2",
                        "nature_mutation": "Nature"
                    }
                )
            else:
                st.warning("Aucun resultat trouve")

    except ImportError:
        st.info("Module Elasticsearch non disponible")
    except Exception as e:
        st.error(f"Erreur: {e}")


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

    # Moteur de recherche Elasticsearch
    moteur_recherche()

    st.divider()

    # Cartes avec onglets
    tab_choropleth, tab_points = st.tabs(["Carte par arrondissement", "Carte des transactions"])

    with tab_choropleth:
        fig_choro = carte_choropleth(df_filtre)
        if fig_choro:
            st.plotly_chart(fig_choro, use_container_width=True)
        else:
            st.info("Impossible de charger la carte des arrondissements")

    with tab_points:
        fig_carte = carte_interactive(df_filtre)
        if fig_carte:
            st.plotly_chart(fig_carte, use_container_width=True)
        else:
            st.info("Pas de coordonnees GPS disponibles pour afficher la carte")

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
