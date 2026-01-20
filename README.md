# DVF Paris - Analyse des Transactions Immobilieres

Projet de Data Engineering pour le scraping, stockage et visualisation des donnees DVF (Demandes de Valeurs Foncieres) de Paris.

## Presentation du Projet

Cette application permet d'analyser les transactions immobilieres des 20 arrondissements de Paris. Elle collecte les donnees depuis l'API DVF+ du Cerema, les stocke dans une base PostgreSQL, les indexe dans Elasticsearch pour la recherche, et les affiche via un dashboard Streamlit interactif.

### Fonctionnalites principales

- Scraping automatique des donnees DVF au lancement
- Stockage relationnel dans PostgreSQL avec extension PostGIS
- Moteur de recherche avance avec Elasticsearch
- Dashboard interactif avec filtres multiples
- Carte choroplethe par arrondissement
- Carte des transactions individuelles
- 7 types de visualisations analytiques

## Architecture Technique

```
Projet_data_engineering/
│
├── main.py                      # Application Streamlit (dashboard)
├── docker-compose.yml           # Orchestration des 3 services
├── requirements.txt             # Dependances Python
├── .env.example                 # Variables d'environnement
│
├── etl/
│   ├── scraper.py               # Pipeline ETL (Extract-Transform-Load)
│   ├── elasticsearch_utils.py   # Module indexation et recherche ES
│   ├── download.py              # Telechargement CSV (alternatif)
│   └── clean_load.py            # Nettoyage CSV (alternatif)
│
├── docker/
│   ├── Dockerfile               # Image de l'application
│   ├── entrypoint.sh            # Script de demarrage
│   └── init-db.sql              # Schema de la base de donnees
│
└── data/                        # Donnees brutes (si telechargement CSV)
```

## Stack Technique

| Composant | Technologie | Version |
|-----------|-------------|---------|
| Langage | Python | 3.11 |
| Application Web | Streamlit | >= 1.30 |
| Base de donnees | PostgreSQL + PostGIS | 16 |
| Moteur de recherche | Elasticsearch | 8.11 |
| Visualisation | Plotly | >= 5.18 |
| Containerisation | Docker + docker-compose | - |
| Source de donnees | API DVF+ Cerema | - |

## Pre-requis

- Docker et docker-compose installes
- 4 Go de RAM minimum (Elasticsearch necessite de la memoire)
- Connexion internet (pour le scraping et les cartes)

## Installation et Lancement

### Methode recommandee : Docker Compose

```bash
# Cloner le repository
git clone <url-du-repo>
cd Projet_data_engineering

# Lancer tous les services
docker-compose up --build
```

L'application sera accessible sur **http://localhost:8501**

Le premier lancement prend quelques minutes car :
1. Les images Docker sont telechargees
2. Elasticsearch demarre (30-60 secondes)
3. Les donnees sont scrapees depuis l'API (~5-10 minutes selon la periode)
4. Les donnees sont indexees dans Elasticsearch

### Methode alternative : Installation locale

```bash
# Installer les dependances
pip install -r requirements.txt

# Demarrer PostgreSQL et Elasticsearch localement
# (voir docker-compose.yml pour la configuration)

# Lancer le scraper
python etl/scraper.py

# Lancer l'application
streamlit run main.py
```

## Services Docker

| Service | Port | Description |
|---------|------|-------------|
| app | 8501 | Dashboard Streamlit |
| db | 5432 | PostgreSQL + PostGIS |
| elasticsearch | 9200 | Moteur de recherche |

## Configuration

Variables d'environnement (definies dans docker-compose.yml) :

| Variable | Description | Valeur par defaut |
|----------|-------------|-------------------|
| DATABASE_URL | Connexion PostgreSQL | postgresql://dvf:dvf@db:5432/dvf |
| ELASTICSEARCH_URL | URL Elasticsearch | http://elasticsearch:9200 |

## Fonctionnalites du Dashboard

