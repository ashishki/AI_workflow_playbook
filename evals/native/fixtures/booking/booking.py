"""Small local booking store used by the future consultation interface."""
import json
from pathlib import Path
from uuid import uuid4


class BookingStore:
    def __init__(self, path):
        self.path = Path(path)
        self.bookings = []

    def list_bookings(self):
        return list(self.bookings)

    def reserve(self, slot, email, request_id):
        record = dict(id=str(uuid4()), slot=slot, email=email, request_id=request_id)
        self.bookings.append(record)
        self.path.write_text(json.dumps(self.bookings, ensure_ascii=False), encoding='utf-8')
        return record
