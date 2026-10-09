import unittest
from slugs import slugify

class SlugTests(unittest.TestCase):
    def test_words(self):
        self.assertEqual(slugify('Two Words'), 'two-words')

    def test_lowercase(self):
        self.assertEqual(slugify('Hello'), 'hello')

    def test_groups_replaced_by_single_dash(self):
        self.assertEqual(slugify('a...b   c!!!d'), 'a-b-c-d')

    def test_no_leading_or_trailing_dashes(self):
        self.assertEqual(slugify('  Hello, World!  '), 'hello-world')
        self.assertEqual(slugify('---Hello---'), 'hello')

    def test_empty_and_whitespace(self):
        self.assertEqual(slugify(''), '')
        self.assertEqual(slugify('   '), '')

    def test_only_symbols(self):
        self.assertEqual(slugify('!!!???'), '')

    def test_already_slug(self):
        self.assertEqual(slugify('abc-123'), 'abc-123')

if __name__ == '__main__':
    unittest.main()
