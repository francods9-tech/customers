import datetime as dt
import unittest


class MetricsTest(unittest.TestCase):
    def test_todo_period_starts_at_first_event(self):
        from metrics import resolver_periodo

        args = {"preset": "todo"}
        eventos = [
            {"fecha": "2026-03-10T00:00:00+00:00"},
            {"fecha": "2026-05-10T00:00:00+00:00"},
        ]

        desde, hasta, label, _, _ = resolver_periodo(args, eventos=eventos)

        self.assertEqual(label, "Todo")
        self.assertEqual(desde.date(), dt.date(2026, 3, 10))
        self.assertGreater(hasta, desde)


if __name__ == "__main__":
    unittest.main()
