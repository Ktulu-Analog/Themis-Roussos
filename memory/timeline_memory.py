import hashlib
import json
from datetime import datetime
from typing import List, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class TimelineMemory:
    """
    Mémoire persistante pour la timeline en JSON local
    Supporte les conversations isolées
    """

    def __init__(self, conversation_id: str = None, storage_file: str = None):
        """
        Args:
            conversation_id: ID de la conversation (pour timeline isolée)
            storage_file: Chemin custom du fichier (optionnel)
        """
        if storage_file:
            # Chemin explicite fourni
            self.storage_file = Path(storage_file)
        elif conversation_id:
            # Timeline liée à une conversation
            self.storage_file = Path(f"data/conversations/{conversation_id}/timeline_events.json")
        else:
            # Fallback : fichier global
            self.storage_file = Path("data/timeline_events.json")

        self.storage_file.parent.mkdir(parents=True, exist_ok=True)

        # Charger les événements existants
        self.events_db = self._load_from_file()

        logger.info(f"✅ TimelineMemory initialisée: {len(self.events_db)} événements")

        # Compatibilité avec le code existant
        self.collection_id = conversation_id or "global"
        self.collection_name = f"timeline_{conversation_id}" if conversation_id else "timeline_global"

    def _load_from_file(self) -> dict:
        """Charger les événements depuis le fichier JSON"""
        if not self.storage_file.exists():
            logger.info(f"Création nouveau fichier: {self.storage_file}")
            return {}

        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Chargé {len(data)} événements depuis {self.storage_file}")
            return data
        except Exception as e:
            logger.error(f"Erreur lecture fichier: {e}")
            return {}

    def _save_to_file(self):
        """Sauvegarder les événements dans le fichier JSON"""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.events_db, f, ensure_ascii=False, indent=2)
            logger.debug(f"💾 Sauvegarde réussie: {len(self.events_db)} événements")
        except Exception as e:
            logger.error(f"Erreur sauvegarde fichier: {e}")

    def _hash_event(self, event) -> str:
        """Générer un ID unique pour l'événement"""
        date_str = event.date.isoformat() if isinstance(event.date, datetime) else str(event.date)
        key = f"{date_str}-{event.title}"
        return hashlib.sha256(key.encode()).hexdigest()

    def _event_to_dict(self, event) -> dict:
        """Convertir un événement en dictionnaire JSON"""
        date_str = event.date.isoformat() if isinstance(event.date, datetime) else str(event.date)

        return {
            "date": date_str,
            "title": event.title,
            "source": getattr(event, "source", "unknown"),
            "event_type": getattr(event, "event_type", "unknown"),
            "description": getattr(event, "description", ""),
            "score": getattr(event, "score", 0.0),
            "timestamp": datetime.utcnow().isoformat()
        }

    # -------------------------------------------------
    # OPERATIONS
    # -------------------------------------------------

    def upsert_event(self, event):
        """Ajouter ou mettre à jour un événement"""

        event_id = self._hash_event(event)

        # Vérifier si existe déjà
        if event_id in self.events_db:
            logger.debug(f"Événement existe déjà: {event.title}")
            return

        # Ajouter au dictionnaire
        self.events_db[event_id] = self._event_to_dict(event)

        # Sauvegarder immédiatement
        self._save_to_file()

        logger.info(f"✅ Événement ajouté: {event.title}")

    def load_all_events(self) -> List:
        """Charger tous les événements"""
        events = []

        for event_id, event_data in self.events_db.items():
            events.append({
                "payload": event_data
            })

        logger.info(f"📚 Chargé {len(events)} événements depuis JSON")
        return events

    def similar_exists(self, event, threshold: float = 0.85) -> bool:
        """
        Vérifier si un événement similaire existe déjà
        Version simplifiée : comparaison exacte sur hash
        (pas de recherche sémantique comme Albert)
        """
        event_id = self._hash_event(event)
        exists = event_id in self.events_db

        if exists:
            logger.debug(f"Doublon détecté: {event.title}")

        return exists

    # -------------------------------------------------
    # ADMIN
    # -------------------------------------------------

    def clear_all(self) -> bool:
        """Supprimer tous les événements"""
        count = len(self.events_db)
        self.events_db.clear()
        self._save_to_file()
        logger.info(f"🗑️ Supprimé {count} événements")
        return True

    def get_stats(self) -> dict:
        """Obtenir des statistiques"""
        return {
            "total_events": len(self.events_db),
            "collection_id": self.collection_id,
            "collection_name": self.collection_name,
            "storage_file": str(self.storage_file),
            "storage_type": "local_json"
        }

    def export_to_json(self, filepath: str) -> bool:
        """Exporter tous les événements vers un fichier JSON"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.events_db, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ Export réussi vers {filepath}")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur export: {e}")
            return False

    def import_from_json(self, filepath: str) -> bool:
        """Importer des événements depuis un fichier JSON"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                imported_data = json.load(f)

            # Fusionner avec les événements existants
            self.events_db.update(imported_data)
            self._save_to_file()

            logger.info(f"✅ Import réussi: {len(imported_data)} événements")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur import: {e}")
            return False
