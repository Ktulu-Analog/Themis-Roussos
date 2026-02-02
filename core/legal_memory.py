class LegalMemory:

    def __init__(self):
        self.dossiers = {}

    def get_or_create(self, topic):
        if topic not in self.dossiers:
            self.dossiers[topic] = {
                "timeline": [],
                "texts": set()
            }
        return self.dossiers[topic]
