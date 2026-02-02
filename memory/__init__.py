"""
Module de mémoire persistante pour la timeline
Utilise l'API Albert pour le stockage des collections
Enfin, quand le endpoint fonctionnera.
Pour l'instant ça utilise un stockage local json dans /DATA
"""

from .albert_collection_client import AlbertCollectionClient
from .timeline_memory_albert import TimelineMemory

__all__ = [
    "AlbertCollectionClient",
    "TimelineMemory",
]
