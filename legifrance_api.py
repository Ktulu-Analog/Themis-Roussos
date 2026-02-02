"""
API Légifrance unifiée

Classe principale qui combine tous les contrôleurs pour fournir
un accès complet aux 68 endpoints de l'API PISTE Légifrance.

Ce module expose la classe LegifranceAPI qui hérite de tous les
contrôleurs spécialisés via l'héritage multiple, offrant ainsi
une interface unifiée pour :
    - Recherche de textes juridiques
    - Consultation de codes et articles
    - Listage de documents
    - Suggestions et autocomplétion
    - Gestion des versions chronologiques
    - Services utilitaires

Architecture:
    LegifranceAPI hérite de 6 contrôleurs:
        - SearchController (5 endpoints)
        - ConsultController (39 endpoints)
        - ListController (13 endpoints)
        - SuggestController (4 endpoints)
        - ChronoController (4 endpoints)
        - MiscController (3 endpoints)

Authentification:
    OAuth 2.0 Client Credentials Flow géré automatiquement
    par la classe de base BaseAPI.

Example:
    >>> from legifrance_api import LegifranceAPI
    >>> 
    >>> api = LegifranceAPI()
    >>> results = api.search({"recherche": {...}})
    >>> code = api.get_code("LEGITEXT000006070721")
    
    # Avec context manager
    >>> with LegifranceAPI() as api:
    ...     codes = api.list_codes()
"""

from typing import Optional
from api.base import LegifranceAPIError
from api.search import SearchController
from api.consult import ConsultController
from api.list import ListController
from api.suggest import SuggestController
from api.chrono import ChronoController
from api.misc import MiscController


class LegifranceAPI(
    SearchController,
    ConsultController,
    ListController,
    SuggestController,
    ChronoController,
    MiscController
):
    """
    API Légifrance complète
    
    Hérite de tous les contrôleurs pour fournir une interface unifiée
    d'accès à l'ensemble des 68 endpoints de l'API Légifrance.
    
    Contrôleurs disponibles:
        - SearchController: 5 endpoints de recherche
        - ConsultController: 39 endpoints de consultation
        - ListController: 13 endpoints de listage
        - SuggestController: 4 endpoints de suggestions
        - ChronoController: 4 endpoints de gestion des versions
        - MiscController: 3 endpoints utilitaires
    
    Example:
        >>> from legifrance_api import LegifranceAPI
        >>> 
        >>> with LegifranceAPI() as api:
        ...     # Recherche
        ...     results = api.search({"recherche": {...}})
        ...     
        ...     # Consultation
        ...     code = api.get_code("LEGITEXT000006070721")
        ...     
        ...     # Liste
        ...     codes = api.list_codes()
        ...     
        ...     # Suggestions
        ...     suggestions = api.suggest("code civil")
    """
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        """
        Initialise l'API Légifrance complète
        
        Args:
            client_id: Client ID OAuth (ou depuis LEGIFRANCE_CLIENT_ID)
            client_secret: Client Secret OAuth (ou depuis LEGIFRANCE_CLIENT_SECRET)
        """
        # Initialiser la classe de base (héritée par tous les contrôleurs)
        super().__init__(client_id, client_secret)
    
    def __repr__(self) -> str:
        return (
            f"<LegifranceAPI("
            f"base_url='{self.base_url}', "
            f"controllers=['Search', 'Consult', 'List', 'Suggest', 'Chrono', 'Misc']"
            f")>"
        )


# Exposer les exceptions et la classe principale
__all__ = ['LegifranceAPI', 'LegifranceAPIError']
