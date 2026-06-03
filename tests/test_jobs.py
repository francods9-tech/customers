import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch


class JobsTest(unittest.TestCase):
    def test_refresh_job_runs_snapshot_refresh_inside_app_context(self):
        from sync import refresh_job

        payload = {
            "clientes": [{"estado": "activo"}, {"estado": "trial"}, {"estado": "impago"}],
            "resumen": {"activos": 1, "trial": 1, "impago": 1},
        }
        out = io.StringIO()

        with patch.object(refresh_job, "refrescar_snapshot", return_value=payload) as refresh:
            with redirect_stdout(out):
                code = refresh_job.main()

        self.assertEqual(code, 0)
        self.assertEqual(refresh.call_count, 1)
        self.assertIn("refresh ok", out.getvalue())
        self.assertIn("activos=1", out.getvalue())

    def test_refrescar_snapshot_marks_active_customer_with_rejected_invoice_as_unpaid(self):
        import sync

        payload = {
            "clientes": [
                {
                    "nombre": "Claudia Balt",
                    "email": "claudia@example.test",
                    "email_key": "claudia@example.test",
                    "estado": "activo",
                    "plan": "Starter",
                }
            ],
            "resumen": {"activos": 1, "trial": 0, "impago": 0},
        }
        unpaid = {
            "claudia@example.test": {
                "facturas_pendientes": [
                    {
                        "fecha_raw": "2026-06-02T00:00:00+00:00",
                        "url": "https://stripe.test/inv",
                        "monto_pendiente": 99.0,
                        "estado": "open",
                    }
                ]
            }
        }

        with patch.object(sync, "build_snapshot", return_value=payload):
            with patch("sync.stripe_unpaid.collect_unpaid_from_stripe", return_value=unpaid):
                with patch.object(sync.db.session, "add") as add:
                    with patch.object(sync.db.session, "commit"):
                        result = sync.refrescar_snapshot()

        customer = result["clientes"][0]
        self.assertEqual(customer["estado"], "impago")
        self.assertEqual(customer["ultima_factura_url"], "https://stripe.test/inv")
        self.assertEqual(result["resumen"]["activos"], 0)
        self.assertEqual(result["resumen"]["impago"], 1)
        add.assert_called_once()

    def test_active_recurrent_diff_reports_removed_customer(self):
        from scripts.active_recurrent_diff import diff_recurrent_customers

        before = {
            "clientes": [
                {"email_key": "ana@example.test", "nombre": "Ana", "estado": "activo", "plan": "Premium"},
                {"email_key": "bruno@example.test", "nombre": "Bruno", "estado": "activo", "plan": "Premium"},
                {"email_key": "carla@example.test", "nombre": "Carla", "estado": "activo", "plan": "Premium"},
            ]
        }
        after = {
            "clientes": [
                {"email_key": "ana@example.test", "nombre": "Ana", "estado": "activo", "plan": "Premium"},
                {"email_key": "bruno@example.test", "nombre": "Bruno", "estado": "impago", "plan": "Premium"},
                {"email_key": "carla@example.test", "nombre": "Carla", "estado": "inactivo", "plan": "Premium"},
            ]
        }

        diff = diff_recurrent_customers(before, after)

        self.assertEqual(diff["before_count"], 3)
        self.assertEqual(diff["after_count"], 2)
        self.assertEqual(diff["delta"], -1)
        self.assertEqual(diff["removed"][0]["email"], "carla@example.test")
        self.assertEqual(diff["removed"][0]["after_estado"], "inactivo")

    def test_active_recurrent_diff_ignores_test_snapshots(self):
        from scripts.active_recurrent_diff import latest_real_payloads

        rows = [
            type("Snapshot", (), {"payload": {"test_marker": "solicitudes_directas", "clientes": []}})(),
            type("Snapshot", (), {"payload": {"generado": "after", "clientes": [{"email_key": "after@example.test"}]}})(),
            type("Snapshot", (), {"payload": {"test_marker": "routes", "clientes": []}})(),
            type("Snapshot", (), {"payload": {"generado": "before", "clientes": [{"email_key": "before@example.test"}]}})(),
        ]

        payloads = latest_real_payloads(rows, count=2)

        self.assertEqual([p["generado"] for p in payloads], ["after", "before"])


if __name__ == "__main__":
    unittest.main()
