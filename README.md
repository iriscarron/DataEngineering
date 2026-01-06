# DVF Paris - Analyse des transactions immobilieres

Projet de Data Engineering - Scraping et visualisation des donnees DVF (Demandes de Valeurs Foncieres) pour Paris.

## Description

Cette application scrape les donnees de transactions immobilieres depuis l'API DVF+ du Cerema pour les 20 arrondissements de Paris, les stocke dans une base PostgreSQL et les affiche via un dashboard Streamlit interactif.

## Fonctionnalites

- Scraping en temps reel depuis l'API DVF+ au lancement
- Stockage des donnees dans PostgreSQL avec PostGIS
- Dashboard interactif avec filtres
- Visualisations:
  - Timeline des achats d'appartements
  - Indicateur des grosses ventes (configurable)
  - Prix median par arrondissement
  - Evolution des prix dans le temps
  - Distribution du prix au m2
  - Prix par type de bien
  - Repartition par type de vente

## Architecture

```
projet/
├── main.py                 # Application Streamlit
├── etl/
│   └── scraper.py          # Scraper API DVF+
├── docker/
│   ├── Dockerfile          # Image Docker
│   ├── entrypoint.sh       # Script de demarrage
│   └── init-db.sql         # Schema BDD
├── docker-compose.yml      # Orchestration des services
└── requirements.txt        # Dependances Python
```

## Technologies utilisees

| Composant | Technologie |
|-----------|-------------|
| Backend | Python 3.11 |
| Web App | Streamlit |
| Base de donnees | PostgreSQL 16 + PostGIS |
| Visualisation | Plotly |
| Containerisation | Docker, docker-compose |
| Source de donnees | API DVF+ Cerema |

## Lancement

### Avec Docker (recommande)

```bash
# Construire et lancer les containers
docker-compose up --build

# L'application sera disponible sur http://localhost:8501
```

Le scraping se fait automatiquement au demarrage.

### Sans Docker (developpement local)

1. Installer les dependances:
```bash
pip install -r requirements.txt
```

2. Lancer PostgreSQL localement (avec PostGIS)

3. Executer le scraper:
```bash
python etl/scraper.py
```

4. Lancer l'application:
```bash
streamlit run main.py
```

## Configuration

Variables d'environnement:

| Variable | Description | Defaut |
|----------|-------------|--------|
| DATABASE_URL | URL de connexion PostgreSQL | postgresql://dvf:dvf@localhost:5432/dvf |

## Source des donnees

Les donnees proviennent de l'API DVF+ du Cerema:
- URL: https://apidf-preprod.cerema.fr/dvf_opendata/mutations/
- Documentation: https://datafoncier.cerema.fr

Les donnees DVF sont mises a jour 2 fois par an (avril et octobre).

## Auteurs

Projet realise dans le cadre de l'unite Data Engineering E4.
