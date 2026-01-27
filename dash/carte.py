"""carte interactive des transactions geolocalisees avec batiments cadastraux."""
import json
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

from dash import layout
from dash.layout import styliser_fig


def render_carte(df):
    """carte des transactions avec polygones des batiments."""
    if df.empty:
        st.info("aucune donnée pour afficher la carte.")
        return

    # layout: filtres a gauche, contenu a droite
    col_filtre, col_contenu = st.columns([1, 3])

    with col_filtre:
        df_filtre = layout.render_filters_sidebar(df, show_percentile=False)

    with col_contenu:
        df_map = df_filtre.dropna(subset=["latitude", "longitude"])
        if df_map.empty:
            st.info("pas de coordonnées disponibles pour la carte.")
            return

        st.markdown(f"## Carte - {len(df_map):,} transactions")
        st.markdown("---")

        # option d'affichage
        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            mode_affichage = st.selectbox(
                "Mode d'affichage",
                ["Bâtiments (polygones)", "Points de transaction"],
                index=0
            )
        with col_opt2:
            if mode_affichage == "Bâtiments (polygones)":
                color_by_display = st.selectbox(
                    "Colorer par",
                    ["Prix au m² moyen"],
                    index=0
                )
            else:
                color_by_display = st.selectbox(
                    "Colorer par",
                    ["Arrondissement", "Prix au m²", "Type de bien", "Type de vente"],
                    index=1
                )

        if mode_affichage == "Bâtiments (polygones)":
            # Charger les bâtiments avec transactions
            with st.spinner("chargement des bâtiments..."):
                df_batiments = layout.charger_batiments_avec_transactions(df_map)

            if df_batiments.empty:
                st.warning("aucun bâtiment avec transaction trouvé.")
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
                title=f"{len(df_batiments):,} bâtiments avec transactions à Paris",
                height=700,
            )

            styliser_fig(fig)
            st.plotly_chart(fig, use_container_width=True)

        else:
            # Mode points (ancien affichage)
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
