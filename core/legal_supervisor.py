class LegalSupervisor:

    def __init__(self, client, model):
        self.client = client
        self.model = model

    def run(self, messages):

        response, stats = chat_with_tools(
            messages,
            client=self.client,
            model=self.model,
            return_stats=True
        )

        clean, timeline_events = extract_timeline_json(response)

        events = timeline_engine.ingest_llm_events(timeline_events)

        return clean, events, stats
