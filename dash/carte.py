"""carte interactive des transactions geolocalisees avec batiments cadastraux."""
import json
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from sqlalchemy import create_engine, text
import os

from dash import layout
from dash.layout import styliser_fig

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dvf:dvf@localhost:5432/dvf")


def render_carte(df):
    """carte des transactions avec polygones des batiments."""
    if df.empty:
        st.info("aucune donnée pour afficher la carte.")
        return

    # layout: filtres a gauche, contenu a droite
    col_filtre, col_contenu = st.columns([1, 3])

    with col_filtre:
        df_filtre = layout.render_filters_sidebar(df, show_percentile=False, show_date_range=False)

    with col_contenu:
        df_map = df_filtre.dropna(subset=["latitude", "longitude"])
        if df_map.empty:
            st.info("pas de coordonnées disponibles pour la carte.")
            return


        # option d'affichage
        niveau_detail = st.selectbox(
            "Niveau de détail",
            ["Arrondissements", "Bâtiments", "Points"],
            index=0,
            help="Arrondissements: vue globale, Bâtiments: polygones individuels, Points: transactions précises"
        )

        color_by_display = "Prix au m²"

        if niveau_detail == "Arrondissements":
            # Vue par arrondissements avec polygones (choroplèthe)
            with st.spinner("Chargement des statistiques par arrondissement..."):
                df_arr, geojson = layout.charger_arrondissements_avec_stats(df_map)

            if df_arr.empty or geojson is None:
                st.warning("Aucune donnée d'arrondissement trouvée.")
                return

            st.info(f"20 arrondissements - {len(df_map):,} transactions")

            # Mapper les codes arrondissement du GeoJSON avec les stats
            # Le GeoJSON contient "c_ar" pour le code arrondissement
            for feature in geojson["features"]:
                arr_code = feature["properties"].get("c_ar", "")
                # Convertir en string et retirer le "75" du début si présent (ex: "7501" -> "1")
                arr_code = str(arr_code)
                if arr_code and arr_code.startswith("75"):
                    arr_code = str(int(arr_code[2:]))
                feature["id"] = arr_code

            # Créer la carte choroplèthe
            fig = go.Figure(go.Choroplethmapbox(
                geojson=geojson,
                locations=df_arr["arrondissement"],
                z=df_arr["prix_m2_moyen"],
                colorscale="Viridis",
                marker_opacity=0.7,
                marker_line_width=2,
                marker_line_color="white",
                text=df_arr.apply(
                    lambda x: f"Arr. {x['arrondissement']}<br>{x['nb_transactions']:,} transactions<br>Prix m²: {x['prix_m2_moyen']:,.0f}€<br>Prix moyen: {x['prix_moyen']/1e6:.2f}M€",
                    axis=1
                ),
                hovertemplate='<b>%{text}</b><extra></extra>',
                colorbar=dict(
                    title=dict(
                        text="Prix m²<br>(€)",
                        side="right"
                    ),
                    tickformat=",",
                    len=0.7,
                )
            ))

            fig.update_layout(
                mapbox=dict(
                    style="carto-positron",
                    center=dict(lat=48.856, lon=2.352),
                    zoom=11
                ),
                title=f"Prix moyen au m² par arrondissement à Paris ({len(df_map):,} transactions)",
                height=700,
            )

            styliser_fig(fig)
            st.plotly_chart(fig, use_container_width=True)

        elif niveau_detail == "Bâtiments":
            # Vue par bâtiments (polygones)
            with st.spinner("Chargement des bâtiments avec transactions..."):
                df_batiments = layout.charger_batiments_avec_transactions(df_map)

            if df_batiments.empty:
                st.warning("Aucun bâtiment avec transaction trouvé.")
                return

            st.info(f"{len(df_batiments):,} bâtiments avec {len(df_map):,} transactions")

            # Créer le GeoJSON des bâtiments
            features = []
            for idx, row in df_batiments.iterrows():
                # Ignorer les lignes sans géométrie
                if row["geometry"] is None or pd.isna(row["geometry"]):
                    continue

                try:
                    geom = json.loads(row["geometry"])
                    features.append({
                        "type": "Feature",
                        "id": str(idx),
                        "geometry": geom,
                        "properties": {
                            "prix_m2_moyen": float(row["prix_m2_moyen"]) if row["prix_m2_moyen"] else 0,
                            "nb_transactions": int(row["nb_transactions"]),
                            "prix_moyen": float(row["prix_moyen"]) if row["prix_moyen"] else 0,
                        }
                    })
                except (json.JSONDecodeError, TypeError):
                    continue

            geojson = {
                "type": "FeatureCollection",
                "features": features
            }

            # Créer la figure avec Choroplethmapbox
            fig = go.Figure(go.Choroplethmapbox(
                geojson=geojson,
                locations=df_batiments.index.astype(str),
                z=df_batiments["prix_m2_moyen"],
                colorscale="Viridis",
                marker_opacity=0.7,
                marker_line_width=0.5,
                marker_line_color="white",
                text=df_batiments.apply(
                    lambda x: f"{x['nb_transactions']} transaction(s)<br>Prix m²: {x['prix_m2_moyen']:,.0f}€<br>Prix moyen: {x['prix_moyen']/1e6:.2f}M€",
                    axis=1
                ),
                hovertemplate='<b>Bâtiment</b><br>%{text}<extra></extra>',
                colorbar=dict(
                    title=dict(
                        text="Prix m²<br>(€)",
                        side="right"
                    ),
                    tickformat=",",
                    len=0.7,
                )
            ))

            # Centrer sur Paris
            fig.update_layout(
                mapbox=dict(
                    style="carto-positron",
                    center=dict(lat=48.856, lon=2.352),
                    zoom=11.5
                ),
                title=f"Bâtiments parisiens avec transactions immobilières ({len(df_batiments):,} bâtiments)",
                height=700,
            )

            styliser_fig(fig)
            st.plotly_chart(fig, use_container_width=True, key="map_batiments")

        else:  # niveau_detail == "Points"
            # Vue par points de transaction
            color_by = {
                "Arrondissement": "arrondissement",
                "Prix au m²": "prix_m2",
                "Type de bien": "type_local",
                "Type de vente": "nature_mutation"
            }[color_by_display]

            kwargs = {
                "data_frame": df_map,
                "lat": "latitude",
                "lon": "longitude",
                "hover_name": "type_local",
                "hover_data": {
                    "valeur_fonciere": ":,.0f",
                    "prix_m2": ":,.0f",
                    "surface_reelle_bati": ":.0f",
                    "arrondissement": True,
                    "date_mutation": True,
                    "latitude": False,
                    "longitude": False
                },
                "zoom": 11.5,
                "title": f"{len(df_map):,} transactions géolocalisées à paris",
                "height": 700,
            }
            if color_by == "prix_m2":
                kwargs["color"] = "prix_m2"
                kwargs["color_continuous_scale"] = "Viridis"
            else:
                kwargs["color"] = color_by
                kwargs["color_discrete_sequence"] = px.colors.sequential.PuBuGn

            fig = px.scatter_mapbox(**kwargs)
            fig.update_layout(mapbox_style="carto-positron")
            fig.update_traces(marker={"size": 8, "opacity": 0.6})
            styliser_fig(fig)
            st.plotly_chart(fig, use_container_width=True)
