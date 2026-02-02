"""
Module Suggest Controller
Gère tous les endpoints d'autosuggestion/autocomplétion de l'API Légifrance
4 endpoints disponibles
"""

from typing import Dict, Any, Optional, List
from .base import BaseAPI


class SuggestController(BaseAPI):
    """
    Contrôleur de suggestions et autocomplétion
    Permet d'obtenir des suggestions pour faciliter la recherche
    """

    def suggest(
        self,
        search_text: Optional[str] = None,
        supplies: Optional[List[str]] = None,
        documents_dits: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Suggestions de résultats génériques

        POST /suggest

        Args:
            search_text: Texte de recherche pour suggestions (optional, nom du param: searchText)
            supplies: Fonds à suggérer (optional, ex: ['JORF', 'JURI'])
            documents_dits: Documents dits (optional)

        Returns:
            Liste de suggestions

        Example:
            api.suggest(search_text="code civil")
        """
        body = {}
        if search_text:
            body["searchText"] = search_text
        if supplies:
            body["supplies"] = supplies
        if documents_dits is not None:
            body["documentsDits"] = documents_dits

        return self.request("/suggest", method="POST", body=body)

    def suggest_acco(self, search_text: Optional[str] = None) -> Dict[str, Any]:
        """
        Suggestions des SIRET et raisons sociales pour les accords d'entreprise

        POST /suggest/acco

        Args:
            search_text: Texte de recherche (optional, nom du param: searchText)

        Returns:
            Suggestions de SIRET et raisons sociales

        Example:
            api.suggest_acco(search_text="Renault")
        """
        body = {}
        if search_text:
            body["searchText"] = search_text

        return self.request("/suggest/acco", method="POST", body=body)

    def suggest_pdc(
        self,
        search_text: Optional[str] = None,
        origin: Optional[str] = None,
        fond: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Suggestions des libellés pour le plan de classement

        POST /suggest/pdc

        Args:
            search_text: Texte de recherche (optional, nom du param: searchText)
            origin: Origine (optional)
            fond: Fond (optional)

        Returns:
            Suggestions de libellés du plan de classement
        """
        body = {}
        if search_text:
            body["searchText"] = search_text
        if origin:
            body["origin"] = origin
        if fond:
            body["fond"] = fond

        return self.request("/suggest/pdc", method="POST", body=body)

    def ping(self) -> Dict[str, Any]:
        """
        Teste le contrôleur de suggestions

        GET /suggest/ping

        Returns:
            Status du contrôleur
        """
        return self.request("/suggest/ping", method="GET")
