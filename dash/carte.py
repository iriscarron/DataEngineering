"""carte interactive des transactions geolocalisees."""
import streamlit as st
import plotly.express as px

from dash import layout
from dash.layout import styliser_fig


def render_carte(df):
    """carte des transactions geolocalisees."""
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

        st.markdown(f"## carte - {len(df_map):,} transactions")
        st.markdown("---")

        # options d'affichage
        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            color_by_display = st.selectbox(
                "colorer par",
                ["arrondissement", "prix au m²", "type de bien", "type de vente"],
                index=1
            )
            color_by = {
                "arrondissement": "arrondissement",
                "prix au m²": "prix_m2",
                "type de bien": "type_local",
                "type de vente": "nature_mutation"
            }[color_by_display]
        with col_opt2:
            size_by_display = st.selectbox(
                "taille par",
                ["surface", "prix", "uniforme"],
                index=0
            )
            size_by = {
                "surface": "surface_reelle_bati",
                "prix": "valeur_fonciere",
                "uniforme": "uniforme"
            }[size_by_display]
        # carte scatter mapbox
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
        if size_by != "uniforme":
            kwargs["size"] = size_by
        fig = px.scatter_mapbox(**kwargs)
        fig.update_layout(mapbox_style="carto-positron")
        # style des marqueurs selon le choix
        if size_by == "uniforme":
            fig.update_traces(marker={"size": 8, "opacity": 0.6})
        else:
            fig.update_traces(marker={"opacity": 0.7})
        styliser_fig(fig)
        st.plotly_chart(fig, use_container_width=True)
