import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import logging
import shutil

logger = logging.getLogger(__name__)


class ConversationManager:
    """
    Gestionnaire de conversations multiples avec timelines isolées

    Chaque conversation a :
    - Un ID unique
    - Un nom généré par le LLM
    - Son propre historique de messages
    - Sa propre timeline d'événements
    """

    def __init__(self, base_dir: str = "data/conversations"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.index_file = self.base_dir.parent / "conversations_index.json"
        self.index = self._load_index()

    def _load_index(self) -> dict:
        """Charger l'index des conversations"""
        if not self.index_file.exists():
            return {"conversations": []}

        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erreur chargement index: {e}")
            return {"conversations": []}

    def _save_index(self):
        """Sauvegarder l'index"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Erreur sauvegarde index: {e}")

    def create_conversation(self) -> str:
        """
        Créer une nouvelle conversation

        Returns:
            ID de la conversation
        """
        # Générer un ID unique
        conv_id = f"conv_{uuid.uuid4().hex[:12]}"

        # Créer le dossier
        conv_dir = self.base_dir / conv_id
        conv_dir.mkdir(parents=True, exist_ok=True)

        # Créer les metadata
        metadata = {
            "id": conv_id,
            "name": "Nouvelle conversation",  # Sera mis à jour par le LLM
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "message_count": 0,
            "event_count": 0
        }

        # Sauvegarder metadata
        with open(conv_dir / "metadata.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        # Créer fichiers vides
        with open(conv_dir / "messages.json", 'w', encoding='utf-8') as f:
            json.dump([], f)

        with open(conv_dir / "timeline_events.json", 'w', encoding='utf-8') as f:
            json.dump({}, f)

        # Ajouter à l'index
        self.index["conversations"].append({
            "id": conv_id,
            "name": metadata["name"],
            "created_at": metadata["created_at"],
            "updated_at": metadata["updated_at"],
            "message_count": 0,
            "event_count": 0
        })
        self._save_index()

        logger.info(f"✅ Conversation créée: {conv_id}")
        return conv_id

    def list_conversations(self) -> List[Dict]:
        """Lister toutes les conversations (triées par date de modification)"""
        return sorted(
            self.index["conversations"],
            key=lambda x: x["updated_at"],
            reverse=True
        )

    def get_conversation(self, conv_id: str) -> Optional[Dict]:
        """Récupérer une conversation complète par ID"""
        conv_dir = self.base_dir / conv_id

        if not conv_dir.exists():
            return None

        try:
            with open(conv_dir / "metadata.json", 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            with open(conv_dir / "messages.json", 'r', encoding='utf-8') as f:
                messages = json.load(f)

            return {
                "metadata": metadata,
                "messages": messages
            }
        except Exception as e:
            logger.error(f"Erreur chargement conversation {conv_id}: {e}")
            return None

    def update_conversation_name(self, conv_id: str, name: str):
        """Mettre à jour le nom d'une conversation (généré par LLM)"""
        conv_dir = self.base_dir / conv_id

        if not conv_dir.exists():
            return False

        try:
            # Charger metadata
            with open(conv_dir / "metadata.json", 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            # Mettre à jour
            metadata["name"] = name
            metadata["updated_at"] = datetime.utcnow().isoformat()

            # Sauvegarder
            with open(conv_dir / "metadata.json", 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            # Mettre à jour l'index
            for conv in self.index["conversations"]:
                if conv["id"] == conv_id:
                    conv["name"] = name
                    conv["updated_at"] = metadata["updated_at"]
                    break

            self._save_index()

            logger.info(f"✅ Nom mis à jour: {conv_id} → {name}")
            return True

        except Exception as e:
            logger.error(f"Erreur mise à jour nom: {e}")
            return False

    def add_message(self, conv_id: str, message: Dict):
        """Ajouter un message à la conversation"""
        conv_dir = self.base_dir / conv_id

        try:
            # Charger messages
            with open(conv_dir / "messages.json", 'r', encoding='utf-8') as f:
                messages = json.load(f)

            # Ajouter
            messages.append(message)

            # Sauvegarder
            with open(conv_dir / "messages.json", 'w', encoding='utf-8') as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)

            # Mettre à jour metadata
            with open(conv_dir / "metadata.json", 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            metadata["message_count"] = len(messages)
            metadata["updated_at"] = datetime.utcnow().isoformat()

            with open(conv_dir / "metadata.json", 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            # Mettre à jour l'index
            for conv in self.index["conversations"]:
                if conv["id"] == conv_id:
                    conv["message_count"] = metadata["message_count"]
                    conv["updated_at"] = metadata["updated_at"]
                    break

            self._save_index()

        except Exception as e:
            logger.error(f"Erreur ajout message: {e}")

    def update_event_count(self, conv_id: str, count: int):
        """Mettre à jour le nombre d'événements dans la timeline"""
        conv_dir = self.base_dir / conv_id

        try:
            # Mettre à jour metadata
            with open(conv_dir / "metadata.json", 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            metadata["event_count"] = count
            metadata["updated_at"] = datetime.utcnow().isoformat()

            with open(conv_dir / "metadata.json", 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            # Mettre à jour l'index
            for conv in self.index["conversations"]:
                if conv["id"] == conv_id:
                    conv["event_count"] = count
                    conv["updated_at"] = metadata["updated_at"]
                    break

            self._save_index()

        except Exception as e:
            logger.error(f"Erreur mise à jour event_count: {e}")

    def delete_conversation(self, conv_id: str) -> bool:
        """Supprimer une conversation"""
        conv_dir = self.base_dir / conv_id

        if not conv_dir.exists():
            return False

        try:
            # Supprimer le dossier
            shutil.rmtree(conv_dir)

            # Retirer de l'index
            self.index["conversations"] = [
                c for c in self.index["conversations"]
                if c["id"] != conv_id
            ]
            self._save_index()

            logger.info(f"✅ Conversation supprimée: {conv_id}")
            return True

        except Exception as e:
            logger.error(f"Erreur suppression conversation: {e}")
            return False

    def get_timeline_path(self, conv_id: str) -> Path:
        """Obtenir le chemin du fichier timeline pour une conversation"""
        return self.base_dir / conv_id / "timeline_events.json"
