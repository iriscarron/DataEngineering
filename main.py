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
    """Lance le scraping des donnees DVF depuis l'API (avec geometries des parcelles)"""
    print("Pas de donnees en base, lancement du scraping avec geometries...")
    from etl.scraper import run_scraper_geo
    run_scraper_geo(annee_min="2024", annee_max="2024")


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
                id, id_mutation, date_mutation, valeur_fonciere, surface_reelle_bati,
                prix_m2, nb_pieces, type_local, nature_mutation,
                code_postal, arrondissement, latitude, longitude,
                geom_json, l_idpar
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
    Carte interactive des transactions immobilieres (points)
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
        height=600,
        uirevision="constant"  # Preserve zoom/pan state on data updates
    )

    # Add zoom controls configuration
    fig.update_mapboxes(
        bearing=0,
        pitch=0
    )

    return fig


def charger_historique_parcelle(id_parcelle):
    """
    Charge l'historique des transactions pour une parcelle
    """
    try:
        engine = create_engine(DATABASE_URL)
        query = f"""
            SELECT id_mutation, date_mutation, nature_mutation, valeur_fonciere,
                   type_local, surface_reelle_bati, nombre_pieces, adresse
            FROM historique_transactions
            WHERE id_parcelle = '{id_parcelle}'
            ORDER BY date_mutation DESC
        """
        df = pd.read_sql(query, engine)
        if "date_mutation" in df.columns:
            df["date_mutation"] = pd.to_datetime(df["date_mutation"])
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(show_spinner="Chargement des parcelles...")
def charger_parcelles(arrondissements=None):
    """
    Charge les parcelles depuis la table parcelles (cadastre complet + DVF)
    """
    try:
        engine = create_engine(DATABASE_URL)

        if arrondissements:
            arr_list = ",".join([f"'{a}'" for a in arrondissements])
            query = f"""
                SELECT id, id_parcelle, geom_json, arrondissement, has_transaction,
                       valeur_fonciere, prix_m2, type_local, surface_reelle_bati,
                       date_mutation, nature_mutation, adresse, nb_transactions
                FROM parcelles
                WHERE arrondissement IN ({arr_list})
            """
        else:
            query = """
                SELECT id, id_parcelle, geom_json, arrondissement, has_transaction,
                       valeur_fonciere, prix_m2, type_local, surface_reelle_bati,
                       date_mutation, nature_mutation, adresse, nb_transactions
                FROM parcelles
            """

        df = pd.read_sql(query, engine)
        if "date_mutation" in df.columns:
            df["date_mutation"] = pd.to_datetime(df["date_mutation"])
        return df
    except Exception as e:
        st.error(f"Erreur chargement parcelles: {e}")
        return pd.DataFrame()


