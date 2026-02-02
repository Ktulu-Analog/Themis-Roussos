###############################################################################
# Définitions des outils disponibles pour le LLM
# Spécifie l'interface et les paramètres de chaque outil
#
# version : 1.1
# date :    30/01/2026
#
###############################################################################

from typing import Any, Dict, List


def get_tools_definition() -> List[Dict[str, Any]]:
    """
    Retourne la définition des outils disponibles pour le LLM

    Version améliorée avec outil pour récupérer les décrets complets.

    Returns:
        Liste des définitions d'outils au format OpenAI Function Calling

    Outils disponibles:
        - rechercher_textes_juridiques: Recherche full-text dans Légifrance
        - consulter_code: Consultation d'un code juridique complet
        - obtenir_article: Récupération d'un article spécifique
        - obtenir_decret_complet: Récupération d'un décret avec TOUS ses articles
        - lister_codes: Liste tous les codes disponibles

    Example:
        >>> tools = get_tools_definition()
        >>> print(len(tools))
        5
        >>> print(tools[3]["function"]["name"])
        obtenir_decret_complet
    """

    return [
        {
            "type": "function",
            "function": {
                "name": "rechercher_textes_juridiques",
                "description": (
                    "Recherche de textes juridiques dans Légifrance. "
                    "Utilise l'API officielle pour trouver des codes, lois, décrets, etc."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Mots-clés de recherche (ex: 'responsabilité civile', 'code du travail')",
                        },
                        "page_size": {
                            "type": "integer",
                            "default": 10,
                            "description": "Nombre de résultats à retourner (défaut: 10)",
                        },
                    },
                    "required": ["query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "consulter_code",
                "description": (
                    "Consulte un code juridique complet (Code civil, pénal, travail, etc.)"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code_name": {
                            "type": "string",
                            "enum": ["civil", "penal", "travail", "commerce", "consommation"],
                            "description": "Nom du code à consulter",
                        },
                    },
                    "required": ["code_name"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "obtenir_article",
                "description": (
                    "Récupère le contenu d'un article spécifique par son ID"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "article_id": {
                            "type": "string",
                            "description": "ID de l'article (ex: LEGIARTI000006419283)",
                        },
                    },
                    "required": ["article_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "obtenir_decret_complet",
                "description": (
                    "Récupère un décret ou une loi avec TOUS ses articles. "
                    "Utiliser cet outil pour les JORFTEXT, LODA, et tous les textes "
                    "qui peuvent avoir une structure tronquée dans la réponse API. "
                    "Cet outil résout le problème où seuls les derniers articles "
                    "sont retournés par l'API."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text_id": {
                            "type": "string",
                            "description": (
                                "ID du texte juridique (ex: JORFTEXT000051774034 pour un décret). "
                                "Accepte les IDs JORFTEXT, LEGITEXT pour les LODA."
                            ),
                        },
                        "fetch_all_articles": {
                            "type": "boolean",
                            "default": False,
                            "description": (
                                "Si True, force la récupération individuelle de chaque article "
                                "même si la structure semble complète. Utile pour les très longs textes."
                            ),
                        },
                    },
                    "required": ["text_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "lister_codes",
                "description": "Liste tous les codes juridiques disponibles",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "page_size": {
                            "type": "integer",
                            "default": 20,
                            "description": "Nombre de codes à retourner",
                        },
                    },
                },
            },
        },
    ]


# Alias pour compatibilité avec l'ancien code
TOOLS = get_tools_definition()
