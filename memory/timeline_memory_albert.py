import hashlib
import json
from datetime import datetime
from typing import List, Optional
import logging

from memory.albert_collection_client import AlbertCollectionClient

logger = logging.getLogger(__name__)


class TimelineMemory:
    """
    Mémoire persistante pour la timeline via l'API Albert
    """

    def __init__(self):
        # Client Albert pour les collections
        self.client = AlbertCollectionClient()

    # -------------------------------------------------
    # UTILS
    # -------------------------------------------------

    def _hash_event(self, event) -> str:
        """Générer un ID unique pour l'événement"""
        key = f"{event.date}-{event.title}"
        return hashlib.sha256(key.encode()).hexdigest()

    def _event_to_content(self, event) -> str:
        """Convertir un événement en texte pour l'embedding"""
        return f"{event.date} {event.title}"

    def _event_to_metadata(self, event) -> dict:
        """Convertir un événement en metadata"""
        return {
            "date": event.date,
            "title": event.title,
            "source": getattr(event, "source", "unknown"),
            "event_type": getattr(event, "event_type", "unknown"),
            "timestamp": datetime.utcnow().isoformat()
        }

    # -------------------------------------------------
    # OPERATIONS
    # -------------------------------------------------

    def upsert_event(self, event):
        """Ajouter ou mettre à jour un événement"""

        # Vérifier si un événement similaire existe déjà
        if self.similar_exists(event):
            logger.info(f"Événement similaire existe déjà: {event.title}")
            return

        # Générer l'ID unique
        event_id = self._hash_event(event)

        # Préparer le contenu et les métadonnées
        content = self._event_to_content(event)
        metadata = self._event_to_metadata(event)

        # Ajouter à la collection Albert
        success = self.client.add_document(
            document_id=event_id,
            content=content,
            metadata=metadata
        )

        if success:
            logger.info(f"Événement ajouté: {event.title}")
        else:
            logger.error(f"Échec ajout événement: {event.title}")

    def load_all_events(self) -> List:
        """Charger tous les événements de la collection"""

        documents = self.client.list_documents()

        # Convertir les documents en objets compatibles
        events = []
        for doc in documents:
            # Les documents Albert ont une structure avec metadata
            events.append({
                "payload": doc.get("metadata", {})
            })

        logger.info(f"Chargé {len(events)} événements depuis Albert")
        return events

    def similar_exists(self, event, threshold: float = 0.85) -> bool:
        """
        Vérifier si un événement similaire existe déjà

        Utilise la recherche sémantique d'Albert pour détecter
        les doublons potentiels
        """

        query = self._event_to_content(event)

        # Rechercher dans la collection
        results = self.client.search(
            query=query,
            limit=1,
            score_threshold=threshold
        )

        if not results:
            return False

        # Vérifier le score du meilleur résultat
        top_result = results[0]
        score = top_result.get("score", 0.0)

        if score >= threshold:
            logger.info(f"Doublon détecté (score={score:.2f}): {event.title}")
            return True

        return False

    # -------------------------------------------------
    # ADMIN
    # -------------------------------------------------

    def clear_all(self) -> bool:
        """Supprimer tous les événements (pour debug)"""

        documents = self.client.list_documents()

        success_count = 0
        for doc in documents:
            doc_id = doc.get("id")
            if doc_id and self.client.delete_document(doc_id):
                success_count += 1

        logger.info(f"Supprimé {success_count}/{len(documents)} événements")
        return success_count == len(documents)

    def get_stats(self) -> dict:
        """Obtenir des statistiques sur la collection"""

        documents = self.client.list_documents()

        return {
            "total_events": len(documents),
            "collection_id": self.client.collection_id,
            "collection_name": self.client.collection_name
        }
