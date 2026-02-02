from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass(slots=True)
class LegalEvent:
    date: datetime
    title: str
    source: str  # chrono | llm | consult
    event_type: str  # loi | decret | jurisprudence
    text_id: Optional[str] = None
    score: float = 0.0
    metadata: dict = field(default_factory=dict)
