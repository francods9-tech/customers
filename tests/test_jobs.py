import io
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
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

    def test_build_snapshot_includes_canceled_subscription_with_future_period_end_as_churn_risk(self):
        import datetime as dt

        from sync import snapshot

        now = dt.datetime(2026, 6, 5, tzinfo=dt.timezone.utc)
        period_end = int(dt.datetime(2026, 6, 20, tzinfo=dt.timezone.utc).timestamp())
        canceled_at = int(now.timestamp())

        class FakeList:
            def __init__(self, rows):
                self.data = rows
                self._rows = rows

            def auto_paging_iter(self):
                return iter(self._rows)

            def __iter__(self):
                return iter(self._rows)

        class FakeCollection:
            def find(self, *args, **kwargs):
                return []

            def aggregate(self, *args, **kwargs):
                return []

        class FakeMongo:
            def __init__(self, *args, **kwargs):
                self._db = SimpleNamespace(
                    users=FakeCollection(),
                    accounts=FakeCollection(),
                    subscriptions=FakeCollection(),
                )

            def __getitem__(self, name):
                return self._db

        class FakeSubscription:
            customer = "cus_cancel_period_end"

            def __getitem__(self, key):
                if key == "items":
                    return {"data": [{"price": {"recurring": {"interval": "month"}}}]}
                raise KeyError(key)

            def to_dict(self):
                return {
                    "customer": self.customer,
                    "status": "canceled",
                    "cancel_at_period_end": True,
                    "current_period_end": period_end,
                    "canceled_at": canceled_at,
                }

        def subscription_list(status, *args, **kwargs):
            if status == "canceled":
                return FakeList([FakeSubscription()])
            return FakeList([])

        def invoice_list(*args, **kwargs):
            if kwargs.get("customer") == "cus_cancel_period_end" and kwargs.get("status") == "paid":
                return FakeList([SimpleNamespace(amount_paid=9900, created=canceled_at)])
            return FakeList([])

        def customer_retrieve(customer_id):
            self.assertEqual(customer_id, "cus_cancel_period_end")
            return SimpleNamespace(email="cancel-futuro@example.test", name="Cancel Futuro")

        with patch.dict("os.environ", {"MONGO_URI": "mongodb://example", "STRIPE_SECRET_KEY": "sk_test"}):
            with patch.object(snapshot, "MongoClient", FakeMongo):
                with patch.object(snapshot, "NOW", return_value=now):
                    with patch.object(snapshot.stripe.Subscription, "list", side_effect=subscription_list):
                        with patch.object(snapshot.stripe.Invoice, "list", side_effect=invoice_list):
                            with patch.object(snapshot.stripe.Customer, "retrieve", side_effect=customer_retrieve):
                                payload = snapshot.build_snapshot()

        customer = next(c for c in payload["clientes"] if c["email_key"] == "cancel-futuro@example.test")
        self.assertEqual(customer["estado"], "activo")
        self.assertTrue(customer.get("cancelacion_programada"))
        self.assertEqual(customer["cancelacion_fecha"], "20/06/2026")
        self.assertEqual(payload["resumen"]["activos"], 1)

    def test_build_snapshot_marks_past_due_period_end_cancellation_as_churn_risk(self):
        import datetime as dt

        from sync import snapshot

        now = dt.datetime(2026, 6, 5, tzinfo=dt.timezone.utc)
        period_end = int(dt.datetime(2026, 6, 20, tzinfo=dt.timezone.utc).timestamp())
        invoice_created = int(dt.datetime(2026, 6, 3, tzinfo=dt.timezone.utc).timestamp())

        class FakeList:
            def __init__(self, rows):
                self.data = rows
                self._rows = rows

            def auto_paging_iter(self):
                return iter(self._rows)

            def __iter__(self):
                return iter(self._rows)

        class FakeCollection:
            def find(self, *args, **kwargs):
                return []

            def aggregate(self, *args, **kwargs):
                return []

        class FakeMongo:
            def __init__(self, *args, **kwargs):
                self._db = SimpleNamespace(
                    users=FakeCollection(),
                    accounts=FakeCollection(),
                    subscriptions=FakeCollection(),
                )

            def __getitem__(self, name):
                return self._db

        class FakeSubscription:
            customer = "cus_past_due_cancel"
            latest_invoice = SimpleNamespace(
                id="inv_past_due",
                amount_due=9900,
                amount_paid=0,
                created=invoice_created,
                hosted_invoice_url="https://stripe.test/inv_past_due",
                status="open",
            )

            def __getitem__(self, key):
                if key == "items":
                    return {"data": [{"price": {"recurring": {"interval": "month"}}}]}
                raise KeyError(key)

            def to_dict(self):
                return {
                    "customer": self.customer,
                    "status": "past_due",
                    "cancel_at_period_end": True,
                    "current_period_end": period_end,
                }

        def subscription_list(status, *args, **kwargs):
            if status == "past_due":
                return FakeList([FakeSubscription()])
            return FakeList([])

        def invoice_list(*args, **kwargs):
            return FakeList([])

        def customer_retrieve(customer_id):
            self.assertEqual(customer_id, "cus_past_due_cancel")
            return SimpleNamespace(email="past-due-cancel@example.test", name="Past Due Cancel")

        with patch.dict("os.environ", {"MONGO_URI": "mongodb://example", "STRIPE_SECRET_KEY": "sk_test"}):
            with patch.object(snapshot, "MongoClient", FakeMongo):
                with patch.object(snapshot, "NOW", return_value=now):
                    with patch.object(snapshot.stripe.Subscription, "list", side_effect=subscription_list):
                        with patch.object(snapshot.stripe.Invoice, "list", side_effect=invoice_list):
                            with patch.object(snapshot.stripe.Customer, "retrieve", side_effect=customer_retrieve):
                                payload = snapshot.build_snapshot()

        customer = next(c for c in payload["clientes"] if c["email_key"] == "past-due-cancel@example.test")
        self.assertEqual(customer["estado"], "impago")
        self.assertTrue(customer.get("cancelacion_programada"))
        self.assertEqual(customer["cancelacion_fecha"], "20/06/2026")
        self.assertEqual(payload["resumen"]["impago"], 1)

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
