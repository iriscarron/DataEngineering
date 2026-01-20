import streamlit as st
import plotly.express as px

from dash.layout import styliser_fig


def render_carte(df):
    """Carte des transactions geolocalisees."""
    if df.empty:
        st.info("Aucune donnee pour afficher la carte.")
        return

    df_map = df.dropna(subset=["latitude", "longitude"])
    if df_map.empty:
        st.info("Pas de coordonnees disponibles pour la carte.")
        return

    fig = px.scatter_mapbox(
        df_map,
        lat="latitude",
        lon="longitude",
        color="arrondissement",
        hover_name="type_local",
        hover_data={
            "valeur_fonciere": True,
            "prix_m2": True,
            "surface_reelle_bati": True,
            "arrondissement": True,
        },
        zoom=11,
        title="Transactions geolocalisees",
        height=650,
    )
    fig.update_layout(mapbox_style="carto-positron")
    fig.update_traces(marker=dict(size=9, opacity=0.6))
    styliser_fig(fig)
    st.plotly_chart(fig, use_container_width=True)
