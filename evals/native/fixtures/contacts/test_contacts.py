import tempfile
import unittest
from pathlib import Path
from export_contacts import export_csv


class ContactTests(unittest.TestCase):
    def test_export_count(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'out.csv'
            self.assertEqual(export_csv('contacts.json', output), 1)
            self.assertIn('reader@example.test', output.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
