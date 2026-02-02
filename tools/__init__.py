"""
Outils pour l'intégration de l'API Légifrance avec les LLM
Package modulaire pour une meilleure organisation du code
"""

from .api_instance import get_api
from .definitions import get_tools_definition, TOOLS
from .executor import execute_tool
from .orchestrator import chat_with_tools
from .formatters import format_search_results, format_result_with_link
from .url_builder import generate_legifrance_url, enrich_search_results_with_links
from .request_builders import build_search_request, CODE_IDS

__all__ = [
    # Instance API
    'get_api',
    
    # Définitions des outils
    'get_tools_definition',
    'TOOLS',
    
    # Exécution
    'execute_tool',
    'chat_with_tools',
    
    # Formatage
    'format_search_results',
    'format_result_with_link',
    
    # URLs
    'generate_legifrance_url',
    'enrich_search_results_with_links',
    
    # Builders
    'build_search_request',
    'CODE_IDS',
]
