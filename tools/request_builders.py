"""
Construction des requêtes pour l'API Légifrance
Helpers pour générer les corps de requête correctement formatés
"""

from typing import Any, Dict

# Mapping des noms de codes vers leurs IDs Légifrance
CODE_IDS = {
    "civil": "LEGITEXT000006070721",
    "penal": "LEGITEXT000006070719",
    "travail": "LEGITEXT000006072050",
    "commerce": "LEGITEXT000005634379",
    "consommation": "LEGITEXT000006069565",
}


def build_search_request(query: str, page_size: int = 10) -> Dict[str, Any]:
    """
    Construit une requête de recherche correcte avec tous les champs obligatoires
    
    L'API Légifrance requiert une structure spécifique avec plusieurs champs obligatoires.
    Cette fonction garantit que la requête est bien formée.
    
    Args:
        query: Mots-clés de recherche
        page_size: Nombre de résultats par page
        
    Returns:
        Dictionnaire de requête prêt pour l'API
        
    Champs obligatoires selon l'API :
        - fond : Le fonds de recherche
        - recherche.champs : Les critères de recherche
        - recherche.operateur : Opérateur entre les champs (ET/OU)
        - recherche.pageSize : Taille de la page
        - recherche.pageNumber : Numéro de la page
        - recherche.sort : Tri des résultats
        - recherche.typePagination : Type de pagination
        
    Example:
        >>> request = build_search_request("responsabilité civile", 10)
        >>> results = api.search(request)
    """
    return {
        "fond": "ALL",  # Rechercher dans tous les fonds
        "recherche": {
            "champs": [
                {
                    "typeChamp": "ALL",
                    "criteres": [
                        {
                            "typeRecherche": "UN_DES_MOTS",
                            "valeur": query,
                            "operateur": "ET"  # ⭐ IMPORTANT: operateur dans le critère
                        }
                    ],
                    "operateur": "ET"  # ET entre les critères du champ
                }
            ],
            "operateur": "ET",  # OBLIGATOIRE - ET entre les champs
            "pageSize": page_size,
            "pageNumber": 1,
            "sort": "PERTINENCE",  # OBLIGATOIRE - Tri par pertinence
            "typePagination": "DEFAUT"  # OBLIGATOIRE
        }
    }


def get_common_search_examples() -> Dict[str, Dict[str, Any]]:
    """
    Retourne des exemples de requêtes de recherche courantes
    Utile pour la documentation et les tests
    
    Returns:
        Dictionnaire d'exemples avec leurs paramètres
        
    Exemples:
        - recherche_simple: Recherche par mots-clés
        - recherche_code: Recherche dans un code spécifique
        - recherche_date: Recherche avec filtre de date
    """
    return {
        "recherche_simple": {
            "description": "Recherche simple par mots-clés",
            "body": {
                "recherche": {
                    "champs": [
                        {
                            "typeChamp": "ALL",
                            "criteres": [
                                {
                                    "typeRecherche": "CONTIENT",
                                    "valeur": "responsabilité civile",
                                }
                            ],
                        }
                    ],
                    "pageSize": 10,
                    "pageNumber": 1,
                }
            },
        },
        "recherche_code": {
            "description": "Recherche dans un code spécifique",
            "body": {
                "recherche": {
                    "champs": [
                        {
                            "typeChamp": "ALL",
                            "criteres": [
                                {
                                    "typeRecherche": "CONTIENT",
                                    "valeur": "vente",
                                }
                            ],
                        }
                    ],
                    "filtres": [
                        {
                            "facette": "CODE",
                            "sousItems": [
                                {
                                    "valeur": "Code civil",
                                }
                            ],
                        }
                    ],
                    "pageSize": 10,
                }
            },
        },
        "recherche_date": {
            "description": "Recherche avec filtre de date",
            "body": {
                "recherche": {
                    "champs": [
                        {
                            "typeChamp": "ALL",
                            "criteres": [
                                {
                                    "typeRecherche": "CONTIENT",
                                    "valeur": "protection des données",
                                }
                            ],
                        }
                    ],
                    "filtres": [
                        {
                            "facette": "DATE_VERSION",
                            "sousItems": [
                                {
                                    "valeur": "2023-01-01",
                                }
                            ],
                        }
                    ],
                    "pageSize": 10,
                }
            },
        },
    }
