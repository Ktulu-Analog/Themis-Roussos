"""
Timeline Ultra avec extraction JSON silencieuse
Détecte et extrait automatiquement les événements juridiques
"""

import logging
import json
import re
import yaml
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LegalEvent:
    """Événement juridique pour la timeline"""
    date: datetime
    title: str
    source: str
    event_type: str
    description: str = ""
    score: float = 0.0

    def to_dict(self) -> dict:
        """Conversion en dictionnaire"""
        return {
            "date": self.date.isoformat() if isinstance(self.date, datetime) else str(self.date),
            "title": self.title,
            "source": self.source,
            "event_type": self.event_type,
            "description": self.description,
            "score": self.score
        }


class TimelineUltra:
    """
    Moteur de timeline avec extraction JSON silencieuse
    Alimente automatiquement la mémoire persistante
    """

    def __init__(self, enable_memory: bool = True, conversation_id: str = None):
        """
        Args:
            enable_memory: Si True, utilise TimelineMemory pour la persistance
            conversation_id: ID de la conversation (pour timeline isolée)
        """
        self.events: List[LegalEvent] = []
        self._fingerprints = set()
        self.enable_memory = enable_memory
        self.conversation_id = conversation_id

        # Initialiser la mémoire si activée
        if self.enable_memory:
            try:
                from memory.timeline_memory import TimelineMemory
                self.memory = TimelineMemory(conversation_id=conversation_id)
                logger.info("✅ TimelineMemory initialisée")

                # Charger les événements existants
                self._load_from_memory()

            except ImportError as e:
                logger.warning(f"TimelineMemory non disponible: {e}")
                self.memory = None
                self.enable_memory = False
        else:
            self.memory = None

    def _load_from_memory(self):
        """Charger les événements depuis la mémoire persistante"""
        if not self.memory:
            return

        try:
            stored_events = self.memory.load_all_events()

            for stored in stored_events:
                payload = stored.get("payload", {})

                # Convertir en LegalEvent
                date_str = payload.get("date")
                if not date_str:
                    continue

                try:
                    date = datetime.fromisoformat(date_str) if isinstance(date_str, str) else date_str
                except:
                    continue

                event = LegalEvent(
                    date=date,
                    title=payload.get("title", ""),
                    source=payload.get("source", "unknown"),
                    event_type=payload.get("event_type", "modification"),
                    description=payload.get("description", "")
                )

                # Ajouter sans dupliquer
                fp = self._fingerprint(event)
                if fp not in self._fingerprints:
                    self.events.append(event)
                    self._fingerprints.add(fp)

            logger.info(f"📚 {len(self.events)} événements chargés depuis la mémoire")

        except Exception as e:
            logger.error(f"Erreur chargement mémoire: {e}")

    def _fingerprint(self, event: LegalEvent) -> tuple:
        """Générer une empreinte unique pour détecter les doublons"""
        date_key = event.date.date() if isinstance(event.date, datetime) else event.date
        return (date_key, event.title.lower().strip()[:100])

    def ingest_llm_events(self, events: List[Any]) -> List[LegalEvent]:
        """
        Ingérer des événements depuis le LLM

        Args:
            events: Liste d'événements (TimelineEvent ou dict)

        Returns:
            Liste des nouveaux événements ajoutés
        """
        new_events = []

        for event in events:
            # Convertir TimelineEvent en LegalEvent
            if hasattr(event, 'date') and hasattr(event, 'title'):
                legal_event = LegalEvent(
                    date=event.date,
                    title=event.title,
                    source="llm",
                    event_type=getattr(event, 'event_type', 'modification'),
                    description=getattr(event, 'description', ''),
                    score=self._score_event(event.title, getattr(event, 'event_type', ''))
                )
            elif isinstance(event, dict):
                # Événement au format dict
                date_str = event.get("date")
                try:
                    date = datetime.fromisoformat(date_str) if isinstance(date_str, str) else date_str
                except:
                    logger.warning(f"Date invalide: {date_str}")
                    continue

                legal_event = LegalEvent(
                    date=date,
                    title=event.get("title", ""),
                    source="llm",
                    event_type=event.get("event_type", "modification"),
                    description=event.get("description", ""),
                    score=self._score_event(event.get("title", ""), event.get("event_type", ""))
                )
            else:
                logger.warning(f"Format d'événement non reconnu: {type(event)}")
                continue

            # Vérifier les doublons
            fp = self._fingerprint(legal_event)
            if fp in self._fingerprints:
                logger.debug(f"Doublon ignoré: {legal_event.title}")
                continue

            # Ajouter à la timeline
            self.events.append(legal_event)
            self._fingerprints.add(fp)
            new_events.append(legal_event)

            # Persister dans la mémoire
            if self.memory:
                try:
                    self.memory.upsert_event(legal_event)
                except Exception as e:
                    logger.error(f"Erreur persistance: {e}")

        # Trier par date
        self.events.sort(key=lambda e: e.date)

        if new_events:
            logger.info(f"✅ {len(new_events)} nouveaux événements ajoutés à la timeline")

        return new_events

    def _score_event(self, title: str, event_type: str) -> float:
        """Calculer un score d'importance pour l'événement"""
        score = 0.0
        title_lower = title.lower()

        # Par type
        if event_type == "loi":
            score += 0.4
        elif event_type == "decret":
            score += 0.2

        # Par contenu
        if any(word in title_lower for word in ["réforme", "codification"]):
            score += 0.3
        if any(word in title_lower for word in ["travail", "social", "emploi"]):
            score += 0.2

        return min(score, 1.0)

    def get_events(self) -> List[LegalEvent]:
        """Retourner tous les événements triés"""
        return sorted(self.events, key=lambda e: e.date)

    def get_events_range(self, start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None) -> List[LegalEvent]:
        """Retourner les événements dans une plage de dates"""
        events = self.get_events()

        if start_date:
            events = [e for e in events if e.date >= start_date]
        if end_date:
            events = [e for e in events if e.date <= end_date]

        return events

    def clear(self):
        """Vider la timeline (sans toucher à la mémoire persistante)"""
        self.events.clear()
        self._fingerprints.clear()
        logger.info("Timeline vidée")


