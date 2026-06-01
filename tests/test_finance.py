import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class FinanceRulesTest(unittest.TestCase):
    def test_mercury_cash_income_excludes_sky_and_internal_transfers(self):
        from sync.finance import calculate_mercury_cash_income

        accounts = [
            {"id": "traqeer_main", "name": "Traqeer Main"},
            {"id": "traqeer_ops", "name": "Traqeer Ops"},
            {"id": "sky", "name": "Sky Reputation"},
        ]
        transactions = [
            {
                "id": "external",
                "amount": 1200.0,
                "status": "sent",
                "account_id": "traqeer_main",
                "description": "Stripe payout",
            },
            {
                "id": "sky-income",
                "amount": 800.0,
                "status": "sent",
                "account_id": "sky",
                "description": "Sky Reputation client",
            },
            {
                "id": "internal",
                "amount": 500.0,
                "status": "sent",
                "account_id": "traqeer_ops",
                "counterparty_account_id": "traqeer_main",
                "description": "Transfer from Traqeer Main",
            },
            {
                "id": "expense",
                "amount": -200.0,
                "status": "sent",
                "account_id": "traqeer_main",
                "description": "Vendor",
            },
        ]

        result = calculate_mercury_cash_income(transactions, accounts)

        self.assertEqual(result["mercury_cash_income"], 1200.0)
        self.assertEqual([row["id"] for row in result["mercury_income_detail"]], ["external"])
        self.assertEqual(result["excluded"]["sky_reputation"][0]["id"], "sky-income")
        self.assertEqual(result["excluded"]["internal_transfers"][0]["id"], "internal")

    def test_stripe_financials_sum_gross_fees_net_and_payouts(self):
        from sync.finance import calculate_stripe_financials

        balance_transactions = [
            {"type": "charge", "amount": 10000, "fee": 320, "net": 9680},
            {"type": "charge", "amount": 5000, "fee": 175, "net": 4825},
            {"type": "refund", "amount": -1000, "fee": 0, "net": -1000},
        ]
        payouts = [{"amount": 9000}, {"amount": 4000}]

        result = calculate_stripe_financials(balance_transactions, payouts)

        self.assertEqual(result["stripe_gross_income"], 140.0)
        self.assertEqual(result["stripe_fees"], 4.95)
        self.assertEqual(result["stripe_net"], 135.05)
        self.assertEqual(result["stripe_payouts"], 130.0)

    def test_financial_summary_uses_mercury_cash_not_mrr(self):
        from sync.finance import build_financial_summary

        result = build_financial_summary(
            month="2026-05",
            mercury={
                "mercury_cash_income": 1200.0,
                "mercury_income_detail": [{"id": "external"}],
                "source_status": "ok",
            },
            stripe={
                "stripe_gross_income": 1500.0,
                "stripe_fees": 50.0,
                "stripe_net": 1450.0,
                "stripe_payouts": 1190.0,
                "mrr": 9999.0,
                "active_customers": 42,
                "source_status": "ok",
            },
            manual_adjustments=25.0,
            expenses=300.0,
        )

        self.assertEqual(result["totals"]["income"], 1225.0)
        self.assertEqual(result["totals"]["expenses"], 300.0)
        self.assertEqual(result["totals"]["net_result"], 925.0)
        self.assertEqual(result["saas"]["mrr"], 9999.0)
        self.assertEqual(result["saas"]["active_customers"], 42)
        self.assertEqual(result["reconciliation"]["gap"], -10.0)

    def test_financial_summary_marks_cash_missing_without_estimate(self):
        from sync.finance import build_financial_summary

        result = build_financial_summary(
            month="2026-05",
            mercury={"source_status": "missing"},
            stripe={"mrr": 9999.0, "active_customers": 42, "source_status": "ok"},
        )

        self.assertEqual(result["totals"]["income"], 0.0)
        self.assertEqual(result["sources"]["mercury"], "missing")
        self.assertEqual(result["sources"]["income"], "missing")


class FinanceApiTest(unittest.TestCase):
    def setUp(self):
        from app import app

        self.app = app
        self.client = app.test_client()
        with self.client.session_transaction() as sess:
            sess["auth"] = True

    def test_summary_api_returns_reconciliation(self):
        with patch("app.get_financial_summary") as summary:
            summary.return_value = {
                "month": "2026-05",
                "totals": {"income": 1200.0, "expenses": 300.0, "net_result": 900.0},
                "saas": {"mrr": 5000.0, "active_customers": 10},
                "reconciliation": {"stripe_net": 1190.0, "mercury_cash": 1200.0, "gap": -10.0},
                "sources": {"income": "ok"},
            }

            response = self.client.get("/api/summary?month=2026-05")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["totals"]["income"], 1200.0)
        self.assertIn("reconciliation", response.json)

    def test_refresh_api_does_not_create_monthly_snapshot(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self.app.config["FINANCE_DATA_DIR"] = tmpdir
            with patch("app.refresh_financial_summary") as refresh:
                refresh.return_value = {"month": "2026-05", "totals": {"income": 1200.0}}

                response = self.client.post("/api/refresh", json={"month": "2026-05"})

            self.assertEqual(response.status_code, 200)
            self.assertEqual(list(Path(tmpdir).glob("income_*.json")), [])

    def test_snapshot_api_persists_reconciled_month(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self.app.config["FINANCE_DATA_DIR"] = tmpdir
            with patch("app.get_financial_summary") as summary:
                summary.return_value = {
                    "month": "2026-05",
                    "totals": {"income": 1200.0, "expenses": 300.0, "net_result": 900.0},
                    "saas": {"mrr": 5000.0, "active_customers": 10},
                    "reconciliation": {"gap": -10.0},
                    "sources": {"income": "ok"},
                }

                response = self.client.post("/api/snapshot", json={"month": "2026-05"})

            self.assertEqual(response.status_code, 200)
            persisted = Path(tmpdir) / "income_2026-05.json"
            self.assertTrue(persisted.exists())
            self.assertEqual(response.json["snapshot"], str(persisted))

    def test_snapshot_api_persists_last_refresh_without_extra_sync(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self.app.config["FINANCE_DATA_DIR"] = tmpdir
            refreshed = {
                "month": "2026-05",
                "totals": {"income": 1300.0, "expenses": 300.0, "net_result": 1000.0},
                "saas": {"mrr": 5000.0, "active_customers": 10},
                "reconciliation": {"gap": 0.0},
                "sources": {"income": "ok"},
            }
            with patch("app.refresh_financial_summary") as refresh:
                refresh.return_value = refreshed
                self.client.post("/api/refresh", json={"month": "2026-05"})

            response = self.client.post("/api/snapshot", json={"month": "2026-05"})

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json["summary"]["totals"]["income"], 1300.0)


if __name__ == "__main__":
    unittest.main()
