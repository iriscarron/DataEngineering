"""
Page de recherche Elasticsearch avec interface visuelle optimale
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import re
from dash.layout import styliser_fig, SECONDARY_COLOR
from etl.elasticsearch_utils import elasticsearch_disponible, get_es_client, INDEX_NAME


def rechercher_avec_arrondissement(query, filtres=None, taille=100):
    """Recherche avec detection automatique de l'arrondissement."""
    es = get_es_client()

    must_clauses = []
    filter_clauses = []

    query_originale = query  # DEBUG

    # Detecter l'arrondissement dans la query
    # Pattern amélioré: gère 1-20, tous les suffixes (e, ème, er, etc.)
    # (?<!\d) = pas précédé d'un chiffre, (?!\w) = pas suivi d'un caractère mot
    pattern = r'(?<!\d)(20|1[0-9]|[1-9])\s*(e|è|ème|eme|er|ère|re|ième|ieme)(?!\w)'
    match = re.search(pattern, query or "", re.IGNORECASE)

    arr_detecte = None  # DEBUG
    if match:
        arr_num = match.group(1)  # Le groupe 1 capture directement le numéro
        if 1 <= int(arr_num) <= 20:
            arr_detecte = arr_num  # DEBUG
            # Ajouter filtre arrondissement
            filter_clauses.append({"term": {"arrondissement": arr_num}})
            # Retirer l'arrondissement de la query
            query = re.sub(pattern, ' ', query, flags=re.IGNORECASE).strip()
            # Nettoyer les espaces multiples
            query = re.sub(r'\s+', ' ', query).strip()

    if query and query.strip():
        must_clauses.append({
            "multi_match": {
                "query": query,
                "fields": ["recherche_complete^3", "type_local^2", "nature_mutation"],
                "fuzziness": "AUTO"
            }
        })

    if filtres:
        if filtres.get("prix_max") is not None:
            filter_clauses.append({"range": {"valeur_fonciere": {"lte": filtres["prix_max"]}}})

    if not must_clauses and not filter_clauses:
        body = {"query": {"match_all": {}}, "size": taille}
    else:
        body = {
            "query": {
                "bool": {
                    "must": must_clauses if must_clauses else [{"match_all": {}}],
                    "filter": filter_clauses
                }
            },
            "size": taille,
            "sort": [{"date_mutation": "desc"}]
        }

    try:
        response = es.search(index=INDEX_NAME, body=body)
        return [hit["_source"] for hit in response["hits"]["hits"]]
    except Exception as e:
        st.error(f"Erreur recherche: {e}")
        return []


