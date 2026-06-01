import unittest
import datetime as dt


class CustomerRulesTest(unittest.TestCase):
    def test_origin_options_include_xbiz(self):
        from db.models import ORIGEN_LABELS

        self.assertEqual(ORIGEN_LABELS["xbiz"], "XBIZ")

    def test_manual_plan_one_time_is_not_recurrent_active(self):
        from customer_rules import enrich_customer

        customer = {
            "nombre": "Ana",
            "email": "ana@example.com",
            "email_key": "ana@example.com",
            "plan": "Premium",
            "estado": "activo",
        }
        meta = type("Meta", (), {
            "origen": "email",
            "onboarding_hecho": True,
            "manual_plan": "one_time",
            "manual_estado": "",
            "tipo_cliente": "",
        })()

        enriched = enrich_customer(customer, meta)

        self.assertEqual(enriched["plan"], "One time payment")
        self.assertEqual(enriched["tipo_cliente"], "One time payment")
        self.assertFalse(enriched["cuenta_activo_recurrente"])

    def test_manual_inactive_overrides_status(self):
        from customer_rules import enrich_customer

        customer = {
            "nombre": "Bruno",
            "email": "bruno@example.com",
            "email_key": "bruno@example.com",
            "plan": "Starter",
            "estado": "activo",
        }
        meta = type("Meta", (), {
            "origen": "referido",
            "onboarding_hecho": False,
            "manual_plan": "",
            "manual_estado": "inactivo",
            "tipo_cliente": "",
        })()

        enriched = enrich_customer(customer, meta)

        self.assertEqual(enriched["estado"], "inactivo")
        self.assertFalse(enriched["cuenta_activo_recurrente"])

    def test_search_matches_name_and_email(self):
        from customer_rules import filter_customers

        customers = [
            {"nombre": "Agencia Norte", "email": "ops@norte.com", "estado": "activo", "origen": "email"},
            {"nombre": "Mia", "email": "mia@example.com", "estado": "trial", "origen": "referido"},
        ]

        self.assertEqual(len(filter_customers(customers, q="norte")), 1)
        self.assertEqual(len(filter_customers(customers, q="example")), 1)
        self.assertEqual(len(filter_customers(customers, q="zzz")), 0)

    def test_filter_can_select_one_time_type(self):
        from customer_rules import filter_customers

        customers = [
            {"nombre": "Ana", "email": "ana@example.com", "estado": "activo", "origen": "email", "tipo_cliente_key": "one_time"},
            {"nombre": "Mia", "email": "mia@example.com", "estado": "activo", "origen": "email", "tipo_cliente_key": "individual"},
        ]

        filtered = filter_customers(customers, tipo="one_time")

        self.assertEqual([c["nombre"] for c in filtered], ["Ana"])

    def test_discount_colab_counts_as_recurrent_active(self):
        from customer_rules import enrich_customer

        customer = {
            "nombre": "Agencia Colab",
            "email": "colab@example.com",
            "email_key": "colab@example.com",
            "plan": "Premium",
            "estado": "activo",
        }
        meta = type("Meta", (), {
            "origen": "email",
            "onboarding_hecho": True,
            "manual_plan": "",
            "manual_estado": "",
            "tipo_cliente": "colab_descuento",
        })()

        enriched = enrich_customer(customer, meta)

        self.assertEqual(enriched["tipo_cliente"], "Colab con descuento")
        self.assertTrue(enriched["cuenta_activo_recurrente"])

    def test_colab_summary_marks_due_reviews(self):
        from customer_rules import colab_summary

        meta = type("Meta", (), {
            "tipo_cliente": "colab_descuento",
            "colab_revision": "2026-05-20",
            "colab_acuerdo": "Post mensual",
            "colab_descuento": "50%",
        })()

        summary = colab_summary(meta, today=dt.date(2026, 5, 27))

        self.assertTrue(summary["es_colab"])
        self.assertTrue(summary["revision_pendiente"])
        self.assertEqual(summary["dias_revision"], 7)

    def test_filter_recurrent_active_excludes_one_time(self):
        from customer_rules import filter_customers

        customers = [
            {"nombre": "Ana", "estado": "activo", "cuenta_activo_recurrente": False},
            {"nombre": "Mia", "estado": "activo", "cuenta_activo_recurrente": True},
            {"nombre": "Leo", "estado": "trial", "cuenta_activo_recurrente": False},
        ]

        filtered = filter_customers(customers, recurrente=True)

        self.assertEqual([c["nombre"] for c in filtered], ["Mia"])

    def test_unpaid_summary_uses_invoice_date_and_link(self):
        from customer_rules import unpaid_summary

        customer = {
            "ultima_factura_fecha_raw": "2026-05-10T00:00:00+00:00",
            "ultima_factura_url": "https://stripe.test/inv_123",
            "impago_monto_pendiente": 129.5,
        }
        today = dt.datetime(2026, 5, 27, tzinfo=dt.timezone.utc)

        summary = unpaid_summary(customer, today=today)

        self.assertEqual(summary["dias"], 17)
        self.assertEqual(summary["label"], "17 dias")
        self.assertEqual(summary["factura_url"], "https://stripe.test/inv_123")
        self.assertEqual(summary["monto"], 129.5)

    def test_unpaid_summary_uses_multiple_pending_invoices(self):
        from customer_rules import unpaid_summary

        customer = {
            "facturas_pendientes": [
                {
                    "fecha_raw": "2026-05-20T00:00:00+00:00",
                    "url": "https://stripe.test/inv_recent",
                    "monto_pendiente": 50.0,
                },
                {
                    "fecha_raw": "2026-04-20T00:00:00+00:00",
                    "url": "https://stripe.test/inv_old",
                    "monto_pendiente": 99.0,
                },
            ],
        }
        today = dt.datetime(2026, 6, 1, tzinfo=dt.timezone.utc)

        summary = unpaid_summary(customer, today=today)

        self.assertEqual(summary["dias"], 42)
        self.assertEqual(summary["label"], "42 dias")
        self.assertEqual(summary["facturas_count"], 2)
        self.assertEqual(summary["monto"], 149.0)
        self.assertEqual(summary["factura_url"], "https://stripe.test/inv_old")
        self.assertEqual(
            [invoice["url"] for invoice in summary["facturas"]],
            ["https://stripe.test/inv_old", "https://stripe.test/inv_recent"],
        )

    def test_unpaid_operational_status_segments_recoverable_customers(self):
        from customer_rules import unpaid_operational_status

        self.assertEqual(unpaid_operational_status(29)["estado"], "impago")
        self.assertEqual(unpaid_operational_status(30)["estado"], "pausado_impago")
        self.assertEqual(unpaid_operational_status(89)["estado"], "pausado_impago")
        self.assertEqual(unpaid_operational_status(90)["estado"], "inactivo_impago")

    def test_unpaid_summary_handles_missing_invoice(self):
        from customer_rules import unpaid_summary

        summary = unpaid_summary({}, today=dt.datetime(2026, 5, 27, tzinfo=dt.timezone.utc))

        self.assertIsNone(summary["dias"])
        self.assertEqual(summary["label"], "sin fecha")
        self.assertEqual(summary["factura_url"], "")

    def test_sort_unpaid_priority_puts_oldest_debt_first(self):
        from customer_rules import sort_unpaid_priority

        rows = [
            {"nombre": "A", "impago": {"dias": 2}},
            {"nombre": "B", "impago": {"dias": 15}},
            {"nombre": "C", "impago": {"dias": None}},
        ]

        sorted_rows = sort_unpaid_priority(rows)

        self.assertEqual([r["nombre"] for r in sorted_rows], ["B", "A", "C"])

    def test_sort_oldest_first_handles_timezone_naive_dates(self):
        from customer_rules import sort_oldest_first

        rows = [
            type("Item", (), {"created_at": dt.datetime(2026, 5, 20, 12, 0)})(),
            type("Item", (), {"created_at": dt.datetime(2026, 5, 10, 12, 0)})(),
        ]

        sorted_rows = sort_oldest_first(rows)

        self.assertEqual(sorted_rows[0].created_at.day, 10)

    def test_trial_summary_uses_explicit_end_or_start_plus_seven_days(self):
        from customer_rules import trial_summary

        explicit = trial_summary(
            {"trial_fin_raw": "2026-05-30T00:00:00+00:00"},
            today=dt.date(2026, 5, 27),
        )
        inferred = trial_summary(
            {"fecha_alta_raw": "2026-05-21T07:15:29+00:00"},
            today=dt.date(2026, 5, 27),
        )

        self.assertEqual(explicit["fecha"], "30/05/2026")
        self.assertEqual(explicit["dias"], 3)
        self.assertEqual(inferred["fecha"], "28/05/2026")
        self.assertEqual(inferred["dias"], 1)
        self.assertTrue(inferred["por_vencer"])

    def test_reactivation_summary_detects_active_customer_with_cancel_event(self):
        from customer_rules import reactivation_summary

        summary = reactivation_summary(
            {"email_key": "ana@example.com", "estado": "activo"},
            [{"email": "ana@example.com", "fecha": "2026-05-10T00:00:00+00:00"}],
        )

        self.assertTrue(summary["reactivado"])
        self.assertEqual(summary["ultima_baja"], "10/05/2026")

    def test_remove_reactivated_cancellations_filters_active_customers(self):
        from customer_rules import remove_reactivated_cancellations

        bajas = [
            {"email": "ana@example.com", "fecha": "2026-05-10T00:00:00+00:00"},
            {"email": "bruno@example.com", "fecha": "2026-05-11T00:00:00+00:00"},
        ]
        clientes = [
            {"email_key": "ana@example.com", "estado": "activo"},
            {"email_key": "bruno@example.com", "estado": "inactivo"},
        ]

        filtered = remove_reactivated_cancellations(bajas, clientes)

        self.assertEqual([b["email"] for b in filtered], ["bruno@example.com"])


if __name__ == "__main__":
    unittest.main()
