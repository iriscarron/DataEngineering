# PROJET DATA – DVF Paris (Streamlit)

## Objectif
Application web Streamlit qui affiche et explore les données de transactions immobilières parisiennes (DVF). Données chargées en base (Postgres/PostGIS conseillé) et visualisées avec filtres, cartes et graphiques.

## Stack cible
- Ingestion : Python (requests/BeautifulSoup ou téléchargement CSV/GeoJSON DVF)
- BDD : Postgres (option PostGIS pour géo)
- API/Front : Streamlit + services Python d’agrégation
- Conteneurs : docker-compose (services app, db, admin facultatif)

## Données attendues
- Source DVF (Paris). Tu peux prendre le fichier DVF national et filtrer sur code INSEE 75056 ou les codes postaux 75001-75020.
- GeoJSON arrondissements : à placer dans `data/geo/` (à récupérer à part si non fourni par la source DVF).
- Colonnes clés : date_mutation, valeur_fonciere, surface_reelle_bati, prix_m2 (calculé), type_local, code_postal, arrondissement, lat/lon.

## Arborescence
- `app/` : code Streamlit, services de stats
- `etl/` : scripts de scraping/téléchargement + nettoyage + chargement BDD
- `data/` : fichiers bruts/intermédiaires (ignorer en git sauf échantillons)
- `docker/` : Dockerfile, init-db.sql, configs
- `main.py` : point d’entrée rapide (peut lancer l’ETL ou l’app)

## Fonctions attendues (côté app)
- Filtres : dates, arrondissement, type_local
- Graphes :
  - Timeline des achats (histogramme ou courbe par mois/année)
  - Indicateur grosses ventes (seuil quantile, sur série ou carte)
  - Prix par arrondissement (bar/choroplèthe)
  - Prix par date (médiane/moyenne)
  - Prix au m² (distribution + évolution)
  - Prix par type_local (locaux/commerce/particuliers)
- Carte : points ou choroplèthe arrondissements
- Bonus : recherche (titre/adresse) si on ajoute un index texte

## Étapes de mise en place
1) Récupérer les données
- Télécharger DVF (CSV ou GeoJSON). Filtrer Paris.
- Placer le GeoJSON arrondissements dans `data/geo/`.

2) Préparer l’ETL
- Script `etl/download.py` : fetch DVF + sauvegarde dans `data/raw/`.
- Script `etl/clean_load.py` : nettoyage, calcul prix_m2, insertion Postgres (COPY pour la vitesse). Index sur date_mutation, code_postal, type_local. PostGIS : colonne geometry et index GIST.

3) Configurer la BDD
- Créer Postgres via docker-compose (voir à rédiger) avec variables env : POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD.
- Option : `docker/init-db.sql` pour créer schéma + extensions PostGIS.

4) Lancer l’app
- Mode local simple : `streamlit run main.py`
- Mode docker (après rédaction des fichiers) : `docker-compose up --build`

## Variables d’environnement (à prévoir)
- `DATABASE_URL` ou `POSTGRES_*`
- `APP_PORT` (facultatif)

## Prochaines tâches
- Ajouter docker-compose.yml + Dockerfile (app + db)
- Écrire `etl/download.py` et `etl/clean_load.py`
- Écrire `app` Streamlit (layout + graphes listés)
- Tester avec un échantillon DVF Paris
- Compléter la doc (commandes exactes, captures d’écran)

## Notes
- Pour les grosses ventes : seuil p95 de `valeur_fonciere` ou `prix_m2` par arrondissement.
- Garder un échantillon léger dans le repo, ignorer le bulk avec .gitignore.
