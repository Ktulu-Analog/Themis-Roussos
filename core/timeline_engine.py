from datetime import datetime
from typing import Iterable, List

from core.models import LegalEvent
from core.reform_detector import score_event


class TimelineEngine:

    def __init__(self):
        self.events: List[LegalEvent] = []
        self._fingerprints = set()

    # -------------------------
    # fingerprint = anti doublons
    # -------------------------
    def _fp(self, e: LegalEvent):
        return (
            e.date.date(),
            e.title.lower().strip()
        )

    # -------------------------
    # INGEST LLM
    # -------------------------
    def ingest_llm_events(self, raw_events: Iterable[dict]):

        new_events = []

        for r in raw_events:

            event = LegalEvent(
                date=datetime.fromisoformat(r["date"]),
                title=r["title"],
                source="llm",
                event_type=self._guess_type(r["title"]),
            )

            fp = self._fp(event)

            if fp in self._fingerprints:
                continue

            event.score = score_event(event)

            self._fingerprints.add(fp)
            self.events.append(event)
            new_events.append(event)

        self.events.sort(key=lambda e: e.date)

        return new_events

    # -------------------------
    # TYPE GUESSING
    # -------------------------
    def _guess_type(self, title):

        t = title.lower()

        if "loi" in t:
            return "loi"
        if "décret" in t:
            return "decret"
        if "arrêté" in t:
            return "arrete"

        return "texte"

    # -------------------------
    # FUTUR : chrono ingestion
    # -------------------------
    def ingest_chrono(self, chrono_data):

        for version in chrono_data:
            event = LegalEvent(
                date=version["date"],
                title=version["label"],
                source="chrono",
                event_type="version"
            )

            fp = self._fp(event)

            if fp not in self._fingerprints:
                self.events.append(event)
                self._fingerprints.add(fp)

        self.events.sort(key=lambda e: e.date)

    # -------------------------
    # SORTIE
    # -------------------------
    def get_events(self):
        return self.events
