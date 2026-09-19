import tempfile
import unittest
from pathlib import Path
from booking import BookingStore


class BookingTests(unittest.TestCase):
    def test_first_reservation(self):
        with tempfile.TemporaryDirectory() as directory:
            store = BookingStore(Path(directory) / 'bookings.json')
            result = store.reserve('2026-10-05T10:00', 'reader@example.test', 'request-1')
            self.assertEqual(result['email'], 'reader@example.test')
            self.assertEqual(len(store.list_bookings()), 1)


if __name__ == '__main__':
    unittest.main()
