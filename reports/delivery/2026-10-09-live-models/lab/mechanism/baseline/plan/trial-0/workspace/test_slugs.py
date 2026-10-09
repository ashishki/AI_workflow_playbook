import unittest
from slugs import slugify

class SlugTests(unittest.TestCase):
    def test_words(self):
        self.assertEqual(slugify('Two Words'), 'two-words')

if __name__ == '__main__':
    unittest.main()
