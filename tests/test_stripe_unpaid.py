import unittest


class StripeUnpaidMergeTest(unittest.TestCase):
    def test_merge_unpaid_details_updates_matching_customer(self):
        from sync.stripe_unpaid import merge_unpaid_details

        payload = {
            "clientes": [
                {"email_key": "ana@example.com", "estado": "activo"},
                {"email_key": "mia@example.com", "estado": "activo"},
            ]
        }
        unpaid = {
            "ana@example.com": {
                "ultima_factura_url": "https://stripe.test/inv",
                "ultima_factura_fecha_raw": "2026-05-10T00:00:00+00:00",
                "impago_monto_pendiente": 99.0,
            }
        }

        result = merge_unpaid_details(payload, unpaid)

        self.assertEqual(result["matched"], 1)
        self.assertEqual(result["with_invoice_link"], 1)
        self.assertEqual(payload["clientes"][0]["estado"], "impago")
        self.assertEqual(payload["clientes"][0]["ultima_factura_url"], "https://stripe.test/inv")
        self.assertEqual(payload["clientes"][1]["estado"], "activo")

    def test_merge_unpaid_details_stores_multiple_pending_invoices(self):
        from sync.stripe_unpaid import merge_unpaid_details

        payload = {"clientes": [{"email_key": "ana@example.com", "estado": "activo"}]}
        unpaid = {
            "ana@example.com": {
                "facturas_pendientes": [
                    {
                        "id": "in_recent",
                        "fecha_raw": "2026-05-20T00:00:00+00:00",
                        "url": "https://stripe.test/recent",
                        "monto_pendiente": 50.0,
                    },
                    {
                        "id": "in_old",
                        "fecha_raw": "2026-04-20T00:00:00+00:00",
                        "url": "https://stripe.test/old",
                        "monto_pendiente": 99.0,
                    },
                ],
                "ultima_factura_url": "https://stripe.test/recent",
            }
        }

        result = merge_unpaid_details(payload, unpaid)

        customer = payload["clientes"][0]
        self.assertEqual(result["matched"], 1)
        self.assertEqual(customer["estado"], "impago")
        self.assertEqual(len(customer["facturas_pendientes"]), 2)
        self.assertEqual(customer["impago_monto_pendiente"], 149.0)
        self.assertEqual(customer["ultima_factura_url"], "https://stripe.test/old")
        self.assertEqual(customer["ultima_factura_fecha_raw"], "2026-04-20T00:00:00+00:00")

    def test_merge_unpaid_details_ignores_unknown_email(self):
        from sync.stripe_unpaid import merge_unpaid_details

        payload = {"clientes": [{"email_key": "ana@example.com", "estado": "activo"}]}
        unpaid = {"unknown@example.com": {"ultima_factura_url": "https://stripe.test/inv"}}

        result = merge_unpaid_details(payload, unpaid)

        self.assertEqual(result["matched"], 0)
        self.assertEqual(payload["clientes"][0]["estado"], "activo")


if __name__ == "__main__":
    unittest.main()
