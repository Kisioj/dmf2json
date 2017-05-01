import unittest
import dmf2json


class TestDMFParser(unittest.TestCase):
    def setUp(self):
        self.parser = dmf2json.DMFParser()

    def test__parse_key_value(self):
        self.assertEqual(
            self.parser._parse_key_value('eyes "blue"'),
            ('eyes', 'blue')
        )
        self.assertEqual(
            self.parser._parse_key_value('mouth'),
            ('mouth', None)
        )
        self.assertEqual(
            self.parser._parse_key_value(''),
            ('', None)
        )
        self.assertEqual(
            self.parser._parse_key_value('hair black'),
            ('hair', 'black')
        )

    def test__parse_key_eq_sign_value(self):
        self.assertEqual(
            self.parser._parse_key_eq_sign_value('eyes = "blue"'),
            ('eyes', 'blue')
        )
        self.assertRaises(
            ValueError,
            self.parser._parse_key_eq_sign_value,
            'mouth',
        )
        self.assertEqual(
            self.parser._parse_key_eq_sign_value('hair = black'),
            ('hair', 'black')
        )


if __name__ == '__main__':
    unittest.main()