def carte_parcelles(df, show_no_transaction=True):
    """
    Carte interactive avec les polygones des parcelles cadastrales

    Args:
        df: DataFrame avec les parcelles
        show_no_transaction: Si True, affiche aussi les parcelles sans vente (fond bleu)
    """
    import json

    if df.empty:
        return None, None

    # Filtrer les lignes avec geometrie valide
    df_geo = df[df["geom_json"].notna()].copy().reset_index(drop=True)

    if df_geo.empty:
        return None, None

    # Limiter pour les performances (afficher plus de parcelles)
    if len(df_geo) > 5000:
        # Garder toutes les parcelles avec transaction + echantillon des autres
        df_with_tx = df_geo[df_geo["has_transaction"] == True]
        df_without_tx = df_geo[df_geo["has_transaction"] == False]
        if len(df_with_tx) < 5000:
            remaining = 5000 - len(df_with_tx)
            df_without_sample = df_without_tx.sample(n=min(remaining, len(df_without_tx)), random_state=42)
            df_geo = pd.concat([df_with_tx, df_without_sample]).reset_index(drop=True)
        else:
            df_geo = df_with_tx.sample(n=5000, random_state=42).reset_index(drop=True)

    # Construire le GeoJSON FeatureCollection
    features = []
    valid_indices = []
    for idx, row in df_geo.iterrows():
        try:
            geom = json.loads(row["geom_json"])
            if not geom or "coordinates" not in geom:
                continue

            has_tx = row.get("has_transaction", False)

            if has_tx and pd.notna(row.get("valeur_fonciere")):
                # Parcelle avec transaction
                prix = row["valeur_fonciere"]
                prix_affiche = f"{prix/1e6:.2f}M euros" if prix >= 1e6 else f"{prix/1e3:.0f}k euros"
                prix_m2 = row["prix_m2"]
                prix_m2_affiche = f"{prix_m2:,.0f} euros/m2" if pd.notna(prix_m2) else "N/A"
                surface = row["surface_reelle_bati"] if pd.notna(row["surface_reelle_bati"]) else 0
                type_local = row["type_local"] or "Bien immobilier"
                date_str = row["date_mutation"].strftime("%d/%m/%Y") if pd.notna(row["date_mutation"]) else "N/A"
            else:
                # Parcelle sans transaction
                prix = 0
                prix_affiche = "Pas de vente"
                prix_m2 = -1  # Valeur speciale pour parcelles sans transaction
                prix_m2_affiche = "N/A"
                surface = 0
                type_local = "Parcelle cadastrale"
                date_str = "N/A"

            feature = {
                "type": "Feature",
                "id": idx,
                "geometry": geom,
                "properties": {
                    "idx": idx,
                    "id_parcelle": row.get("id_parcelle", ""),
                    "has_transaction": has_tx,
                    "prix": prix,
                    "prix_affiche": prix_affiche,
                    "prix_m2": prix_m2 if pd.notna(prix_m2) and prix_m2 > 0 else 0,
                    "prix_m2_affiche": prix_m2_affiche,
                    "surface": surface,
                    "type_local": type_local,
                    "arrondissement": row.get("arrondissement") or "N/A",
                    "date": date_str,
                    "adresse": row.get("adresse") or ""
                }
            }
            features.append(feature)
            valid_indices.append(idx)
        except (json.JSONDecodeError, TypeError, KeyError):
            continue

    if not features:
        return None, None

    # Filter df_geo to only valid rows
    df_geo = df_geo.loc[valid_indices].reset_index(drop=True)

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    # Calculer le centre
    all_lats = []
    all_lons = []
    for f in features[:100]:  # Sample for center calculation
        coords = f["geometry"].get("coordinates", [])
        if f["geometry"]["type"] == "Polygon" and coords:
            for c in coords[0]:
                all_lons.append(c[0])
                all_lats.append(c[1])
        elif f["geometry"]["type"] == "MultiPolygon" and coords:
            for poly in coords:
                for ring in poly:
                    for c in ring:
                        all_lons.append(c[0])
                        all_lats.append(c[1])

    if all_lats and all_lons:
        center_lat = sum(all_lats) / len(all_lats)
        center_lon = sum(all_lons) / len(all_lons)
    else:
        center_lat, center_lon = 48.8566, 2.3522

    # Separer les parcelles avec et sans transaction
    features_with_tx = [f for f in features if f["properties"]["has_transaction"]]
    features_without_tx = [f for f in features if not f["properties"]["has_transaction"]]

    fig = go.Figure()

    # 1. Parcelles SANS transaction (contours bleus) - si active
    if show_no_transaction and features_without_tx:
        geojson_no_tx = {"type": "FeatureCollection", "features": features_without_tx}
        ids_no_tx = [f["id"] for f in features_without_tx]

        fig.add_trace(go.Choroplethmapbox(
            geojson=geojson_no_tx,
            locations=ids_no_tx,
            z=[0] * len(features_without_tx),
            colorscale=[[0, "rgba(200, 200, 255, 0.3)"], [1, "rgba(200, 200, 255, 0.3)"]],
            marker_opacity=0.4,
            marker_line_width=0.8,
            marker_line_color="darkblue",
            showscale=False,
            hovertemplate=(
                "<b>Parcelle %{customdata[0]}</b><br>"
                "Arr: %{customdata[1]}e<br>"
                "Pas de vente enregistree<br>"
                "<extra></extra>"
            ),
            customdata=[[
                f["properties"]["id_parcelle"],
                f["properties"]["arrondissement"]
            ] for f in features_without_tx],
            name="Sans vente"
        ))

    # 2. Parcelles AVEC transaction (colorees par prix/m2)
    if features_with_tx:
        geojson_tx = {"type": "FeatureCollection", "features": features_with_tx}
        ids_tx = [f["id"] for f in features_with_tx]
        prix_m2_values = [f["properties"]["prix_m2"] for f in features_with_tx]

        # Calculer les bornes de couleur
        valid_prices = [p for p in prix_m2_values if p > 0]
        if valid_prices:
            zmin = np.percentile(valid_prices, 10)
            zmax = np.percentile(valid_prices, 90)
        else:
            zmin, zmax = 3000, 15000

        fig.add_trace(go.Choroplethmapbox(
            geojson=geojson_tx,
            locations=ids_tx,
            z=prix_m2_values,
            colorscale="RdYlGn_r",
            zmin=zmin,
            zmax=zmax,
            marker_opacity=0.8,
            marker_line_width=1,
            marker_line_color="darkred",
            colorbar=dict(
                title="Prix/m2",
                tickformat=",d",
                ticksuffix=" euros",
                len=0.8
            ),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Parcelle: %{customdata[6]}<br>"
                "Prix: %{customdata[1]}<br>"
                "Prix/m2: %{customdata[2]}<br>"
                "Surface: %{customdata[3]:.0f} m2<br>"
                "Arr: %{customdata[4]}e<br>"
                "Date: %{customdata[5]}<br>"
                "<extra></extra>"
            ),
            customdata=[[
                f["properties"]["type_local"],
                f["properties"]["prix_affiche"],
                f["properties"]["prix_m2_affiche"],
                f["properties"]["surface"],
                f["properties"]["arrondissement"],
                f["properties"]["date"],
                f["properties"]["id_parcelle"]
            ] for f in features_with_tx],
            name="Avec vente"
        ))

    # Titre dynamique
    if show_no_transaction:
        title = f"Parcelles cadastrales - {len(features_with_tx)} ventes / {len(features)} parcelles"
    else:
        title = f"Ventes immobilieres - {len(features_with_tx)} transactions"

    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox_zoom=14,
        mapbox_center={"lat": center_lat, "lon": center_lon},
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        height=700,
        title=title,
        uirevision="parcelles",
        showlegend=False
    )

    return fig, df_geo


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
        height=600,
        uirevision="constant",  # Preserve zoom/pan state on data updates
        coloraxis_colorbar=dict(
            title="Prix/m2",
            tickformat=",d"
        )
    )

    # Add zoom controls configuration
    fig.update_mapboxes(
        bearing=0,
        pitch=0
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
    tab_parcelles, tab_choropleth, tab_points = st.tabs([
        "Carte des parcelles",
        "Carte par arrondissement",
        "Carte des transactions (points)"
    ])

    # Configuration pour un meilleur zoom/scroll sur les cartes
    map_config = {
        "scrollZoom": True,
        "displayModeBar": True,
        "modeBarButtonsToAdd": ["zoomIn2d", "zoomOut2d", "resetScale2d"],
        "displaylogo": False
    }

    with tab_parcelles:
        st.subheader("Carte cadastrale avec ventes DVF")

        # Controles en ligne
        col_arr, col_toggle, col_search = st.columns([2, 2, 2])

        with col_arr:
            arr_parcelles = st.selectbox(
                "Arrondissement",
                options=[str(i) for i in range(1, 21)],
                index=3,  # 4eme par defaut
                key="arr_parcelles"
            )

        with col_toggle:
            show_all_parcels = st.toggle(
                "Afficher toutes les parcelles",
                value=True,
                help="Affiche les parcelles sans vente en fond bleu"
            )

        with col_search:
            search_parcelle = st.text_input(
                "Rechercher parcelle",
                placeholder="Ex: 75104000AF0061",
                key="search_parcelle"
            )

        arr_list = [arr_parcelles]

        # Charger les parcelles
        df_parcelles = charger_parcelles(tuple(arr_list))

        if not df_parcelles.empty:
            # Layout: carte + panneau details
            col_map, col_details = st.columns([3, 1])

            with col_map:
                fig_parcelles, df_geo = carte_parcelles(df_parcelles, show_no_transaction=show_all_parcels)

                if fig_parcelles:
                    # Afficher la carte avec selection
                    selected = st.plotly_chart(
                        fig_parcelles,
                        use_container_width=True,
                        config=map_config,
                        on_select="rerun",
                        key="map_parcelles"
                    )

            with col_details:
                st.markdown("### Details")

                # Gerer la recherche de parcelle
                parcelle_found = None
                if search_parcelle:
                    match = df_geo[df_geo["id_parcelle"].str.contains(search_parcelle.upper(), na=False)]
                    if not match.empty:
                        parcelle_found = match.iloc[0]
                        st.success(f"Parcelle trouvee!")
                    else:
                        st.warning("Parcelle non trouvee")

                # Gerer le clic sur la carte
                elif selected and hasattr(selected, 'selection') and selected.selection:
                    points = selected.selection.get('points', [])
                    if points:
                        point = points[0]
                        # Recuperer l'index de la parcelle
                        point_idx = point.get('pointIndex', point.get('point_index'))
                        if point_idx is not None and point_idx < len(df_geo):
                            parcelle_found = df_geo.iloc[point_idx]

                # Afficher les details de la parcelle
                if parcelle_found is not None:
                    row = parcelle_found
                    id_parcelle = row.get('id_parcelle', '')

                    st.markdown(f"**Parcelle:**")
                    st.code(id_parcelle)

                    if row.get('has_transaction'):
                        # Charger l'historique complet
                        historique = charger_historique_parcelle(id_parcelle)

                        if not historique.empty:
                            st.markdown("---")
                            st.markdown(f"#### Historique ({len(historique)} vente{'s' if len(historique) > 1 else ''})")

                            for i, tx in historique.iterrows():
                                with st.expander(
                                    f"{tx['date_mutation'].strftime('%d/%m/%Y') if pd.notna(tx['date_mutation']) else 'N/A'} - "
                                    f"{tx['valeur_fonciere']/1e6:.2f}M euros" if tx['valeur_fonciere'] >= 1e6 else
                                    f"{tx['date_mutation'].strftime('%d/%m/%Y') if pd.notna(tx['date_mutation']) else 'N/A'} - "
                                    f"{tx['valeur_fonciere']/1e3:.0f}k euros",
                                    expanded=(i == 0)  # Premier element ouvert
                                ):
                                    # Type
                                    st.write(f"**{tx.get('type_local', 'Bien immobilier')}**")

                                    # Prix
                                    prix = tx['valeur_fonciere']
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        prix_str = f"{prix/1e6:.2f}M" if prix >= 1e6 else f"{prix/1e3:.0f}k"
                                        st.metric("Prix", f"{prix_str}")

                                    # Surface et prix/m2
                                    surface = tx.get('surface_reelle_bati')
                                    with col2:
                                        if pd.notna(surface) and surface > 0:
                                            st.metric("Surface", f"{surface:.0f} m2")
                                            prix_m2 = prix / surface
                                            st.caption(f"soit {prix_m2:,.0f} euros/m2")

                                    # Pieces
                                    pieces = tx.get('nombre_pieces')
                                    if pd.notna(pieces) and pieces > 0:
                                        st.write(f"**Pieces:** {int(pieces)}")

                                    # Adresse
                                    adresse = tx.get('adresse')
                                    if adresse:
                                        st.write(f"**Adresse:** {adresse}")

                                    # Nature
                                    nature = tx.get('nature_mutation')
                                    if nature:
                                        st.write(f"**Type:** {nature}")
                        else:
                            st.info("Historique non disponible")
                    else:
                        st.info("Pas de vente enregistree sur cette parcelle")
                else:
                    st.info("Cliquez sur une parcelle coloree pour voir les details de la vente")

                # Stats
                st.markdown("---")
                nb_avec_vente = df_geo["has_transaction"].sum() if "has_transaction" in df_geo.columns else 0
                st.caption(f"{len(df_geo)} parcelles")
                st.caption(f"{nb_avec_vente} avec ventes")
        else:
            st.warning("Aucune parcelle trouvee. Chargez les donnees cadastrales avec:")
            st.code("python -m etl.load_cadastre_dvf", language="bash")

    with tab_choropleth:
        fig_choro = carte_choropleth(df_filtre)
        if fig_choro:
            st.plotly_chart(fig_choro, use_container_width=True, config=map_config)
        else:
            st.info("Impossible de charger la carte des arrondissements")

    with tab_points:
        fig_carte = carte_interactive(df_filtre)
        if fig_carte:
            st.plotly_chart(fig_carte, use_container_width=True, config=map_config)
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
