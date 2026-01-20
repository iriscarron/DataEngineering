import streamlit as st
import plotly.express as px

from dash.layout import styliser_fig


def render_carte_region(df):
    """Carte de chaleur sur Paris pour visualiser la densite ou les prix."""
    if df.empty:
        st.info("Aucune donnee pour afficher la carte regionale.")
        return

    df_map = df.dropna(subset=["latitude", "longitude"])
    if df_map.empty:
        st.info("Pas de coordonnees disponibles pour la carte.")
        return

    center_lat = df_map["latitude"].mean()
    center_lon = df_map["longitude"].mean()

    fig = px.density_mapbox(
        df_map,
        lat="latitude",
        lon="longitude",
        z="prix_m2",
        radius=18,
        center=dict(lat=center_lat, lon=center_lon),
        zoom=11,
        title="Chaleur des prix au m2",
        height=650,
    )
    fig.update_layout(mapbox_style="carto-positron", coloraxis_colorscale="YlOrRd")
    styliser_fig(fig)
    st.plotly_chart(fig, use_container_width=True)
