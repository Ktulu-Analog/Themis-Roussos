"""
Gestion de l'instance globale de l'API Légifrance
"""

import logging
from typing import Optional
from legifrance_api import LegifranceAPI

logger = logging.getLogger(__name__)

# Instance globale API
_api_instance: Optional[LegifranceAPI] = None


def get_api() -> LegifranceAPI:
    """
    Obtient ou crée l'instance globale de l'API Légifrance
    
    Returns:
        LegifranceAPI: Instance singleton de l'API
        
    Example:
        >>> api = get_api()
        >>> results = api.search({"recherche": {...}})
    """
    global _api_instance
    if _api_instance is None:
        _api_instance = LegifranceAPI()
        logger.info("Instance API Légifrance créée")
    return _api_instance


def reset_api() -> None:
    """
    Réinitialise l'instance globale de l'API
    Utile pour les tests ou le changement de credentials
    """
    global _api_instance
    _api_instance = None
    logger.info("Instance API Légifrance réinitialisée")
