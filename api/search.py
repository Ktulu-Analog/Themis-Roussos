"""
Module Search Controller
Gère tous les endpoints de recherche de l'API Légifrance
"""

from typing import Dict, Any, Optional
from .base import BaseAPI


class SearchController(BaseAPI):
    """
    Contrôleur de recherche
    5 endpoints disponibles
    """

    def search(self, search_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recherche générique des documents indexés

        POST /search

        Args:
            search_request: Requête de recherche avec fond, filtres, pagination

        Returns:
            Résultats de recherche paginés

        Example:
            {
                "fond": "ALL",
                "recherche": {
                    "champs": [{
                        "typeChamp": "ALL",
                        "criteres": [{
                            "typeRecherche": "CONTIENT",
                            "valeur": "responsabilité civile"
                        }],
                        "operateur": "ET"
                    }],
                    "operateur": "ET",
                    "pageSize": 10,
                    "pageNumber": 1,
                    "sort": "PERTINENCE",
                    "typePagination": "DEFAUT"
                }
            }
        """
        return self.request("/search", method="POST", body=search_request)

    def canonical_article_version(
        self,
        article_id: str
    ) -> Dict[str, Any]:
        """
        Récupération des versions de l'article

        POST /search/canonicalArticleVersion

        Args:
            article_id: ID de l'article (REQUIRED, nom du param: id)

        Returns:
            Informations de version de l'article
        """
        return self.request(
            "/search/canonicalArticleVersion",
            method="POST",
            body={"id": article_id}
        )

    def canonical_version(
        self,
        cid_text: str,
        date: str,
        cid_section: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Récupération des infos de la version canonique

        POST /search/canonicalVersion

        Args:
            cid_text: CID du texte (REQUIRED, nom du param: cidText)
            date: Date de référence (REQUIRED, format YYYY-MM-DD)
            cid_section: CID de la section (optional, nom du param: cidSection)

        Returns:
            Informations de version canonique
        """
        body = {
            "cidText": cid_text,
            "date": date
        }
        if cid_section:
            body["cidSection"] = cid_section

        return self.request(
            "/search/canonicalVersion",
            method="POST",
            body=body
        )

    def nearest_version(
        self,
        cid_text: str,
        date: str,
        cid_section: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Récupération des infos de la version la plus proche

        POST /search/nearestVersion

        Args:
            cid_text: CID du texte (REQUIRED, nom du param: cidText)
            date: Date de référence (REQUIRED, format YYYY-MM-DD)
            cid_section: CID de la section (optional, nom du param: cidSection)

        Returns:
            Informations de la version la plus proche
        """
        body = {
            "cidText": cid_text,
            "date": date
        }
        if cid_section:
            body["cidSection"] = cid_section

        return self.request(
            "/search/nearestVersion",
            method="POST",
            body=body
        )

    def ping(self) -> Dict[str, Any]:
        """
        Teste le contrôleur de recherche

        GET /search/ping

        Returns:
            Status du contrôleur
        """
        return self.request("/search/ping", method="GET")
