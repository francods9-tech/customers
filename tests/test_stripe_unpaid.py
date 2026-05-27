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

    def test_merge_unpaid_details_ignores_unknown_email(self):
        from sync.stripe_unpaid import merge_unpaid_details

        payload = {"clientes": [{"email_key": "ana@example.com", "estado": "activo"}]}
        unpaid = {"unknown@example.com": {"ultima_factura_url": "https://stripe.test/inv"}}

        result = merge_unpaid_details(payload, unpaid)

        self.assertEqual(result["matched"], 0)
        self.assertEqual(payload["clientes"][0]["estado"], "activo")


if __name__ == "__main__":
    unittest.main()
