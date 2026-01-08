"""
Module Elasticsearch pour l'indexation et la recherche des transactions DVF
"""
import os
import time
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk


ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
INDEX_NAME = "dvf_transactions"


def get_es_client():
    """
    Cree et retourne un client Elasticsearch
    """
    return Elasticsearch([ELASTICSEARCH_URL])


def attendre_elasticsearch(max_tentatives=30, delai=2):
    """
    Attend que Elasticsearch soit disponible
    """
    es = get_es_client()
    for i in range(max_tentatives):
        try:
            if es.ping():
                print("Elasticsearch est disponible")
                return True
        except Exception:
            pass
        print(f"Attente Elasticsearch... ({i+1}/{max_tentatives})")
        time.sleep(delai)
    return False


def creer_index():
    """
    Cree l'index Elasticsearch avec le mapping approprie
    """
    es = get_es_client()

    mapping = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "analyzer": {
                    "francais": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": ["lowercase", "asciifolding"]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "id_mutation": {"type": "keyword"},
                "date_mutation": {"type": "date"},
                "valeur_fonciere": {"type": "float"},
                "surface_reelle_bati": {"type": "float"},
                "prix_m2": {"type": "float"},
                "nb_pieces": {"type": "integer"},
                "type_local": {
                    "type": "text",
                    "analyzer": "francais",
                    "fields": {"keyword": {"type": "keyword"}}
                },
                "nature_mutation": {
                    "type": "text",
                    "analyzer": "francais",
                    "fields": {"keyword": {"type": "keyword"}}
                },
                "code_postal": {"type": "keyword"},
                "arrondissement": {"type": "keyword"},
                "coordonnees": {"type": "geo_point"},
                "recherche_complete": {
                    "type": "text",
                    "analyzer": "francais"
                }
            }
        }
    }

    if es.indices.exists(index=INDEX_NAME):
        es.indices.delete(index=INDEX_NAME)
        print(f"Index {INDEX_NAME} supprime")

    es.indices.create(index=INDEX_NAME, body=mapping)
    print(f"Index {INDEX_NAME} cree")


def indexer_transactions(df):
    """
    Indexe les transactions dans Elasticsearch
    """
    if df.empty:
        print("Pas de donnees a indexer")
        return 0

    es = get_es_client()

    def generer_documents():
        for _, row in df.iterrows():
            doc = {
                "_index": INDEX_NAME,
                "_source": {
                    "id_mutation": str(row.get("id_mutation", "")),
                    "date_mutation": row["date_mutation"].isoformat() if hasattr(row["date_mutation"], "isoformat") else str(row["date_mutation"]),
                    "valeur_fonciere": float(row["valeur_fonciere"]) if row.get("valeur_fonciere") else None,
                    "surface_reelle_bati": float(row["surface_reelle_bati"]) if row.get("surface_reelle_bati") else None,
                    "prix_m2": float(row["prix_m2"]) if row.get("prix_m2") else None,
                    "nb_pieces": int(row["nb_pieces"]) if row.get("nb_pieces") else None,
                    "type_local": str(row.get("type_local", "")),
                    "nature_mutation": str(row.get("nature_mutation", "")),
                    "code_postal": str(row.get("code_postal", "")),
                    "arrondissement": str(row.get("arrondissement", "")),
                    "recherche_complete": f"{row.get('type_local', '')} {row.get('nature_mutation', '')} {row.get('arrondissement', '')}eme arrondissement Paris {row.get('code_postal', '')}"
                }
            }

            # Ajouter les coordonnees si disponibles
            if row.get("latitude") and row.get("longitude"):
                doc["_source"]["coordonnees"] = {
                    "lat": float(row["latitude"]),
                    "lon": float(row["longitude"])
                }

            yield doc

    succes, erreurs = bulk(es, generer_documents(), raise_on_error=False)
    print(f"Indexation terminee: {succes} documents indexes, {len(erreurs) if erreurs else 0} erreurs")
    return succes


def rechercher_transactions(query, filtres=None, taille=100):
    """
    Recherche des transactions dans Elasticsearch

    Arguments:
        query: Texte de recherche (ex: "appartement 16eme")
        filtres: Dictionnaire de filtres optionnels
        taille: Nombre max de resultats

    Retourne:
        Liste des transactions correspondantes
    """
    es = get_es_client()

    # Construction de la requete
    must_clauses = []
    filter_clauses = []

    # Recherche textuelle
    if query and query.strip():
        must_clauses.append({
            "multi_match": {
                "query": query,
                "fields": ["recherche_complete^3", "type_local^2", "nature_mutation", "arrondissement"],
                "fuzziness": "AUTO"
            }
        })

    # Filtres optionnels
    if filtres:
        if filtres.get("arrondissement"):
            filter_clauses.append({"term": {"arrondissement": filtres["arrondissement"]}})

        if filtres.get("type_local"):
            filter_clauses.append({"term": {"type_local.keyword": filtres["type_local"]}})

        if filtres.get("prix_min") is not None or filtres.get("prix_max") is not None:
            range_query = {"range": {"valeur_fonciere": {}}}
            if filtres.get("prix_min") is not None:
                range_query["range"]["valeur_fonciere"]["gte"] = filtres["prix_min"]
            if filtres.get("prix_max") is not None:
                range_query["range"]["valeur_fonciere"]["lte"] = filtres["prix_max"]
            filter_clauses.append(range_query)

        if filtres.get("surface_min") is not None or filtres.get("surface_max") is not None:
            range_query = {"range": {"surface_reelle_bati": {}}}
            if filtres.get("surface_min") is not None:
                range_query["range"]["surface_reelle_bati"]["gte"] = filtres["surface_min"]
            if filtres.get("surface_max") is not None:
                range_query["range"]["surface_reelle_bati"]["lte"] = filtres["surface_max"]
            filter_clauses.append(range_query)

        if filtres.get("date_min") or filtres.get("date_max"):
            range_query = {"range": {"date_mutation": {}}}
            if filtres.get("date_min"):
                range_query["range"]["date_mutation"]["gte"] = filtres["date_min"]
            if filtres.get("date_max"):
                range_query["range"]["date_mutation"]["lte"] = filtres["date_max"]
            filter_clauses.append(range_query)

    # Requete finale
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
        print(f"Erreur recherche Elasticsearch: {e}")
        return []


def compter_documents():
    """
    Retourne le nombre de documents dans l'index
    """
    es = get_es_client()
    try:
        if not es.indices.exists(index=INDEX_NAME):
            return 0
        response = es.count(index=INDEX_NAME)
        return response["count"]
    except Exception:
        return 0


def elasticsearch_disponible():
    """
    Verifie si Elasticsearch est disponible et contient des donnees
    """
    try:
        es = get_es_client()
        return es.ping() and compter_documents() > 0
    except Exception:
        return False
