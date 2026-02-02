"""
Module Misc Controller
Gère les endpoints de services divers de l'API Légifrance
3 endpoints disponibles
"""

from typing import Dict, Any, List
from .base import BaseAPI


class MiscController(BaseAPI):
    """
    Contrôleur de services divers
    Fournit des informations utilitaires sur l'API
    """

    def get_commit_id(self) -> Dict[str, Any]:
        """
        Informations de déploiement et versioning de l'API

        GET /misc/commitId

        Returns:
            Informations sur la version déployée de l'API

        Example:
            {
                "commitId": "abc123...",
                "version": "2.4.2",
                ...
            }
        """
        return self.request("/misc/commitId", method="GET")

    def get_dates_without_jo(self) -> Dict[str, Any]:
        """
        Liste des dates sans Journal Officiel

        GET /misc/datesWithoutJo

        Returns:
            Liste des dates où aucun JO n'a été publié
        """
        return self.request("/misc/datesWithoutJo", method="GET")

    def get_years_without_table(self) -> Dict[str, Any]:
        """
        Liste des années sans table annuelle

        GET /misc/yearsWithoutTable

        Returns:
            Liste des années sans table annuelle disponible
        """
        return self.request("/misc/yearsWithoutTable", method="GET")
