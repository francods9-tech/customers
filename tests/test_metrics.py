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

    def test_recurrent_northstar_compares_current_count_with_previous_7_days(self):
        from metrics import recurrent_northstar_delta

        result = recurrent_northstar_delta(
            current_count=12,
            altas_periodo=[{"email": "a@example.com"}, {"email": "b@example.com"}],
            bajas_periodo=[{"email": "c@example.com"}],
        )

        self.assertEqual(result["valor"], 12)
        self.assertEqual(result["previo"], 11)
        self.assertEqual(result["delta"], 9.1)

    def test_trial_events_use_trial_customer_signup_dates(self):
        from metrics import trial_events

        customers = [
            {
                "email": "trial@example.com",
                "email_key": "trial@example.com",
                "estado": "trial",
                "fecha_alta_raw": "2026-05-20T00:00:00+00:00",
                "origen": "instagram",
            },
            {
                "email": "paid@example.com",
                "estado": "activo",
                "fecha_alta_raw": "2026-05-21T00:00:00+00:00",
                "origen": "email",
            },
        ]

        self.assertEqual(
            trial_events(customers),
            [{
                "fecha": "2026-05-20T00:00:00+00:00",
                "email": "trial@example.com",
                "origen": "instagram",
            }],
        )

    def test_dashboard_metrics_group_instagram_variants(self):
        from metrics import filtrar, por_canal

        eventos = [
            {"fecha": "2026-05-20T00:00:00+00:00", "origen": "instagram"},
            {"fecha": "2026-05-21T00:00:00+00:00", "origen": "ig_en"},
            {"fecha": "2026-05-22T00:00:00+00:00", "origen": "ig_es"},
            {"fecha": "2026-05-23T00:00:00+00:00", "origen": "email"},
        ]
        desde = dt.datetime(2026, 5, 1, tzinfo=dt.timezone.utc)
        hasta = dt.datetime(2026, 6, 1, tzinfo=dt.timezone.utc)

        self.assertEqual(len(filtrar(eventos, desde, hasta, canal="instagram")), 3)
        self.assertEqual(por_canal(eventos)["instagram"], 3)


if __name__ == "__main__":
    unittest.main()
