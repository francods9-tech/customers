import os
import unittest


class FakeCollection:
    def __init__(self, rows=None, aggregate_result=None):
        self.rows = rows or []
        self.aggregate_result = aggregate_result

    def aggregate(self, pipeline):
        if self.aggregate_result is not None:
            return self.aggregate_result
        match = pipeline[0].get("$match", {})
        account_ids = set(match.get("accountId", {}).get("$in", []))
        status_counts = {"pending": 0, "removed": 0, "deindexed": 0}
        reports = []
        for row in self.rows:
            if row.get("accountId") not in account_ids or row.get("deleted") is True:
                continue
            status = row.get("status")
            if status in status_counts:
                status_counts[status] += 1
            metadata = row.get("metadata") or {}
            role = metadata.get("reportedByRole")
            if role in ("cliente", "customer", "usuario", "user"):
                reports.append(row)
        last_report = ""
        repeated = 0
        for row in reports:
            metadata = row.get("metadata") or {}
            reported_at = metadata.get("reportedAt") or metadata.get("reported_at") or row.get("createdAt") or ""
            last_report = max(last_report, str(reported_at))
            repeated += 1 if metadata.get("repeated") or metadata.get("duplicate") else 0
        return [{
            "_id": None,
            "pendientes": status_counts["pending"],
            "gestionados": status_counts["removed"] + status_counts["deindexed"],
            "manual_reports_count": len(reports),
            "last_reported_at": last_report,
            "repeated_reports": repeated,
        }]

    def count_documents(self, query):
        account_ids = set(query.get("accountId", {}).get("$in", []))
        status = query.get("status")
        statuses = set(status.get("$in", [])) if isinstance(status, dict) else {status}
        return sum(
            1 for row in self.rows
            if row.get("accountId") in account_ids and row.get("status") in statuses
        )


class FakeDb:
    def __init__(self):
        self.account_health_checks = FakeCollection(aggregate_result=[])
        self.detected_items = FakeCollection(rows=[
            {
                "accountId": "acc-1",
                "status": "pending",
                "metadata": {
                    "reportedByRole": "customer",
                    "reportedAt": "2026-06-01",
                    "url": "https://pirata.example.test/uno",
                },
            },
            {
                "accountId": "acc-1",
                "status": "removed",
                "metadata": {
                    "reportedByRole": "usuario",
                    "reportedAt": "2026-06-03",
                    "repeated": True,
                    "url": "https://pirata.example.test/dos",
                },
            },
            {
                "accountId": "acc-1",
                "status": "removed",
                "metadata": {"reportedByRole": "admin", "reportedAt": "2026-06-04"},
            },
        ])
        self.impersonations = FakeCollection(rows=[
            {"accountId": "acc-1", "status": "pending"},
            {"accountId": "acc-1", "status": "reported"},
            {"accountId": "acc-1", "status": "removed"},
        ])


class HealthTest(unittest.TestCase):
    def test_salud_cuenta_incluye_suplantaciones_gestionadas_y_reportes_manual(self):
        import sync.health as health

        original_db = health._db
        original_env = os.environ.get("MONGO_URI")
        os.environ["MONGO_URI"] = "mongodb://example.test"
        health._db = lambda: FakeDb()
        try:
            result = health.salud_de_cuentas(["acc-1"])
        finally:
            health._db = original_db
            if original_env is None:
                os.environ.pop("MONGO_URI", None)
            else:
                os.environ["MONGO_URI"] = original_env

        self.assertEqual(result["detected_pendientes"], 1)
        self.assertEqual(result["detected_gestionados"], 2)
        self.assertEqual(result["impersonations_pendientes"], 1)
        self.assertEqual(result["impersonations_gestionadas"], 2)
        self.assertEqual(result["manual_reports"]["count"], 2)
        self.assertEqual(result["manual_reports"]["last_reported_at"], "2026-06-03")
        self.assertEqual(result["manual_reports"]["repeated_count"], 1)
        self.assertNotIn("url", result["manual_reports"])


if __name__ == "__main__":
    unittest.main()
