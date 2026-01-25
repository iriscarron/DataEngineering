"""Carte interactive des transactions géolocalisées."""
import streamlit as st
import plotly.express as px

from dash.layout import styliser_fig


def render_carte(df):
    """Carte des transactions géolocalisées avec design premium."""
    if df.empty:
        st.info("Aucune donnée pour afficher la carte.")
        return

    df_map = df.dropna(subset=["latitude", "longitude"])
    if df_map.empty:
        st.info("Pas de coordonnées disponibles pour la carte.")
        return

    # En-tête de section
    st.markdown(
        """
        <div style='background: linear-gradient(135deg, #0f2f4f 0%, #1a3a52 100%);
                    padding: 1.5rem; border-radius: 12px; margin-bottom: 1.5rem;
                    border: 1px solid #0ea5e9;
                    box-shadow: 0 4px 12px rgba(14, 165, 233, 0.3);'>
            <h2 style='color: #0ea5e9; margin: 0;'>
                Cartographie Interactive des Transactions
            </h2>
            <p style='color: #94a3b8; margin-top: 0.5rem;'>
                Visualisation géographique de {len(df_map):,}
                transactions à Paris
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    # Options d'affichage
    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        color_by = st.selectbox(
            "Colorer par",
            ["arrondissement", "prix_m2", "type_local", "nature_mutation"],
            index=1
        )
    with col_opt2:
        size_by = st.selectbox(
            "Taille par",
            ["surface_reelle_bati", "valeur_fonciere", "uniforme"],
            index=0
        )
    # Carte scatter mapbox améliorée
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
        "title": f"{len(df_map):,} transactions géolocalisées à Paris",
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
    # Style des marqueurs selon le choix
    if size_by == "uniforme":
        fig.update_traces(marker={"size": 8, "opacity": 0.6})
    else:
        fig.update_traces(marker={"opacity": 0.7})
    styliser_fig(fig)
    st.plotly_chart(fig, use_container_width=True)
    # Légende interactive
    st.markdown(
        """
        <div style='background: #0f2f4f; padding: 1rem; border-radius: 8px; margin-top: 1rem;
                    border: 1px solid #0ea5e9;'>
            <div style='color: #0ea5e9; font-weight: 600; margin-bottom: 0.5rem;'>Astuce</div>
            <div style='color: #94a3b8; font-size: 0.9rem;'>
                • Cliquez et faites glisser pour vous déplacer sur la carte<br>
                • Utilisez la molette pour zoomer/dézoomer<br>
                • Survolez les points pour voir les détails des transactions
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
