import unittest

from amr_changing_world.mic import parse_mic


class TestMICParsing(unittest.TestCase):
    def test_exact(self):
        result = parse_mic("0.25")
        self.assertEqual((result.lower, result.upper, result.censoring), (0.25, 0.25, "exact"))

    def test_left_censored(self):
        result = parse_mic("<=0.06")
        self.assertEqual((result.lower, result.upper, result.censoring), (None, 0.06, "left"))

    def test_right_censored(self):
        result = parse_mic(">8")
        self.assertEqual((result.lower, result.upper, result.censoring), (8.0, None, "right"))

    def test_invalid_is_retained(self):
        result = parse_mic("not-a-mic")
        self.assertFalse(result.parsed)
        self.assertEqual(result.raw, "not-a-mic")


if __name__ == "__main__":
    unittest.main()

