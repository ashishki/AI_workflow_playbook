import unittest
from slugs import slugify

class SlugTests(unittest.TestCase):
    def test_words(self):
        self.assertEqual(slugify('Two Words'), 'two-words')

    def test_lowercase(self):
        self.assertEqual(slugify('HELLO World'), 'hello-world')

    def test_symbol_groups_collapse_to_single_dash(self):
        self.assertEqual(slugify('a---b___c...d'), 'a-b-c-d')

    def test_no_leading_or_trailing_dash(self):
        self.assertEqual(slugify('  Hello, World!  '), 'hello-world')

    def test_empty_string(self):
        self.assertEqual(slugify(''), '')

    def test_whitespace_only(self):
        self.assertEqual(slugify('   \t\n  '), '')

    def test_only_symbols(self):
        self.assertEqual(slugify('!!!---;;;'), '')

if __name__ == '__main__':
    unittest.main()
