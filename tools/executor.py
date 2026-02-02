###############################################################################
# Exécution des appels d'outils
# Gère l'exécution synchrone des outils définis pour le LLM
#
# version : 1.1
# date :    30/01/2026
# modif :   Ajout de _execute_get_decree_complete pour gérer les décrets
#           dont l'API ne retourne que les derniers articles
#
###############################################################################


import logging
import traceback
from typing import Any, Dict, List

from legifrance_api import LegifranceAPIError

from .api_instance import get_api
from .request_builders import build_search_request, CODE_IDS
from .url_builder import generate_legifrance_url, enrich_search_results_with_links
from .formatters import format_result_with_link

logger = logging.getLogger(__name__)

def execute_tool(
    tool_name: str,
    arguments: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Exécute un appel d'outil de manière synchrone

    Dispatcher principal pour l'exécution des outils Légifrance.
    Route les appels vers les fonctions d'exécution appropriées.

    Args:
        tool_name: Nom de l'outil à exécuter
        arguments: Arguments de l'outil

    Returns:
        Résultat de l'exécution de l'outil avec structure:
        {
            "success": bool,
            "data": Any,  # Données brutes de l'API
            "error": str,  # Si success=False
            ...  # Métadonnées spécifiques à l'outil
        }

    Raises:
        LegifranceAPIError: Si l'API Légifrance retourne une erreur
        Exception: Pour toute autre erreur inattendue

    Example:
        >>> result = execute_tool(
        ...     "rechercher_textes_juridiques",
        ...     {"query": "code civil", "page_size": 10}
        ... )
        >>> print(result["success"])
        True
    """

    api = get_api()

    try:
        if tool_name == "rechercher_textes_juridiques":
            return _execute_search(api, arguments)

        elif tool_name == "consulter_code":
            return _execute_get_code(api, arguments)

        elif tool_name == "obtenir_article":
            return _execute_get_article(api, arguments)

        elif tool_name == "obtenir_decret_complet":
            return _execute_get_decree_complete(api, arguments)

        elif tool_name == "lister_codes":
            return _execute_list_codes(api, arguments)

        else:
            return {
                "success": False,
                "error": f"Outil inconnu: {tool_name}",
            }

    except LegifranceAPIError as e:
        logger.error(f"Erreur API Légifrance dans {tool_name}: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_type": "LegifranceAPIError",
            "tool": tool_name,
            "arguments": arguments,
        }

    except Exception as e:
        logger.error(f"Erreur inattendue dans {tool_name}: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc(),
            "tool": tool_name,
            "arguments": arguments,
        }

def _execute_search(api: Any, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recherche de textes avec l'API Légifrance

    Effectue une recherche full-text dans la base Légifrance et enrichit
    les résultats avec des liens directs vers le site officiel.

    Args:
        api: Instance de l'API Légifrance
        arguments: Dictionnaire contenant:
            - query (str): Mots-clés de recherche (requis)
            - page_size (int): Nombre de résultats (défaut: 10)

    Returns:
        Dictionnaire contenant:
            - success (bool): True si succès
            - data (dict): Résultats bruts enrichis avec URLs
            - query (str): Requête effectuée
            - total_results (int): Nombre total de résultats
            - formatted_results (str): Top 5 des résultats formatés

    Example:
        >>> result = _execute_search(api, {"query": "responsabilité civile"})
        >>> print(result["total_results"])
        152
    """
    query = arguments.get("query", "")
    page_size = arguments.get("page_size", 10)

    if not query:
        return {
            "success": False,
            "error": "Le paramètre 'query' est requis",
        }

    # Construire la requête correcte
    search_request = build_search_request(query, page_size)

    # Appeler l'API
    result = api.search(search_request)

    # Enrichir avec les URLs Légifrance
    enriched_result = enrich_search_results_with_links(result)

    # Formater les résultats pour le LLM avec les liens
    formatted_results = []
    if enriched_result.get("results"):
        for i, res in enumerate(enriched_result["results"][:5], 1):  # Top 5
            formatted_results.append(format_result_with_link(res, i))

    return {
        "success": True,
        "data": enriched_result,
        "query": query,
        "total_results": enriched_result.get("totalResultNumber", 0),
        "formatted_results": "\n".join(formatted_results) if formatted_results else "Aucun résultat",
    }

def _execute_get_code(api: Any, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Consulte un code juridique complet

    Récupère la structure et le contenu d'un code juridique
    (Code civil, pénal, travail, etc.).

    Args:
        api: Instance de l'API Légifrance
        arguments: Dictionnaire contenant:
            - code_name (str): Nom du code (civil, penal, travail, commerce, consommation)

    Returns:
        Dictionnaire contenant:
            - success (bool): True si succès
            - data (dict): Données du code
            - code_name (str): Nom du code
            - code_id (str): ID Légifrance du code
            - legifrance_url (str): Lien vers Légifrance
            - info (str): Message formaté avec lien

    Example:
        >>> result = _execute_get_code(api, {"code_name": "civil"})
        >>> print(result["code_id"])
        LEGITEXT000006070721
    """
    code_name = arguments.get("code_name", "")

    if code_name not in CODE_IDS:
        return {
            "success": False,
            "error": f"Le code '{code_name}' inconnu. Voici les codes disponibles: {list(CODE_IDS.keys())}",
        }

    code_id = CODE_IDS[code_name]
    result = api.get_code(code_id)

    # Ajouter l'URL Légifrance
    url = generate_legifrance_url(code_id, "code")

    return {
        "success": True,
        "data": result,
        "code_name": code_name,
        "code_id": code_id,
        "legifrance_url": url,
        "info": f"Code {code_name} - 🔗 [Consulter ce document sur Légifrance]({url})",
    }

def _execute_get_article(api: Any, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Récupère un article spécifique par son identifiant

    Obtient le contenu complet d'un article de code juridique
    avec ses métadonnées.

    Args:
        api: Instance de l'API Légifrance
        arguments: Dictionnaire contenant:
            - article_id (str): ID de l'article (ex: LEGIARTI000006419283)

    Returns:
        Dictionnaire contenant:
            - success (bool): True si succès
            - data (dict): Données de l'article
            - article_id (str): ID de l'article
            - legifrance_url (str): Lien vers Légifrance
            - info (str): Message formaté avec lien

    Example:
        >>> result = _execute_get_article(api, {"article_id": "LEGIARTI000006419283"})
        >>> print(result["success"])
        True
    """
    article_id = arguments.get("article_id", "")

    if not article_id:
        return {
            "success": False,
            "error": "Le paramètre 'article_id' est requis",
        }

    # Utiliser get_article qui prend un ID d'article directement
    result = api.get_article(article_id)

    # Ajouter l'URL Légifrance
    url = generate_legifrance_url(article_id, "article")

    return {
        "success": True,
        "data": result,
        "article_id": article_id,
        "legifrance_url": url,
        "info": f"Article {article_id} - 🔗 [Consulter sur Légifrance]({url})",
    }

def _execute_list_codes(api: Any, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Liste tous les codes disponibles (en vigueur et abrogés)

    Récupère la liste paginée de tous les codes juridiques
    disponibles dans la base Légifrance.

    Args:
        api: Instance de l'API Légifrance
        arguments: Dictionnaire contenant:
            - page_size (int): Nombre de codes à retourner (défaut: 20)

    Returns:
        Dictionnaire contenant:
            - success (bool): True si succès
            - data (dict): Liste des codes
            - total_codes (int): Nombre total de codes disponibles

    Example:
        >>> result = _execute_list_codes(api, {"page_size": 50})
        >>> print(result["total_codes"])
        78
    """
    page_size = arguments.get("page_size", 20)

    result = api.list_codes(page_size=page_size)

    return {
        "success": True,
        "data": result,
        "total_codes": result.get("totalResultNumber", 0),
    }


# ============================================================================
# NOUVELLE FONCTION : Récupération complète des décrets
# ============================================================================

def _extract_all_article_ids(data: Dict[str, Any], ids: List[str] = None) -> List[str]:
    """
    Extrait récursivement tous les IDs d'articles d'une structure

    Args:
        data: Structure JSON retournée par l'API
        ids: Liste accumulatrice

    Returns:
        Liste de tous les IDs d'articles détectés
    """
    if ids is None:
        ids = []

    # Détecter si c'est un article
    if data.get('type') == 'article' or 'ARTI' in data.get('id', ''):
        if data.get('id'):
            ids.append(data['id'])

    if data.get('cid') and 'ARTI' in data.get('cid', ''):
        if data['cid'] not in ids:  # Éviter les doublons
            ids.append(data['cid'])

    # Parcourir les sous-structures
    for key in ['sections', 'articles', 'sections_ta', 'articleLiensFondamentaux']:
        if key in data and isinstance(data[key], list):
            for item in data[key]:
                _extract_all_article_ids(item, ids)

    return ids


def _extract_articles_with_content(data: Dict[str, Any], articles: List[Dict] = None) -> List[Dict]:
    """
    Extrait récursivement tous les articles avec leur contenu

    Args:
        data: Structure JSON de l'API
        articles: Liste accumulatrice

    Returns:
        Liste d'articles avec leur contenu
    """
    if articles is None:
        articles = []

    # Si c'est un article avec du contenu
    if data.get('texte') or data.get('type') == 'article':
        article_info = {
            'id': data.get('id', data.get('cid', 'N/A')),
            'num': data.get('num', 'N/A'),
            'title': data.get('intOrdre', ''),
            'text': data.get('texte', ''),
            'etat': data.get('etat', 'N/A'),
            'cid': data.get('cid', 'N/A')
        }

        # N'ajouter que si on a du texte
        if article_info['text']:
            articles.append(article_info)

    # Parcourir récursivement
    for key in ['sections', 'articles', 'sections_ta']:
        if key in data and isinstance(data[key], list):
            for item in data[key]:
                _extract_articles_with_content(item, articles)

    return articles


def _execute_get_decree_complete(api: Any, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Récupère un décret avec TOUS ses articles

    Cette fonction résout le problème où l'API PISTE ne retourne
    que les 2 derniers articles d'un décret.

    Stratégie:
    1. Récupérer le texte via get_jorf() ou get_law_decree()
    2. Extraire tous les IDs d'articles de la structure
    3. Vérifier si la structure contient le texte de tous les articles
    4. Si manquant, récupérer les articles individuellement

    Args:
        api: Instance LegifranceAPI
        arguments: {
            "text_id": str,  # ID du texte (ex: JORFTEXT000051774034)
            "fetch_all_articles": bool  # Si True, force la récup individuelle
        }

    Returns:
        Dict avec:
        - success: bool
        - decree_metadata: métadonnées du décret
        - all_articles: liste complète des articles
        - total_articles: nombre d'articles
        - method_used: méthode utilisée
        - formatted_summary: résumé formaté pour le LLM
    """
    text_id = arguments.get("text_id", "")
    fetch_all = arguments.get("fetch_all_articles", False)

    if not text_id:
        return {
            "success": False,
            "error": "Le paramètre 'text_id' est requis"
        }

    try:
        # 1. Récupérer le texte (essayer JORF puis LODA si échec)
        logger.info(f"Récupération du texte {text_id}")

        decree = None
        method_type = None

        # Déterminer la méthode selon le préfixe
        if text_id.startswith('JORFTEXT'):
            try:
                decree = api.get_jorf(text_id)
                method_type = "JORF"
            except Exception as e:
                logger.warning(f"Échec get_jorf: {e}, essai avec get_law_decree")
                decree = api.get_law_decree(text_id)
                method_type = "LODA"
        else:
            # Pour LEGITEXT et autres, essayer get_law_decree
            decree = api.get_law_decree(text_id)
            method_type = "LODA"

        # Extraire les métadonnées
        text_info = decree.get('text', {})
        metadata = {
            'id': text_id,
            'title': text_info.get('title', 'N/A'),
            'nature': text_info.get('nature', 'N/A'),
            'date_signature': text_info.get('dateSignature', 'N/A'),
            'date_publi': text_info.get('datePubli', 'N/A'),
            'nor': text_info.get('nor', 'N/A'),
            'num': text_info.get('num', 'N/A'),
            'etat': text_info.get('etat', 'N/A')
        }

        # 2. Extraire les articles de la structure
        articles_from_structure = _extract_articles_with_content(decree)
        article_ids = _extract_all_article_ids(decree)

        logger.info(f"Articles avec contenu dans structure: {len(articles_from_structure)}")
        logger.info(f"IDs d'articles détectés: {len(article_ids)}")

        # 3. Déterminer si on doit récupérer individuellement
        method = "structure"
        all_articles = articles_from_structure

        # Si moins de 50% des articles ont du contenu, récupérer individuellement
        threshold = max(len(article_ids) * 0.5, 2)  # Au moins 2 articles manquants

        if fetch_all or len(articles_from_structure) < threshold:
            logger.warning(
                f"Structure incomplète ({len(articles_from_structure)}/{len(article_ids)} articles). "
                f"Récupération individuelle..."
            )
            method = "individual_fetch"

            fetched_articles = []
            max_articles = min(len(article_ids), 100)  # Limite à 100 pour éviter timeout

            for i, article_id in enumerate(article_ids[:max_articles], 1):
                try:
                    article_data = api.get_article(article_id)

                    article_content = article_data.get('article', {})
                    fetched_articles.append({
                        'id': article_id,
                        'num': article_content.get('num', 'N/A'),
                        'title': article_content.get('intOrdre', ''),
                        'text': article_content.get('texte', ''),
                        'etat': article_content.get('etat', 'N/A'),
                        'cid': article_content.get('cid', article_id),
                        'date_debut': article_content.get('dateDebut', 'N/A'),
                        'date_fin': article_content.get('dateFin', 'N/A')
                    })

                    if i % 10 == 0:
                        logger.info(f"Récupéré {i}/{max_articles} articles")

                except Exception as e:
                    logger.error(f"Erreur article {article_id}: {e}")
                    # Ajouter quand même avec erreur
                    fetched_articles.append({
                        'id': article_id,
                        'num': 'N/A',
                        'text': f"[Erreur de récupération: {str(e)}]",
                        'error': str(e)
                    })

            all_articles = fetched_articles
            logger.info(f"Récupération terminée: {len(fetched_articles)} articles")

        # 4. Générer l'URL Légifrance
        url = generate_legifrance_url(text_id, "jorf" if method_type == "JORF" else "loda")

        # 5. Formater pour le LLM
        formatted_articles = []
        preview_limit = min(len(all_articles), 5)  # Top 5 pour le contexte

        for i, art in enumerate(all_articles[:preview_limit], 1):
            text_preview = art['text'][:300] if art['text'] else "[Pas de contenu]"
            formatted_articles.append(
                f"**Article {art['num']}** {art.get('title', '')}\n"
                f"{text_preview}{'...' if len(art['text']) > 300 else ''}\n"
            )

        # 6. Résumé formaté
        summary = (
            f"📄 **{metadata['title']}**\n\n"
            f"**Métadonnées:**\n"
            f"- Nature: {metadata['nature']}\n"
            f"- NOR: {metadata['nor']}\n"
            f"- Date signature: {metadata['date_signature']}\n"
            f"- Date publication: {metadata['date_publi']}\n"
            f"- État: {metadata['etat']}\n\n"
            f"📊 **{len(all_articles)} article(s) récupéré(s)** "
            f"(méthode: {method}, source: {method_type})\n\n"
            f"🔗 [Consulter sur Légifrance]({url})\n\n"
            f"**Aperçu des premiers articles:**\n\n"
            + "\n".join(formatted_articles)
        )

        if len(all_articles) > preview_limit:
            summary += f"\n\n... et {len(all_articles) - preview_limit} autres articles"

        return {
            "success": True,
            "decree_metadata": metadata,
            "all_articles": all_articles,
            "total_articles": len(all_articles),
            "article_ids_found": len(article_ids),
            "method_used": method,
            "source_type": method_type,
            "legifrance_url": url,
            "formatted_summary": summary,
            "data": decree,  # Données brutes pour référence
            "info": summary  # Alias pour compatibilité
        }

    except LegifranceAPIError as e:
        logger.error(f"Erreur API lors de la récupération du texte: {e}")
        return {
            "success": False,
            "error": f"Erreur API Légifrance: {str(e)}",
            "error_type": "LegifranceAPIError",
            "text_id": text_id
        }

    except Exception as e:
        logger.error(f"Erreur inattendue lors de la récupération du texte: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc(),
            "text_id": text_id
        }
