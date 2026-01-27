"""Layout, theming, and data loading utilities for DVF Paris Analytics."""

import os
import pandas as pd
import streamlit as st
import plotly.express as px
from sqlalchemy import create_engine

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dvf:dvf@localhost:5432/dvf")

PRIMARY_COLOR = "#0ea5e9"
SECONDARY_COLOR = "#06b6d4"
ACCENT_COLOR = "#2563eb"
MUTED_BG = "#1a1a2e"
TEXT_COLOR = "#ffffff"
COLORWAY = [
    "#0ea5e9",
    "#06b6d4",
    "#2563eb",
    "#3b82f6",
    "#60a5fa",
    "#93c5fd",
]

px.defaults.template = "plotly_white"
px.defaults.color_discrete_sequence = COLORWAY


def configure_page():
    """Configure la page Streamlit (doit etre appele en premier)."""
    st.set_page_config(page_title="DVF Paris", layout="wide")


def apply_theme():
    """Applique le theming global: tons clairs, fond beige."""
    st.markdown(
        """
        <style>
        @import url(
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        :root {{
            --primary:#2c5f2d;
            --accent:#97bc62;
            --muted:#f5f1e8;
            --text:#2d3436;
        }}
        html, body, [data-testid="stAppViewContainer"] {{
            font-family: 'Inter', sans-serif;
            color: #2d3436;
            background: #f5f1e8;
        }}
        [data-testid="stSidebar"] {{
            background: #faf8f3 !important;
            color: #2d3436;
            border-right: 1px solid #e0ddd5;
        }}
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3, [data-testid="stSidebar"] label {{
            color: #2d3436 !important;
            font-weight: 600;
        }}
        /* Boutons de filtre */
        [data-testid="stSidebar"] button {{
            background: #2c5f2d !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 6px !important;
            font-weight: 500 !important;
        }}
        [data-testid="stSidebar"] button:hover {{
            background: #3d7a3e !important;
        }}
        /* Inputs et sliders */
        [data-testid="stSidebar"] [role="slider"] {{
            accent-color: #2c5f2d;
        }}
        [data-testid="stSidebar"] input {{
            background-color: #ffffff !important;
            color: #2d3436 !important;
            border: 1px solid #d0cdc5 !important;
            border-radius: 6px !important;
        }}
        /* Multiselect */
        [data-testid="stSidebar"] [role="combobox"] {{
            background-color: #ffffff !important;
            color: #2d3436 !important;
            border: 1px solid #d0cdc5 !important;
        }}
        .metric-card {{
            background: #ffffff;
            border: 1px solid #e0ddd5;
            border-radius: 8px;
            padding: 16px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            color: #2d3436;
        }}
        .block-container {{
            padding-top: 1.2rem;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #2d3436 !important;
            font-weight: 700 !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def styliser_fig(fig):
    """Uniformise la mise en forme des figures Plotly: fond clair."""
    fig.update_layout(
        font={"family": "Inter", "color": "#2d3436", "size": 12},
        title_font={"size": 18, "color": "#2d3436", "family": "Inter", "weight": 700},
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        hoverlabel={
            "bgcolor": "#f5f1e8",
            "font_size": 12,
            "font_family": "Inter",
            "namelength": -1,
            "font_color": "#2d3436"
        },
        margin={"t": 60, "b": 40, "l": 40, "r": 20},
        legend={"orientation": "h", "y": -0.25,
                "x": 0, "title": None, "font": {"color": "#2d3436"}},
        colorway=COLORWAY,
        hovermode="closest",
        xaxis={"showgrid": True, "gridwidth": 1, "gridcolor": "#e0ddd5"},
        yaxis={"showgrid": True, "gridwidth": 1, "gridcolor": "#e0ddd5"},
    )
    return fig


@st.cache_data(show_spinner=False)
def charger_donnees():
    """Charge les donnees depuis PostgreSQL."""
    try:
        engine = create_engine(DATABASE_URL)
        query = (
            """
            SELECT
                date_mutation, valeur_fonciere, surface_reelle_bati,
                prix_m2, nb_pieces, type_local, nature_mutation,
                code_postal, arrondissement, latitude, longitude
            FROM transactions
            WHERE valeur_fonciere IS NOT NULL
            ORDER BY date_mutation DESC
            """
        )
        df = pd.read_sql(query, engine)
        df["date_mutation"] = pd.to_datetime(df["date_mutation"])
        return df
    except Exception as e:  # pylint: disable=broad-except
        st.error(f"Erreur de connexion a la base: {e}")
        return pd.DataFrame()


@st.cache_data(show_spinner=False, ttl=3600)
def charger_batiments_avec_transactions(df_transactions):
    """Charge les batiments avec leurs transactions associees (optimisé)."""
    try:
        engine = create_engine(DATABASE_URL)

        # Optimisé: on limite aux bâtiments avec transactions et on utilise un index spatial
        query = """
            WITH trans AS (
                SELECT
                    latitude, longitude, valeur_fonciere, prix_m2,
                    type_local, arrondissement, date_mutation,
                    ST_SetSRID(ST_MakePoint(longitude, latitude), 4326) as geom_point
                FROM transactions
                WHERE latitude IS NOT NULL
                AND longitude IS NOT NULL
                AND valeur_fonciere IS NOT NULL
            ),
            batiments_avec_trans AS (
                SELECT DISTINCT b.id
                FROM batiments b
                INNER JOIN trans t ON ST_DWithin(b.geom, t.geom_point, 0.0001)
                LIMIT 5000
            )
            SELECT
                b.id as batiment_id,
                ST_AsGeoJSON(ST_Simplify(b.geom, 0.00001)) as geometry,
                b.commune,
                COUNT(t.latitude) as nb_transactions,
                AVG(t.valeur_fonciere) as prix_moyen,
                AVG(t.prix_m2) as prix_m2_moyen,
                MAX(t.date_mutation) as derniere_transaction
            FROM batiments b
            INNER JOIN batiments_avec_trans bat ON b.id = bat.id
            LEFT JOIN trans t ON ST_DWithin(b.geom, t.geom_point, 0.0001)
            GROUP BY b.id, b.geom, b.commune
        """

        df = pd.read_sql(query, engine)
        return df
    except Exception as e:  # pylint: disable=broad-except
        st.error(f"Erreur de chargement des bâtiments: {e}")
        return pd.DataFrame()


def render_filters_sidebar(df, show_percentile=False):
    """affiche les filtres dans une sidebar et renvoie le dataframe filtre."""
    if df.empty:
        return df

    st.markdown("## filtres")
    st.markdown("---")

    # periode
    date_range = st.date_input(
        "période",
        value=(df["date_mutation"].min().date(), df["date_mutation"].max().date()),
        min_value=df["date_mutation"].min().date(),
        max_value=df["date_mutation"].max().date(),
    )

    # arrondissements
    arrondissements = sorted(
        df["arrondissement"].dropna().unique(),
        key=lambda x: int(x) if str(x).isdigit() else 0,
    )
    arr_selected = st.multiselect("arrondissements", arrondissements, default=arrondissements)

    # type de bien
    types = sorted(df["type_local"].dropna().unique())
    types_selected = st.multiselect("type de bien", types, default=types)

    # type de vente
    if "nature_mutation" in df.columns:
        natures = sorted(df["nature_mutation"].dropna().unique())
        natures_selected = st.multiselect("type de vente", natures, default=natures)
    else:
        natures_selected = []

    # prix avec champs de saisie
    st.markdown("**plage de prix (€)**")
    col_prix1, col_prix2 = st.columns(2)
    with col_prix1:
        prix_min = st.number_input(
            "de",
            min_value=0,
            max_value=int(df["valeur_fonciere"].max()) if not df.empty else 1000000,
            value=0,
            step=10000,
            format="%d"
        )
    with col_prix2:
        prix_max = st.number_input(
            "à",
            min_value=0,
            max_value=int(df["valeur_fonciere"].max()) if not df.empty else 10000000,
            value=int(df["valeur_fonciere"].quantile(0.99)) if not df.empty else 5000000,
            step=10000,
            format="%d"
        )

    # seuil grosses ventes (optionnel)
    seuil_percentile = 95
    if show_percentile:
        seuil_percentile = st.slider(
            "seuil grosses ventes (%)",
            min_value=80,
            max_value=99,
            value=95,
        )

    # application des filtres
    if len(date_range) == 2:
        mask = (
            (df["date_mutation"].dt.date >= date_range[0])
            & (df["date_mutation"].dt.date <= date_range[1])
            & (df["valeur_fonciere"] >= prix_min)
            & (df["valeur_fonciere"] <= prix_max)
        )

        # Filtre arrondissement
        if arr_selected:
            mask = mask & (df["arrondissement"].isin(arr_selected))

        # Filtre type de bien
        if types_selected:
            mask = mask & (df["type_local"].isin(types_selected))

        # Filtre type de vente
        if natures_selected and "nature_mutation" in df.columns:
            mask = mask & (df["nature_mutation"].isin(natures_selected))

        df_filtre = df[mask].copy()
    else:
        df_filtre = df.copy()

    st.markdown(f"**{len(df_filtre):,}** transactions affichées")

    return df_filtre