### Indicateurs cles (KPIs)
- Nombre total de transactions
- Prix moyen des transactions
- Prix median au m2
- Surface moyenne
- Nombre de grosses ventes (top 5%)

### Moteur de recherche Elasticsearch
- Recherche textuelle ("appartement 16eme", "maison 5 pieces")
- Filtrage par budget
- Resultats tries par date

### Cartes interactives
- **Carte choroplethe** : Prix median au m2 par arrondissement (coloree)
- **Carte des transactions** : Points individuels avec details au survol

### Graphiques analytiques
1. Timeline des transactions par mois
2. Indicateur des grosses ventes (seuil configurable)
3. Prix median par arrondissement
4. Evolution des prix dans le temps
5. Distribution du prix au m2 (boxplot)
6. Prix par type de bien
7. Repartition par type de vente

### Filtres disponibles
- Periode (date debut / fin)
- Arrondissements (selection multiple)
- Type de bien (Appartement, Maison, Local, etc.)
- Type de vente (Vente, VEFA, etc.)
- Plage de prix

## Pipeline ETL

Le pipeline ETL s'execute automatiquement au demarrage :

```
[1/4] Scraping API DVF+ Cerema
      └─> Recuperation des mutations pour les 20 arrondissements
      └─> Pagination automatique (500 resultats/page)
      └─> Gestion des erreurs et retry

[2/4] Transformation des donnees
      └─> Mapping des champs API vers schema BDD
      └─> Calcul du prix au m2
      └─> Generation des coordonnees GPS
      └─> Nettoyage des valeurs manquantes

[3/4] Chargement PostgreSQL
      └─> Insertion par lots de 1000 enregistrements
      └─> Tables indexees pour les requetes

[4/4] Indexation Elasticsearch
      └─> Creation de l'index avec mapping
      └─> Indexation en bulk des transactions
      └─> Champs optimises pour la recherche
```

## Source des Donnees

Les donnees proviennent de l'API DVF+ du Cerema :
- **URL** : https://apidf-preprod.cerema.fr/dvf_opendata/mutations/
- **Documentation** : https://datafoncier.cerema.fr
- **Mise a jour** : 2 fois par an (avril et octobre)
- **Couverture** : Transactions immobilieres en France

## Schema de la Base de Donnees

Table `transactions` :

| Colonne | Type | Description |
|---------|------|-------------|
| id | SERIAL | Identifiant unique |
| id_mutation | VARCHAR | ID mutation DVF |
| date_mutation | DATE | Date de la transaction |
| valeur_fonciere | NUMERIC | Prix de vente |
| surface_reelle_bati | NUMERIC | Surface en m2 |
| prix_m2 | NUMERIC | Prix au m2 calcule |
| nb_pieces | INTEGER | Nombre de pieces |
| type_local | VARCHAR | Type de bien |
| nature_mutation | VARCHAR | Type de vente |
| code_postal | VARCHAR | Code postal |
| arrondissement | VARCHAR | Numero d'arrondissement |
| latitude | NUMERIC | Coordonnee GPS |
| longitude | NUMERIC | Coordonnee GPS |
| scraped_at | TIMESTAMP | Date de scraping |

## Developpement

### Relancer le scraping manuellement

```bash
# Depuis le container
docker-compose exec app python etl/scraper.py

# Ou localement
python etl/scraper.py
```

### Reinitialiser les donnees

```bash
# Supprimer les volumes et relancer
docker-compose down -v
docker-compose up --build
```

### Acceder a PostgreSQL

```bash
docker-compose exec db psql -U dvf -d dvf
```

### Acceder a Elasticsearch

```bash
# Verifier le statut
curl http://localhost:9200/_cluster/health

# Compter les documents
curl http://localhost:9200/dvf_transactions/_count
```

## Auteurs

Projet realise dans le cadre de l'unite Data Engineering, Iris Carron et Cléo Detrez.

## Licence

Donnees DVF : Licence Ouverte / Open Licence (Etalab)
