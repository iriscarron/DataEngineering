import os
from datetime import datetime
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st


st.set_page_config(page_title="DVF Paris", layout="wide")


def get_engine_url() -> str:
	# Placeholder: use env var if present, fallback to local dev
	return os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/dvf")


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
	# TODO: remplacer par une requete Postgres + PostGIS
	sample_path = "data/sample_dvf.parquet"
	if os.path.exists(sample_path):
		return pd.read_parquet(sample_path)

	rng = pd.date_range("2022-01-01", periods=120, freq="W")
	arr = np.random.choice([f"75{str(i).zfill(3)}" for i in range(1, 21)], size=len(rng))
	valeurs = np.random.lognormal(mean=12, sigma=0.6, size=len(rng))
	surfaces = np.random.uniform(20, 120, size=len(rng))
	df = pd.DataFrame(
		{
			"date_mutation": rng,
			"valeur_fonciere": valeurs,
			"surface_reelle_bati": surfaces,
			"prix_m2": valeurs / surfaces,
			"type_local": np.random.choice(["Appartement", "Local", "Maison"], size=len(rng)),
			"code_postal": arr,
			"arrondissement": np.random.choice([str(i) for i in range(1, 21)], size=len(rng)),
		}
	)
	return df


def chart_timeline(df: pd.DataFrame):
	if df.empty:
		return None
	ts = df.copy()
	ts["date_mutation"] = pd.to_datetime(ts["date_mutation"])
	ts["annee_mois"] = ts["date_mutation"].dt.to_period("M").astype(str)
	agg = ts.groupby("annee_mois").size().reset_index(name="nb")
	return px.bar(agg, x="annee_mois", y="nb", title="Transactions dans le temps")


def chart_big_sales(df: pd.DataFrame):
	if df.empty:
		return None
	seuil = df["valeur_fonciere"].quantile(0.95)
	flagged = df[df["valeur_fonciere"] >= seuil].copy()
	flagged["date_mutation"] = pd.to_datetime(flagged["date_mutation"])
	return px.scatter(
		flagged,
		x="date_mutation",
		y="valeur_fonciere",
		color="arrondissement",
		title="Grosses ventes (p95)",
	)


def chart_arrondissement(df: pd.DataFrame):
	if df.empty:
		return None
	agg = df.groupby("arrondissement")["valeur_fonciere"].median().reset_index()
	return px.bar(agg, x="arrondissement", y="valeur_fonciere", title="Prix median par arrondissement")


def chart_price_per_m2(df: pd.DataFrame):
	if df.empty:
		return None
	return px.box(df, x="arrondissement", y="prix_m2", color="arrondissement", title="Distribution prix au m2")


def chart_price_by_type(df: pd.DataFrame):
	if df.empty:
		return None
	agg = df.groupby("type_local")["valeur_fonciere"].median().reset_index()
	return px.bar(agg, x="type_local", y="valeur_fonciere", title="Prix median par type de bien")


def main():
	st.title("DVF Paris – Streamlit")
	st.caption("Postgres/PostGIS pour la BDD. Remplacer les donnees factices par la BDD DVF.")

	df = load_data()
	if df.empty:
		st.warning("Aucune donnee chargee. Charger le DVF dans la BDD ou placer un sample dans data/.")
		return

	min_date = pd.to_datetime(df["date_mutation"]).min()
	max_date = pd.to_datetime(df["date_mutation"]).max()

	with st.sidebar:
		st.header("Filtres")
		date_min, date_max = st.date_input(
			"Plage de dates",
			value=(min_date.date(), max_date.date()),
			min_value=min_date.date(),
			max_value=max_date.date(),
		)
		arr_options = sorted(df["arrondissement"].dropna().unique())
		arr_selected = st.multiselect("Arrondissements", arr_options, default=arr_options)
		types_options = sorted(df["type_local"].dropna().unique())
		types_selected = st.multiselect("Types", types_options, default=types_options)

	mask = (
		(pd.to_datetime(df["date_mutation"]).dt.date >= date_min)
		& (pd.to_datetime(df["date_mutation"]).dt.date <= date_max)
		& (df["arrondissement"].isin(arr_selected))
		& (df["type_local"].isin(types_selected))
	)
	filtered = df[mask].copy()

	st.subheader("Apercu donnees")
	st.dataframe(filtered.head(50))

	col1, col2 = st.columns(2)
	with col1:
		fig = chart_timeline(filtered)
		if fig:
			st.plotly_chart(fig, use_container_width=True)
	with col2:
		fig = chart_big_sales(filtered)
		if fig:
			st.plotly_chart(fig, use_container_width=True)

	col3, col4 = st.columns(2)
	with col3:
		fig = chart_arrondissement(filtered)
		if fig:
			st.plotly_chart(fig, use_container_width=True)
	with col4:
		fig = chart_price_per_m2(filtered)
		if fig:
			st.plotly_chart(fig, use_container_width=True)

	fig = chart_price_by_type(filtered)
	if fig:
		st.plotly_chart(fig, use_container_width=True)

	st.info("Branches a implementer : requetes Postgres, carte GeoJSON, detection outliers ajustable.")


if __name__ == "__main__":
	main()
