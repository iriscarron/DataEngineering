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
├── main.py                      # Point d'entree de l'application
├── docker-compose.yml           # Orchestration Docker (PostgreSQL + Elasticsearch)
├── requirements.txt             # Dependances Python (streamlit, pandas, sqlalchemy, elasticsearch, etc.)
├── README.md                    # Documentation
│
├── dash/                        # Application Streamlit multi-pages
│   ├── router.py                # Routeur principal (navigation, selection pages)
│   ├── layout.py                # Configuration theme et utilities
│   ├── navbar.py                # Barre de navigation
│   ├── splash.py                # Page d'accueil (landing page avec 6 bulles)
│   ├── home.py                  # Page Accueil (grid 2x2 d'info)
│   ├── recherche.py             # Page Recherche (Elasticsearch full-text search)
│   ├── carte.py                 # Page Carte (choropleth + markers)
│   ├── prix.py                  # Page Prix (statistiques et graphiques)
│   ├── lexique.py               # Page A propos / Lexique
│   ├── simplepage.py            # Composants reutilisables
│   └── setup.py                 # Configuration Streamlit
│
├── etl/                         # Pipeline ETL
│   ├── scraper.py               # Pipeline complet (API → PostgreSQL → Elasticsearch)
│   ├── elasticsearch_utils.py   # Module Elasticsearch (indexation, recherche)
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

**Note** : Depuis le code Python (scraper sur Windows), utiliser `http://localhost:9200` ou `http://127.0.0.1:9200`.

### Configuration Streamlit

Definie dans `dash/setup.py` :
- Page config en mode "wide" (layout)
- Titre : "DVF Paris - Dashboard Immobilier"
- Theme couleurs : Beige/Marron (#f5f1e8, #3d2817, #8B7355)
- Navigation multi-pages avec splash screen

## Pages du Dashboard

### 1. **Splash Screen** (Page d'accueil)
- Page de bienvenue avec 6 bulles de navigation
- Navigation directe vers chaque section
- Design beige/marron elegant

### 2. **Accueil** (Home)
- Grid 2x2 de cartes d'information
- Types d'habitation Paris
- Types de vente
- Indicateurs cles
- Source des donnees

### 3. **Recherche** (Recherche)
- Moteur de recherche Elasticsearch avec autocomplete
- Recherche textuelle ("appartement 16eme", "maison 5 pieces")
- Filtres multiples :
  - Arrondissement
  - Type de bien
  - Plage de prix
- Affichage des resultats avec details complets

### 4. **Carte** (Carte)
- **Carte choroplethe** : Prix median au m2 par arrondissement (coloree)
- **Carte des transactions** : Points individuels avec details au survol
- Filtres par arrondissement et type

### 5. **Prix** (Prix)
- Statistiques et analyses de prix
- Graphiques analytiques :
  - Timeline des transactions par mois
  - Prix median par arrondissement
  - Evolution des prix dans le temps
  - Distribution du prix au m2 (boxplot)
  - Prix par type de bien
- Filtres par periode et arrondissements

### 6. **À propos** (À propos)
- Lexique des termes DVF
- Definitions des concepts immobiliers
- Information sur les sources

### Indicateurs cles (KPIs)
- Nombre total de transactions
- Prix moyen des transactions
- Prix median au m2
- Surface moyenne

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

# Exemple : Compter les transactions
SELECT COUNT(*) FROM transactions;

# Voir la structure
\dt
\d transactions
```

## Troubleshooting

### Elasticsearch n'est pas disponible

**Symptôme** : Message "Elasticsearch non disponible ou l'index est vide" sur la page Recherche

**Solution** :
1. Verifier que Docker tourne : `docker ps`
2. Relancer Docker Compose si needed : `docker-compose down && docker-compose up -d`
3. Attendre 30-60 secondes le temps qu'Elasticsearch démarre
4. Lancer le scraper : `python etl/scraper.py`
5. Verifier la connexion : voir section "Verifier Elasticsearch" ci-dessus

### Scraper se connecte mais n'indexe pas

**Solution** :
- Verifier que le container Elasticsearch est "healthy" : `docker-compose ps`
- Les logsdu container : `docker-compose logs elasticsearch`

### La page Recherche reste vide apres le scraper

- Attendre que le scraper finisse complètement (voir "Scraping termine!" dans les logs)
- Rafraichir la page Streamlit (F5)

## Notes de Conception

### Palette de couleurs
- Primaire : Beige #f5f1e8, #f3e7d6
- Secondaire : Marron #3d2817, #5b3a22, #8B7355
- Accent : Or/Bronze #c8ac88
- Gradient cartes : De #f3e7d6 (clair) à #dfc8a8 (moyen)

### Donnees actuelles
- **Periode** : 2020-2024
- **Zone** : Paris (20 arrondissements)
- **Nb transactions** : ~204,000
- **Source** : API DVF+ Cerema
- **Maj** : 2 fois par an (avril / octobre)

## Auteurs

Projet realise dans le cadre de l'unite Data Engineering.

**Contributeurs** : Iris Carron, Cléo Detrez

**Periode de realisation** : 2025-2026

## Licence

Donnees DVF : Licence Ouverte / Open Licence (Etalab)

- Documentation DVF : https://datafoncier.cerema.fr
- API DVF+ : https://apidf-preprod.cerema.fr/dvf_opendata/mutations/
