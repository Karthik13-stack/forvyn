import uuid
import time

class VersioningService:

    def __init__(self):
        self.versions = {}

    def save(self, doc_id, content):
        if doc_id not in self.versions:
            self.versions[doc_id] = []
        self.versions[doc_id].append({'id': str(uuid.uuid4()), 'time': time.time(), 'content': content})

    def get_versions(self, doc_id):
        return self.versions.get(doc_id, [])