def render_recherche(_df):
    """Interface de recherche Elasticsearch avec design moderne."""

    st.markdown(
		"""
		<div style='background: linear-gradient(135deg, #3d2817 0%, #5b3a22 100%);
					padding: 2rem; border-radius: 16px; margin-bottom: 2rem;
					border: 1px solid #8b7355; box-shadow: 0 4px 16px rgba(61, 40, 23, 0.35);'>
			<h2 style='color: #e6dcc8; margin: 0; font-size: 2rem;'>
				RECHERCHE
			</h2>
			<p style='color: #d6c6a8; margin-top: 0.5rem; font-size: 1.1rem;'>
				Moteur de recherche Elasticsearch avec recherche floue et filtres avancés
			</p>
		</div>
		""",
		unsafe_allow_html=True,
	)

    if not elasticsearch_disponible():
        st.error("Elasticsearch n'est pas disponible ou l'index est vide. " \
        "Lancez d'abord le scraper.")
        st.info(
            "Commande: `python etl/scraper.py` " \
            "ou attendez que le scraping se termine dans le conteneur."
        )
        return
    col_search, col_budget = st.columns([3, 1])

    with col_search:
        query = st.text_input(
			"Rechercher une transaction",
			placeholder="Ex: appartement 16eme, maison 5 pieces, local commercial...",
			help="Recherche intelligente avec fuzzy matching et analyse en français",
		)

    with col_budget:
        budget_max = st.number_input(
			"Budget max (€)",
			min_value=0,
			max_value=50000000,
			value=5000000,
			step=100000,
			help="Filtrer les résultats par budget maximum",
		)

    _, col_btn2, _ = st.columns([1, 2, 1])
    with col_btn2:
        rechercher = st.button(
			"Lancer la recherche",
			use_container_width=True,
			type="primary",
		)

    if rechercher or query:
        with st.spinner("Recherche en cours dans Elasticsearch..."):
            filtres = {"prix_max": budget_max} if budget_max else None
            resultats = rechercher_avec_arrondissement(query or "", filtres=filtres, taille=100)

        if not resultats:
            st.warning("Aucun résultat trouvé. Essayez une autre recherche.")
            return
        df_resultats = pd.DataFrame(resultats)
        df_resultats["date_mutation"] = pd.to_datetime(
			df_resultats["date_mutation"], errors="coerce"
		)

        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(
				f"""
				<div style='background: linear-gradient(135deg, #8b5a2b 0%, #a67c52 100%);
							padding: 1.5rem; border-radius: 12px; text-align: center;
							box-shadow: 0 4px 12px rgba(139, 90, 43, 0.4);'>
					<div style='font-size: 2.5rem; font-weight: 700; color: white;'>{len(resultats)}</div>
					<div style='color: #f5efe6; font-size: 0.9rem; margin-top: 0.3rem;'>Résultats</div>
				</div>
				""",
				unsafe_allow_html=True,
			)

        with col2:
            prix_moyen = df_resultats["valeur_fonciere"].mean()
            st.markdown(
				f"""
				<div style='background: linear-gradient(135deg, #6b3f1d 0%, #8b5a2b 100%);
							padding: 1.5rem; border-radius: 12px; text-align: center;
							box-shadow: 0 4px 12px rgba(107, 63, 29, 0.4);'>
					<div style='font-size: 2.5rem; font-weight: 700; color: white;'>{prix_moyen/1e6:.2f}M€</div>
					<div style='color: #f1e6d6; font-size: 0.9rem; margin-top: 0.3rem;'>Prix moyen</div>
				</div>
				""",
				unsafe_allow_html=True,
			)

        with col3:
            prix_m2_med = df_resultats["prix_m2"].median()
            st.markdown(
				f"""
				<div style='background: linear-gradient(135deg, #9c6b3b 0%, #b08968 100%);
							padding: 1.5rem; border-radius: 12px; text-align: center;
							box-shadow: 0 4px 12px rgba(156, 107, 59, 0.4);'>
					<div style='font-size: 2.5rem; font-weight: 700; color: white;'>{prix_m2_med:,.0f}€</div>
					<div style='color: #f5efe6; font-size: 0.9rem; margin-top: 0.3rem;'>Prix/m² médian</div>
				</div>
				""",
				unsafe_allow_html=True,
			)

        with col4:
            surface_moy = df_resultats["surface_reelle_bati"].mean()
            st.markdown(
				f"""
				<div style='background: linear-gradient(135deg, #8b5a2b 0%, #a67c52 100%);
							padding: 1.5rem; border-radius: 12px; text-align: center;
							box-shadow: 0 4px 12px rgba(139, 90, 43, 0.4);'>
					<div style='font-size: 2.5rem; font-weight: 700; color: white;'>{surface_moy:.0f}m²</div>
					<div style='color: #f5efe6; font-size: 0.9rem; margin-top: 0.3rem;'>Surface moyenne</div>
				</div>
				""",
				unsafe_allow_html=True,
			)

        st.markdown("<br>", unsafe_allow_html=True)

        tab1, tab2, tab3 = st.tabs(["Liste des résultats", "Graphiques", "Carte"])

        with tab1:
            st.subheader(f"{len(resultats)} transactions trouvées")

            for _, row in df_resultats.head(20).iterrows():
                with st.container():
                    col_info, col_prix = st.columns([3, 1])
                    with col_info:
                        arr = row.get("arrondissement", "?")
                        date_val = row.get("date_mutation", "")
                        date_txt = date_val.strftime("%d/%m/%Y") if pd.notna(date_val) else "N/A"
                        st.markdown(
							f"""
							<div style='background: linear-gradient(135deg, #3d2817 0%, #5b3a22 100%);
										padding: 1rem; border-radius: 10px; margin-bottom: 0.8rem;
										border-left: 4px solid #d4a574;
										box-shadow: 0 2px 8px rgba(212, 165, 116, 0.2);'>
								<div style='color: #d4a574; font-weight: 600; font-size: 1.1rem;'>
									{row.get("type_local", "N/A")} - Paris {arr}ème
								</div>
								<div style='color: #d6c6a8; font-size: 0.85rem; margin-top: 0.3rem;'>
									Date: {date_txt}
									&nbsp;&nbsp;|&nbsp;&nbsp;
									Surface: {row.get("surface_reelle_bati", 0):.0f} m²
									&nbsp;&nbsp;|&nbsp;&nbsp;
									Vente: {row.get("nature_mutation", "Vente")}
								</div>
							</div>
							""",
							unsafe_allow_html=True,
						)

                    with col_prix:
                        prix = row.get("valeur_fonciere", 0)
                        prix_m2 = row.get("prix_m2", 0)
                        st.markdown(
							f"""
							<div style='background: linear-gradient(135deg, #a67c52 0%, #c8956a 100%);
										padding: 1rem; border-radius: 10px; text-align: center;
										box-shadow: 0 2px 8px rgba(212, 165, 116, 0.3);'>
								<div style='font-size: 1.8rem; font-weight: 700; color: white;'>
									{prix/1e6:.2f}M€
								</div>
								<div style='color: #f5efe6; font-size: 0.8rem;'>
									{prix_m2:,.0f}€/m²
								</div>
							</div>
							""",
							unsafe_allow_html=True,
						)

            if len(df_resultats) > 20:
                st.info(f"Affichage de 20 résultats sur {len(df_resultats)} trouvés")

        with tab2:
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                agg_arr = df_resultats.groupby("arrondissement").agg({
					"valeur_fonciere": ["mean", "count"]
				}).reset_index()
                agg_arr.columns = ["arrondissement", "prix_moyen", "count"]

                fig = px.bar(
					agg_arr,
					x="arrondissement",
					y="count",
					color="prix_moyen",
					title="Résultats par arrondissement",
					labels={"arrondissement": "Arrondissement", "count": "Nombre", "prix_moyen": "Prix moyen"},
					color_continuous_scale="Blues",
				)
            fig.update_traces(marker_line_width=0)
            styliser_fig(fig)
            st.plotly_chart(fig, use_container_width=True)

            with col_g2:
                fig = px.histogram(
					df_resultats,
					x="valeur_fonciere",
					nbins=30,
					title="Distribution des prix",
					labels={"valeur_fonciere": "Prix (€)"},
				)
                fig.update_traces(marker_color=SECONDARY_COLOR)
                styliser_fig(fig)
                st.plotly_chart(fig, use_container_width=True)

            if "type_local" in df_resultats.columns:
                agg_type = df_resultats.groupby("type_local").agg({
					"prix_m2": "median",
					"valeur_fonciere": "count"
				}).reset_index()
                agg_type.columns = ["type_local", "prix_m2_median", "count"]

                fig = px.bar(
					agg_type,
					x="type_local",
					y="prix_m2_median",
					color="count",
					title="Prix médian/m² par type de bien",
					labels={"type_local": "Type", "prix_m2_median": "Prix/m² médian", "count": "Nombre"},
					text="count",
					color_continuous_scale="Turbo",
				)
                fig.update_traces(textposition="outside", marker_line_width=0)
                styliser_fig(fig)
                st.plotly_chart(fig, use_container_width=True)

        with tab3:
            # Extraire lat/lon depuis le champ coordonnees (geo_point Elasticsearch)
            if "coordonnees" in df_resultats.columns:
                df_resultats["latitude"] = df_resultats["coordonnees"].apply(
                    lambda x: x.get("lat") if isinstance(x, dict) else None
                )
                df_resultats["longitude"] = df_resultats["coordonnees"].apply(
                    lambda x: x.get("lon") if isinstance(x, dict) else None
                )

            if "latitude" in df_resultats.columns and "longitude" in df_resultats.columns:
                df_geo = df_resultats.dropna(subset=["latitude", "longitude"])
            else:
                df_geo = pd.DataFrame()

            if df_geo.empty:
                st.warning("Aucune coordonnée GPS disponible pour ces résultats")
            else:
                fig = px.scatter_mapbox(
					df_geo,
					lat="latitude",
					lon="longitude",
					color="prix_m2",
					size="surface_reelle_bati",
					hover_name="type_local",
					hover_data={
						"valeur_fonciere": ":,.0f",
						"prix_m2": ":,.0f",
						"surface_reelle_bati": ":.0f",
						"arrondissement": True,
						"date_mutation": True,
						"latitude": False,
						"longitude": False,
					},
					color_continuous_scale="Viridis",
					zoom=11.5,
					title="Localisation des résultats",
					height=600,
				)
                fig.update_layout(mapbox_style="carto-positron")
                fig.update_traces(marker={"opacity": 0.8})
                styliser_fig(fig)
                st.plotly_chart(fig, use_container_width=True)

                st.markdown("### Statistiques géographiques")
                col_s1, col_s2, col_s3 = st.columns(3)
                with col_s1:
                    arr_counts = df_geo["arrondissement"].value_counts().head(3)
                    st.markdown("**Top 3 arrondissements:**")
                    for arr, count in arr_counts.items():
                        st.write(f"  • {arr}ème: {count} transactions")

                with col_s2:
                    prix_moyen_geo = (
						df_geo.groupby("arrondissement")["prix_m2"]
						.median()
						.sort_values(ascending=False)
						.head(3)
					)
                    st.markdown("**Prix/m² les plus élevés:**")
                    for arr, prix in prix_moyen_geo.items():
                        st.write(f"  • {arr}ème: {prix:,.0f}€/m²")

                with col_s3:
                    surface_arr = (
						df_geo.groupby("arrondissement")["surface_reelle_bati"]
						.mean()
						.sort_values(ascending=False)
						.head(3)
					)
                    st.markdown("**Surfaces moyennes:**")
                    for arr, surf in surface_arr.items():
                        st.write(f"  • {arr}ème: {surf:.0f}m²")

    if not query:
        st.markdown("---")
        st.markdown("### Exemples de recherches")

        col_ex1, col_ex2, col_ex3 = st.columns(3)

        with col_ex1:
            st.markdown(
				"""
				<div style='background: #3d2817; padding: 1rem; border-radius: 8px; border: 1px solid #d4a574;'>
					<div style='font-weight: 600; color: #d4a574; margin-bottom: 0.5rem;'>Par type</div>
					<div style='color: #d6c6a8; font-size: 0.9rem;'>
						• appartement<br>
						• maison<br>
						• local commercial
					</div>
				</div>
				""",
				unsafe_allow_html=True,
			)

        with col_ex2:
            st.markdown(
				"""
				<div style='background: #3d2817; padding: 1rem; border-radius: 8px; border: 1px solid #c8956a;'>
					<div style='font-weight: 600; color: #c8956a; margin-bottom: 0.5rem;'>Par localisation</div>
					<div style='color: #d6c6a8; font-size: 0.9rem;'>
						• 16eme<br>
						• 8eme arrondissement<br>
						• 1er
					</div>
				</div>
				""",
				unsafe_allow_html=True,
			)

        with col_ex3:
            st.markdown(
				"""
				<div style='background: #3d2817; padding: 1rem; border-radius: 8px; border: 1px solid #b8860b;'>
					<div style='font-weight: 600; color: #b8860b; margin-bottom: 0.5rem;'>Combinaisons</div>
					<div style='color: #d6c6a8; font-size: 0.9rem;'>
						• appartement 16eme<br>
						• maison 5 pieces<br>
						• vente 2024
					</div>
				</div>
				""",
				unsafe_allow_html=True,
			)
