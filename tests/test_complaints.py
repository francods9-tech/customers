import datetime as dt
import unittest


class ComplaintRulesTest(unittest.TestCase):
    def test_category_stats_counts_open_and_resolved(self):
        from complaint_rules import complaint_stats

        rows = [
            type("Q", (), {"categoria": "encuentra_links", "resuelta": False, "created_at": dt.datetime(2026, 5, 20)})(),
            type("Q", (), {"categoria": "encuentra_links", "resuelta": True, "created_at": dt.datetime(2026, 5, 21)})(),
            type("Q", (), {"categoria": "tiempos_gestion", "resuelta": False, "created_at": dt.datetime(2026, 5, 22)})(),
        ]

        stats = complaint_stats(rows, today=dt.datetime(2026, 5, 27, tzinfo=dt.timezone.utc))

        self.assertEqual(stats["total_abiertas"], 2)
        self.assertEqual(stats["total_resueltas"], 1)
        self.assertEqual(stats["por_categoria"]["encuentra_links"]["abiertas"], 1)
        self.assertEqual(stats["por_categoria"]["encuentra_links"]["resueltas"], 1)
        self.assertEqual(stats["max_dias_abierta"], 7)

    def test_category_label_uses_editable_category_names(self):
        from complaint_rules import category_label

        categories = {
            "envia_links": "Envia links",
            "tiempos_gestion": "Tiempos de gestion",
        }

        self.assertEqual(category_label("envia_links", categories), "Envia links")
        self.assertEqual(category_label("", categories), "Sin categoria")
        self.assertEqual(category_label("otra", categories), "otra")

    def test_category_key_normalizes_editable_labels(self):
        from complaint_rules import category_key

        self.assertEqual(category_key("Tiempos de gestion"), "tiempos_de_gestion")
        self.assertEqual(category_key("  Envia   links  "), "envia_links")

    def test_customer_request_stats_include_complaints_and_requests_by_team(self):
        from complaint_rules import request_stats

        rows = [
            type("Q", (), {"tipo": "queja", "equipo": "cs", "estado_gestion": "abierta", "resuelta": False})(),
            type("Q", (), {"tipo": "solicitud", "equipo": "ops", "estado_gestion": "en_gestion", "resuelta": False})(),
            type("Q", (), {"tipo": "nota", "equipo": "", "estado_gestion": "", "resuelta": False})(),
            type("Q", (), {"tipo": "queja", "equipo": "ops", "estado_gestion": "resuelta", "resuelta": True})(),
        ]

        stats = request_stats(rows)

        self.assertEqual(stats["total_abiertas"], 2)
        self.assertEqual(stats["total_resueltas"], 1)
        self.assertEqual(stats["por_equipo"]["cs"], 1)
        self.assertEqual(stats["por_equipo"]["ops"], 1)
        self.assertEqual(stats["por_estado"]["en_gestion"], 1)


if __name__ == "__main__":
    unittest.main()
