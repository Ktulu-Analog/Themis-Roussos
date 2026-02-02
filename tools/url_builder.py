###############################################################################
# Construction des URLs Légifrance pour les afficher dans le chat
# Génère les liens directs vers les textes sur le site officiel
#
# version : 0.7.2 un vrai champ de mines
# date :    29/01/2026
###############################################################################

from typing import Any, Dict


def generate_legifrance_url(text_id: str, text_type: str = "auto") -> str:
    """
    Génère l'URL Légifrance pour un texte donné
    
    Args:
        text_id: ID du texte (ex: LEGITEXT000006070721, LEGIARTI000006419283)
        text_type: Type de texte ou "auto" pour détection automatique
    
    Returns:
        URL complète vers Légifrance
    
    Types de textes supportés:
        - code: Codes juridiques (LEGITEXT)
        - article: Articles de code (LEGIARTI)
        - section: Sections de code (LEGISCTA)
        - jorf: Textes du Journal Officiel (JORFTEXT)
        - kali: Conventions collectives (KALITEXT)
        - juri: Jurisprudence (CETATEXT, JURITEXT)
        - cnil: Délibérations CNIL (CNILTEXT)
        - loda: Lois et décrets autonomes
        - acco: Accords d'entreprise
    
    Example:
        >>> url = generate_legifrance_url("LEGITEXT000006070721", "code")
        >>> print(url)
        https://www.legifrance.gouv.fr/codes/id/LEGITEXT000006070721/
    """
    base_url = "https://www.legifrance.gouv.fr"

    # Détection automatique du type selon le préfixe
    if text_type == "auto":
        if text_id.startswith("LEGITEXT"):
            text_type = "code"
        elif text_id.startswith("LEGIARTI"):
            text_type = "article"
        elif text_id.startswith("LEGISCTA"):
            text_type = "section"
        elif text_id.startswith("JORFTEXT") or text_id.startswith("JORFCONT"):
            text_type = "jorf"
        elif text_id.startswith("KALITEXT") or text_id.startswith("KALICONT"):
            text_type = "kali"
        elif text_id.startswith("CETATEXT") or text_id.startswith("JURITEXT"):
            text_type = "juri"
        elif text_id.startswith("CNILTEXT"):
            text_type = "cnil"
        else:
            # Fallback : essayer de deviner par le contenu
            text_type = "code"

    # Construction de l'URL selon le type
    if text_type == "code":
        return f"{base_url}/codes/id/{text_id}/"
    elif text_type == "article":
        return f"{base_url}/codes/article_lc/{text_id}"
    elif text_type == "section":
        return f"{base_url}/codes/section_lc/{text_id}"
    elif text_type == "jorf":
        # Les textes JORF (décrets, lois) utilisent le chemin /loda/id/
        return f"{base_url}/loda/id/{text_id}"
    elif text_type == "kali":
        # Conventions collectives
        return f"{base_url}/conv_coll/id/{text_id}"
    elif text_type == "juri":
        # Jurisprudence
        return f"{base_url}/juri/id/{text_id}"
    elif text_type == "cnil":
        # Délibérations CNIL
        return f"{base_url}/cnil/id/{text_id}"
    elif text_type == "loda":
        # Lois et décrets autonomes
        return f"{base_url}/loda/id/{text_id}"
    elif text_type == "acco":
        # Accords d'entreprise
        return f"{base_url}/acco/id/{text_id}"
    else:
        # URL générique de fallback
        return f"{base_url}/affichTexte.do?cidTexte={text_id}"

def enrich_search_results_with_links(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrichit les résultats de recherche avec des URLs cliquables
    
    Ajoute un champ 'legifrance_url' à chaque résultat contenant
    le lien direct vers le texte sur Légifrance.
    
    Args:
        results: Résultats bruts de l'API
    
    Returns:
        Résultats enrichis avec champ 'legifrance_url'
    
    Example:
        >>> results = {"results": [{"titles": [{"id": "LEGITEXT000006070721"}]}]}
        >>> enriched = enrich_search_results_with_links(results)
        >>> print(enriched["results"][0]["legifrance_url"])
        https://www.legifrance.gouv.fr/codes/id/LEGITEXT000006070721/
    """
    if not results.get("results"):
        return results

    enriched_results = results.copy()

    for result in enriched_results["results"]:
        # Récupérer l'ID du texte
        text_id = None
        text_type = "auto"

        # Essayer différentes sources d'ID
        if result.get("titles"):
            # Prendre le premier titre
            first_title = result["titles"][0]
            text_id = first_title.get("id") or first_title.get("cid")

        # Déterminer le type selon plusieurs critères
        origin = result.get("origin", "").upper()
        result_type = result.get("type", "")
        nature = result.get("nature", "")

        # Détection du type par origine et type de résultat
        if origin == "CETAT" or result_type == "data_juri":
            text_type = "juri"
        elif "JORF" in origin or result_type == "data_jorf":
            text_type = "jorf"
        elif origin == "KALI" or result_type == "data_kali":
            text_type = "kali"
        elif origin == "CNIL" or result_type == "data_cnil":
            text_type = "cnil"
        elif origin == "LODA" or result_type == "data_loda":
            text_type = "loda"
        elif origin == "ACCO" or result_type == "data_acco":
            text_type = "acco"
        elif origin == "CODE" or result_type == "data_code":

            # Déterminer si c'est un code ou un article
            if text_id and text_id.startswith("LEGIARTI"):
                text_type = "article"
            elif text_id and text_id.startswith("LEGISCTA"):
                text_type = "section"
            else:
                text_type = "code"
        else:
            # Laisser la détection automatique par préfixe
            text_type = "auto"

        # Générer l'URL
        if text_id:
            result["legifrance_url"] = generate_legifrance_url(text_id, text_type)
        else:
            result["legifrance_url"] = None

    return enriched_results
