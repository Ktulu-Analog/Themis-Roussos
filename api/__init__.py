"""
Package API Légifrance
Architecture modulaire par contrôleur
"""

from .base import BaseAPI, LegifranceAPIError
from .search import SearchController
from .consult import ConsultController
from .list import ListController
from .suggest import SuggestController
from .chrono import ChronoController
from .misc import MiscController

__all__ = [
    'BaseAPI',
    'LegifranceAPIError',
    'SearchController',
    'ConsultController',
    'ListController',
    'SuggestController',
    'ChronoController',
    'MiscController',
]

__version__ = '3.0.0'
