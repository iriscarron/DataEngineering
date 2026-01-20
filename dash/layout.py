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
    st.set_page_config(page_title="DVF Paris", layout="wide", page_icon="🏠")


def apply_theme():
    """Applique le theming global: tons bleus, fond noir, filtres verts turquoise."""
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        :root {{
            --primary:#0ea5e9;
            --accent:#2563eb;
            --muted:#1a1a2e;
            --text:#ffffff;
        }}
        html, body, [data-testid="stAppViewContainer"] {{
            font-family: 'Inter', sans-serif;
            color: #ffffff;
            background: linear-gradient(135deg, #0f0f1e 0%, #1a1a2e 50%, #16213e 100%);
        }}
        [data-testid="stSidebar"] {{
            background: linear-gradient(135deg, #0f0f1e 0%, #1a1a2e 50%, #16213e 100%) !important;
            color: #ffffff;
        }}
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] label {{
            color: #ffffff !important;
            font-weight: 600;
        }}
        /* Boutons de filtre */
        [data-testid="stSidebar"] button {{
            background: linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%) !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
        }}
        [data-testid="stSidebar"] button:hover {{
            background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%) !important;
        }}
        /* Inputs et sliders */
        [data-testid="stSidebar"] [role="slider"] {{
            accent-color: #06b6d4;
        }}
        [data-testid="stSidebar"] input {{
            background-color: #16213e !important;
            color: #ffffff !important;
            border: 1px solid #0ea5e9 !important;
            border-radius: 6px !important;
        }}
        /* Multiselect */
        [data-testid="stSidebar"] [role="combobox"] {{
            background-color: #16213e !important;
            color: #ffffff !important;
            border: 1px solid #0ea5e9 !important;
        }}
        .metric-card {{
            background: linear-gradient(135deg, #0f2f4f 0%, #1a3a52 100%);
            border: 1px solid #0ea5e9;
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 2px 8px rgba(14, 165, 233, 0.2);
            color: #ffffff;
        }}
        .block-container {{
            padding-top: 1.2rem;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #ffffff !important;
            font-weight: 700 !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def styliser_fig(fig):
    """Uniformise la mise en forme des figures Plotly: fond noir, texte blanc, bleu."""
    fig.update_layout(
        font=dict(family="Inter", color="#ffffff", size=12),
        title_font=dict(size=18, color="#ffffff", family="Inter", weight=700),
        plot_bgcolor="#0f0f1e",
        paper_bgcolor="#1a1a2e",
        hoverlabel=dict(bgcolor="#16213e", font_size=12, font_family="Inter", namelength=-1, font_color="#ffffff"),
        margin=dict(t=60, b=40, l=40, r=20),
        legend=dict(orientation="h", y=-0.25, x=0, title=None, font=dict(color="#ffffff")),
        colorway=COLORWAY,
        hovermode="closest",
        xaxis=dict(showgrid=True, gridwidth=1, gridcolor="#334155"),
        yaxis=dict(showgrid=True, gridwidth=1, gridcolor="#334155"),
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


def render_filters(df):
    """Affiche les filtres et renvoie le dataframe filtre + params."""
    if df.empty:
        return df, {"seuil_percentile": 95}

    with st.sidebar:
        st.header("Filtres")

        min_date = df["date_mutation"].min().date()
        max_date = df["date_mutation"].max().date()

        date_range = st.date_input(
            "Periode",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )

        arrondissements = sorted(
            df["arrondissement"].dropna().unique(),
            key=lambda x: int(x) if str(x).isdigit() else 0,
        )
        arr_selected = st.multiselect(
            "Arrondissements",
            arrondissements,
            default=arrondissements,
        )

        types = sorted(df["type_local"].dropna().unique())
        types_selected = st.multiselect(
            "Type de bien",
            types,
            default=types,
        )

        if "nature_mutation" in df.columns:
            natures = sorted(df["nature_mutation"].dropna().unique())
            natures_selected = st.multiselect(
                "Type de vente",
                natures,
                default=natures,
            )
        else:
            natures_selected = []

        st.subheader("Filtres prix")
        max_valeur = int(df["valeur_fonciere"].max()) if not df.empty else 1
        slider_top = int(df["valeur_fonciere"].quantile(0.99)) if not df.empty else max_valeur
        prix_min, prix_max = st.slider(
            "Plage de prix (euros)",
            min_value=0,
            max_value=max(max_valeur, 1),
            value=(0, max(slider_top, 1)),
        )

        seuil_percentile = st.slider(
            "Seuil grosses ventes (percentile)",
            min_value=80,
            max_value=99,
            value=95,
        )

    if len(date_range) == 2:
        mask = (
            (df["date_mutation"].dt.date >= date_range[0])
            & (df["date_mutation"].dt.date <= date_range[1])
            & (df["arrondissement"].isin(arr_selected))
            & (df["type_local"].isin(types_selected))
            & (df["valeur_fonciere"] >= prix_min)
            & (df["valeur_fonciere"] <= prix_max)
        )
        if natures_selected and "nature_mutation" in df.columns:
            mask = mask & (df["nature_mutation"].isin(natures_selected))
        df_filtre = df[mask].copy()
    else:
        df_filtre = df.copy()

    return df_filtre, {
        "date_range": date_range,
        "arrondissements": arr_selected,
        "types": types_selected,
        "natures": natures_selected,
        "prix_min": prix_min,
        "prix_max": prix_max,
        "seuil_percentile": seuil_percentile,
    }
