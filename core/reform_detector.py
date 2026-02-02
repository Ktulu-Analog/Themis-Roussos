def score_event(event: LegalEvent):

    score = 0

    if event.event_type == "loi":
        score += 0.4

    if "codification" in event.title.lower():
        score += 0.5

    if "réforme" in event.title.lower():
        score += 0.3

    return min(score, 1.0)
