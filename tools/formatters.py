"""
Formatage des résultats pour l'affichage
Convertit les données brutes de l'API en texte lisible
"""

import re
from typing import Any, Dict


def format_search_results(results: Dict[str, Any]) -> str:
    """
    Formate les résultats de recherche pour l'affichage simple
    
    Args:
        results: Résultats bruts de l'API
        
    Returns:
        Texte formaté pour l'utilisateur (sans liens)
        
    Example:
        >>> results = api.search(request)
        >>> print(format_search_results(results))
        **10 résultat(s) trouvé(s)**
        
        1. **Code civil**
           - ID: `LEGITEXT000006070721`
           - Nature: CODE
    """
    if not results.get("results"):
        return "Aucun résultat trouvé."

    output = []
    total = results.get("totalResultNumber", 0)
    output.append(f"**{total} résultat(s) trouvé(s)**\n")

    for i, result in enumerate(results["results"], 1):
        title = result.get("title", "Sans titre")
        text_id = result.get("textId", "N/A")
        nature = result.get("nature", "")

        output.append(f"{i}. **{title}**")
        output.append(f"   - ID: `{text_id}`")
        if nature:
            output.append(f"   - Nature: {nature}")
        output.append("")

    return "\n".join(output)


def format_result_with_link(result: Dict[str, Any], index: int) -> str:
    """
    Formate un résultat avec son lien cliquable
    
    Args:
        result: Un résultat de recherche
        index: Numéro du résultat
        
    Returns:
        Texte formaté en Markdown avec lien
        
    Example:
        >>> result = enriched_results["results"][0]
        >>> print(format_result_with_link(result, 1))
        **1. Code civil**
           - ID: `LEGITEXT000006070721`
           - Nature: CODE
           - Source: CODE
           - 🔗 [Consulter sur Légifrance](https://...)
    """
    # Extraire le titre
    title = "Sans titre"
    if result.get("titles") and len(result["titles"]) > 0:
        title = result["titles"][0].get("title", "Sans titre")
        # Nettoyer les balises HTML de highlight
        title = re.sub(r'</?mark>', '', title)

    # Extraire l'ID
    text_id = "N/A"
    if result.get("titles") and len(result["titles"]) > 0:
        text_id = result["titles"][0].get("id") or result["titles"][0].get("cid") or "N/A"

    # Nature et origine
    nature = result.get("nature", "")
    origin = result.get("origin", "")

    # URL Légifrance
    url = result.get("legifrance_url")

    # Formater
    output = f"**{index}. {title}**\n"
    output += f"   - ID: `{text_id}`\n"

    if nature:
        output += f"   - Nature: {nature}\n"
    if origin:
        output += f"   - Source: {origin}\n"

    if url:
        output += f"   - 🔗 [Consulter sur Légifrance]({url})\n"

    return output


def format_code_info(code_data: Dict[str, Any], code_name: str, url: str) -> str:
    """
    Formate les informations d'un code juridique
    
    Args:
        code_data: Données du code
        code_name: Nom du code
        url: URL Légifrance
        
    Returns:
        Texte formaté
    """
    title = code_data.get("title", f"Code {code_name}")
    
    output = f"**{title}**\n\n"
    output += f"🔗 [Consulter sur Légifrance]({url})\n\n"
    
    # Informations supplémentaires si disponibles
    if code_data.get("sections"):
        nb_sections = len(code_data["sections"])
        output += f"📚 {nb_sections} section(s) principale(s)\n"
    
    return output


def format_article_info(article_data: Dict[str, Any], article_id: str, url: str) -> str:
    """
    Formate les informations d'un article
    
    Args:
        article_data: Données de l'article
        article_id: ID de l'article
        url: URL Légifrance
        
    Returns:
        Texte formaté
    """
    num = article_data.get("num", "")
    title = f"Article {num}" if num else f"Article {article_id}"
    
    output = f"**{title}**\n\n"
    
    # Contenu de l'article
    if article_data.get("text"):
        output += f"{article_data['text']}\n\n"
    
    output += f"🔗 [Consulter sur Légifrance]({url})\n"
    
    return output
