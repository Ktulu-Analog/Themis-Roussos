import os
import requests
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class AlbertCollectionClient:
    """
    Client pour gérer les collections via l'API Albert
    Documentation: https://albert.api.etalab.gouv.fr/swagger
    """

    def __init__(self):
        self.base_url = "https://albert.api.etalab.gouv.fr/v1"
        self.api_key = os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY non défini")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        self.collection_name = "legal_timeline"
        self.collection_id = None

        # Initialiser ou récupérer la collection
        self._init_collection()

    # -------------------------------------------------
    # COLLECTIONS
    # -------------------------------------------------

    def _init_collection(self):
        """Créer ou récupérer la collection timeline"""

        # 1. Lister les collections existantes
        collections = self.list_collections()

        # 2. Chercher si notre collection existe
        for coll in collections:
            # Format: {"id": 783, "name": "legal_timeline", ...}
            if isinstance(coll, dict):
                if coll.get("name") == self.collection_name:
                    self.collection_id = str(coll.get("id"))
                    logger.info(f"Collection '{self.collection_name}' trouvée: {self.collection_id}")
                    return

        # 3. Créer la collection si elle n'existe pas
        self.collection_id = self.create_collection(
            name=self.collection_name,
            description="Timeline des événements juridiques",
            model="BAAI/bge-m3"
        )

        if self.collection_id:
            logger.info(f"Collection '{self.collection_name}' créée: {self.collection_id}")
        else:
            logger.error(f"Échec création collection '{self.collection_name}'")

    def list_collections(self) -> List[Dict[str, Any]]:
        """Liste toutes les collections"""

        try:
            response = requests.get(
                f"{self.base_url}/collections",
                headers=self.headers,
                timeout=30
            )

            logger.info(f"list_collections status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()

                # Format OpenAI-style: {"object": "list", "data": [...]}
                if isinstance(data, dict) and 'data' in data:
                    collections = data['data']
                    logger.info(f"Trouvé {len(collections)} collection(s)")
                    return collections

                # Fallback: liste directe
                elif isinstance(data, list):
                    return data

                # Autre fallback
                elif isinstance(data, dict) and 'collections' in data:
                    return data['collections']
                else:
                    logger.warning(f"Format inattendu: {data}")
                    return []

            logger.warning(f"Erreur listing collections: {response.status_code} - {response.text[:200]}")
            return []

        except Exception as e:
            logger.error(f"Erreur listing collections: {e}")
            return []

    def create_collection(
        self,
        name: str,
        description: str = "",
        model: str = "BAAI/bge-m3"
    ) -> Optional[str]:
        """Créer une nouvelle collection"""

        payload = {
            "name": name,
            "description": description,
            "model": model
        }

        try:
            response = requests.post(
                f"{self.base_url}/collections",
                json=payload,
                headers=self.headers,
                timeout=30
            )

            if response.status_code in [200, 201]:
                data = response.json()
                # L'API retourne {"id": 68921}
                collection_id = str(data.get("id"))
                logger.info(f"Collection '{name}' créée avec ID: {collection_id}")
                return collection_id

            logger.error(f"Erreur création collection: {response.status_code} - {response.text}")
            return None

        except Exception as e:
            logger.error(f"Exception création collection: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    # -------------------------------------------------
    # DOCUMENTS
    # -------------------------------------------------

    def add_document(
        self,
        document_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Ajouter un document à la collection"""

        if not self.collection_id:
            logger.error("Collection non initialisée")
            return False

        payload = {
            "id": document_id,
            "content": content,
            "metadata": metadata or {}
        }

        try:
            response = requests.post(
                f"{self.base_url}/collections/{self.collection_id}/documents",
                json=payload,
                headers=self.headers,
                timeout=30
            )

            if response.status_code in [200, 201]:
                logger.info(f"Document {document_id} ajouté")
                return True

            logger.warning(f"Erreur ajout document: {response.status_code} - {response.text}")
            return False

        except Exception as e:
            logger.error(f"Erreur ajout document: {e}")
            return False

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Récupérer un document par son ID"""

        if not self.collection_id:
            return None

        try:
            response = requests.get(
                f"{self.base_url}/collections/{self.collection_id}/documents/{document_id}",
                headers=self.headers,
                timeout=30
            )

            if response.status_code == 200:
                return response.json()

            return None

        except Exception as e:
            logger.error(f"Erreur récupération document: {e}")
            return None

    def list_documents(self) -> List[Dict[str, Any]]:
        """Liste tous les documents de la collection"""

        if not self.collection_id:
            return []

        try:
            response = requests.get(
                f"{self.base_url}/collections/{self.collection_id}/documents",
                headers=self.headers,
                timeout=30
            )

            if response.status_code == 200:
                return response.json()

            return []

        except Exception as e:
            logger.error(f"Erreur listing documents: {e}")
            return []

    def delete_document(self, document_id: str) -> bool:
        """Supprimer un document"""

        if not self.collection_id:
            return False

        try:
            response = requests.delete(
                f"{self.base_url}/collections/{self.collection_id}/documents/{document_id}",
                headers=self.headers,
                timeout=30
            )

            return response.status_code in [200, 204]

        except Exception as e:
            logger.error(f"Erreur suppression document: {e}")
            return False

    # -------------------------------------------------
    # SEARCH
    # -------------------------------------------------

    def search(
        self,
        query: str,
        limit: int = 5,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Rechercher dans la collection"""

        if not self.collection_id:
            return []

        payload = {
            "collections": [self.collection_id],
            "prompt": query,
            "k": limit,
            "score_threshold": score_threshold
        }

        try:
            response = requests.post(
                f"{self.base_url}/search",
                json=payload,
                headers=self.headers,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("chunks", [])

            logger.warning(f"Erreur recherche: {response.status_code}")
            return []

        except Exception as e:
            logger.error(f"Erreur recherche: {e}")
            return []