def load_timeline_extraction_prompt() -> str:
    """
    Charger le prompt d'extraction de timeline depuis prompt.yml

    Returns:
        Prompt d'extraction
    """
    with open("prompt.yml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        return config["timeline_extraction_prompt"]


def extract_events_silently(
    client,
    model: str,
    response_text: str,
    extraction_model: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    EXTRACTION SILENCIEUSE JSON avec modèle dédié optimisé

    Appelle le LLM pour extraire les événements d'une réponse
    sans afficher quoi que ce soit à l'utilisateur

    Args:
        client: Client OpenAI
        model: Nom du modèle principal
        response_text: Texte de la réponse à analyser
        extraction_model: Modèle léger pour l'extraction (optionnel, recommandé)
                         Ex: "claude-haiku-4-5-20251001" ou "gpt-3.5-turbo"

    Returns:
        Liste d'événements au format dict

    """

    # Utiliser le modèle léger si spécifié, sinon le modèle principal
    model_to_use = extraction_model or model

    if extraction_model and extraction_model != model:
        logger.info(f"🎯 Extraction optimisée avec modèle léger: {extraction_model}")
    else:
        logger.info(f"🔍 Extraction avec modèle principal: {model}")

    # Charger le prompt depuis prompt.yml
    EXTRACTION_PROMPT = load_timeline_extraction_prompt()

    try:
        logger.info(f"🔍 Extraction silencieuse JSON en cours avec {model_to_use}...")

        response = client.chat.completions.create(
            model=model_to_use,  # 🔥 Modèle optimisé (léger si spécifié)
            temperature=0,
            messages=[
                {"role": "system", "content": EXTRACTION_PROMPT},
                {"role": "user", "content": response_text}
            ]
        )

        json_text = response.choices[0].message.content.strip()

        # Nettoyer le JSON (enlever les markdown fences si présents)
        json_text = re.sub(r'^```json\s*', '', json_text)
        json_text = re.sub(r'\s*```$', '', json_text)

        # Parser le JSON
        events = json.loads(json_text)

        if not isinstance(events, list):
            logger.warning("Le JSON retourné n'est pas une liste")
            return []

        # Convertir les dates
        for event in events:
            if "date" in event and isinstance(event["date"], str):
                try:
                    event["date"] = datetime.fromisoformat(event["date"])
                except:
                    # Fallback : essayer de parser juste l'année
                    year_match = re.search(r'\b(19|20)\d{2}\b', event["date"])
                    if year_match:
                        event["date"] = datetime(int(year_match.group()), 1, 1)
                    else:
                        logger.warning(f"Date invalide: {event['date']}")
                        continue

        logger.info(f"✅ {len(events)} événements extraits silencieusement")
        return events

    except json.JSONDecodeError as e:
        logger.error(f"Erreur parsing JSON: {e}")
        logger.error(f"Contenu reçu: {json_text[:200]}")
        return []
    except Exception as e:
        logger.error(f"Erreur extraction silencieuse: {e}")
        return []


def render_timeline_ultra(timeline: TimelineUltra):
    """
    Afficher la timeline dans Streamlit

    Args:
        timeline: Instance de TimelineUltra
    """
    import streamlit as st
    from timeline_header import display_timeline_header, TimelineEvent

    # Convertir LegalEvent en TimelineEvent pour l'affichage
    display_events = []
    for event in timeline.get_events():
        display_events.append(TimelineEvent(
            date=event.date,
            title=event.title,
            event_type=event.event_type,
            description=event.description,
            details=f"Source: {event.source} | Score: {event.score:.2f}"
        ))

    # Afficher
    display_timeline_header(display_events)

    # Stats compactes
    if display_events:
        col1, col2, col3 = st.columns(3)
        col1.metric("📅 Événements", len(display_events))

        # Plus ancien et plus récent
        if len(display_events) >= 2:
            oldest = min(e.date for e in display_events)
            newest = max(e.date for e in display_events)
            col2.metric("📆 Plus ancien", oldest.strftime("%Y"))
            col3.metric("📆 Plus récent", newest.strftime("%Y"))
