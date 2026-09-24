import datetime as dt
import unittest
from contextlib import contextmanager
from unittest.mock import patch

from sync import count_snapshots

TEST_DOMAIN = "@count-snapshots.test"
TEST_MARKER = "count_snapshots_test"
TEST_TOKEN = "count-snapshots-token"
FIRST_DAY = "2000-01-03"
SECOND_DAY = "2000-01-04"


def customer_row(email, plan="Premium", estado="activo"):
    return {
        "nombre": email.split("@")[0],
        "email": email,
        "email_key": email,
        "plan": plan,
        "estado": estado,
        "anual": False,
        "fecha_alta": "01/12/1999",
        "fecha_alta_raw": "1999-12-01T00:00:00+00:00",
        "dias_de_alta": 30,
        "account_ids": [],
    }


class CountSummaryTest(unittest.TestCase):
    def test_summarize_counts_groups_recurrent_actives_by_plan(self):
        from sync.count_snapshots import summarize_counts

        customers = [
            {"estado": "activo", "plan": "Premium", "cuenta_activo_recurrente": True},
            {"estado": "activo", "plan": "Premium", "cuenta_activo_recurrente": True},
            {"estado": "activo", "plan": "", "cuenta_activo_recurrente": True},
            {"estado": "trial", "plan": "Starter", "cuenta_activo_recurrente": False},
            {"estado": "impago", "plan": "VIP", "cuenta_activo_recurrente": True},
        ]

        counts = summarize_counts(customers)

        self.assertEqual(counts["active_recurring"], 4)
        self.assertEqual(counts["trial"], 1)
        self.assertEqual(counts["unpaid"], 1)
        self.assertEqual(counts["active_by_plan"], {"?": 1, "Premium": 2, "VIP": 1})
        self.assertEqual(counts["summary"]["total"], 5)

    def test_summary_only_keeps_allowlisted_integer_counts(self):
        from sync.count_snapshots import SUMMARY_KEYS, summarize_counts

        with patch("customer_rules.customer_summary", return_value={
            **{key: 0 for key in SUMMARY_KEYS}, "mrr_usd": 1234,
        }):
            counts = summarize_counts([])

        self.assertEqual(set(counts["summary"]), set(SUMMARY_KEYS))
        self.assertTrue(all(isinstance(value, int) for value in counts["summary"].values()))

    def test_summarize_counts_of_empty_base_is_all_zero(self):
        from sync.count_snapshots import summarize_counts

        counts = summarize_counts([])

        self.assertEqual(counts["active_recurring"], 0)
        self.assertEqual(counts["trial"], 0)
        self.assertEqual(counts["unpaid"], 0)
        self.assertEqual(counts["active_by_plan"], {})


class WeeklyCountsTest(unittest.TestCase):
    def test_latest_per_week_keeps_the_last_day_of_each_iso_week_newest_first(self):
        from sync.count_snapshots import latest_per_week

        daily = [
            {"date": "2000-01-03", "active_recurring": 10},
            {"date": "2000-01-09", "active_recurring": 12},
            {"date": "2000-01-05", "active_recurring": 11},
            {"date": "2000-01-10", "active_recurring": 13},
        ]

        weekly = latest_per_week(daily)

        self.assertEqual(
            [(row["week_start"], row["date"], row["active_recurring"]) for row in weekly],
            [("2000-01-10", "2000-01-10", 13), ("2000-01-03", "2000-01-09", 12)],
        )

    def test_latest_per_week_of_no_rows_is_empty(self):
        from sync.count_snapshots import latest_per_week

        self.assertEqual(latest_per_week([]), [])


class CountSnapshotStorageTest(unittest.TestCase):
    def setUp(self):
        from app import app

        self.app = app
        previous_token = app.config.get("CUSTOMERS_API_TOKEN")
        self.addCleanup(app.config.__setitem__, "CUSTOMERS_API_TOKEN", previous_token)
        app.config["CUSTOMERS_API_TOKEN"] = TEST_TOKEN
        self.client = app.test_client()

    def tearDown(self):
        from db import db
        from db.models import CustomerCountSnapshot, CustomerMeta, Snapshot

        with self.app.app_context():
            CustomerCountSnapshot.query.filter(
                CustomerCountSnapshot.snapshot_date < dt.date(2001, 1, 1)
            ).delete(synchronize_session=False)
            Snapshot.query.filter(
                Snapshot.payload["test_marker"].as_string() == TEST_MARKER
            ).delete(synchronize_session=False)
            CustomerMeta.query.filter(
                CustomerMeta.email.like(f"%{TEST_DOMAIN}")
            ).delete(synchronize_session=False)
            db.session.commit()

    def add_snapshot(self, customers, generated_at):
        from db import db
        from db.models import Snapshot

        payload = {
            "test_marker": TEST_MARKER,
            "generado": generated_at,
            "clientes": customers,
            "eventos": {"altas": [], "bajas": []},
            "resumen": {},
        }
        with self.app.app_context():
            db.session.add(Snapshot(payload=payload))
            db.session.commit()
        return payload

    def refresh_returning(self, customers, generated_at):
        return lambda: self.add_snapshot(customers, generated_at)

    def stored_rows(self):
        from db.models import CustomerCountSnapshot

        with self.app.app_context():
            return [
                (row.snapshot_date.isoformat(), row.active_recurring, row.trial, row.unpaid)
                for row in CustomerCountSnapshot.query
                .filter(CustomerCountSnapshot.snapshot_date < dt.date(2001, 1, 1))
                .order_by(CustomerCountSnapshot.snapshot_date)
            ]

    @contextmanager
    def only_test_metas(self):
        """The suite runs on the real local DB: hide its manual customers."""
        import app as app_module

        real_meta_map = app_module._meta_map

        def test_meta_map():
            return {email: meta for email, meta in real_meta_map().items() if email.endswith(TEST_DOMAIN)}

        with patch.object(app_module, "_meta_map", test_meta_map):
            yield

    def run_refresh(self, customers, generated_at):
        import app as app_module

        with patch.object(app_module, "refrescar_snapshot", self.refresh_returning(customers, generated_at)):
            with self.only_test_metas(), self.app.app_context():
                return app_module.refresh_and_record_counts()

    def login(self):
        with self.client.session_transaction() as session:
            session["auth"] = True

    def test_refresh_records_one_row_per_utc_day_and_reruns_overwrite_it(self):
        first = [customer_row(f"a{TEST_DOMAIN}")]
        second = first + [customer_row(f"b{TEST_DOMAIN}")]

        self.run_refresh(first, f"{FIRST_DAY}T04:00:00+00:00")
        self.run_refresh(second, f"{FIRST_DAY}T18:30:00+00:00")

        self.assertEqual(self.stored_rows(), [(FIRST_DAY, 2, 0, 0)])

    def test_refresh_keys_the_row_by_the_payload_timestamp_in_utc(self):
        self.run_refresh([customer_row(f"a{TEST_DOMAIN}")], "2000-01-03T23:30:00-03:00")

        self.assertEqual(self.stored_rows(), [(SECOND_DAY, 1, 0, 0)])

    def test_failed_refresh_records_nothing(self):
        import app as app_module

        def failing_refresh():
            raise RuntimeError("stripe down")

        with patch.object(app_module, "refrescar_snapshot", failing_refresh):
            with self.app.app_context():
                with self.assertRaises(RuntimeError):
                    app_module.refresh_and_record_counts()

        self.assertEqual(self.stored_rows(), [])

    def test_manually_inactive_customers_are_not_counted(self):
        from db import db
        from db.models import CustomerMeta

        with self.app.app_context():
            db.session.add(CustomerMeta(email=f"gone{TEST_DOMAIN}", manual_estado="inactivo"))
            db.session.commit()
        customers = [customer_row(f"a{TEST_DOMAIN}"), customer_row(f"gone{TEST_DOMAIN}")]

        self.run_refresh(customers, f"{FIRST_DAY}T04:00:00+00:00")

        self.assertEqual(self.stored_rows(), [(FIRST_DAY, 1, 0, 0)])

    def test_recorded_actives_match_the_ceo_metrics_endpoint(self):
        customers = [
            customer_row(f"a{TEST_DOMAIN}"),
            customer_row(f"b{TEST_DOMAIN}", plan="One time payment"),
            customer_row(f"c{TEST_DOMAIN}", estado="trial"),
        ]

        self.run_refresh(customers, f"{FIRST_DAY}T04:00:00+00:00")
        with self.only_test_metas():
            response = self.client.get(
                f"/api/ceo/customer-metrics?start={FIRST_DAY}&end={FIRST_DAY}",
                headers={"Authorization": f"Bearer {TEST_TOKEN}"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.stored_rows()[0][1], response.json["active_customers"])

    def test_sync_keeps_fresh_data_and_says_so_when_recording_counts_fails(self):
        import app as app_module

        self.login()
        refresh = self.refresh_returning([customer_row(f"a{TEST_DOMAIN}")], f"{FIRST_DAY}T04:00:00+00:00")
        with patch.object(app_module, "refrescar_snapshot", refresh):
            with patch.object(count_snapshots, "record_daily_counts", side_effect=RuntimeError("db down")):
                with self.assertLogs(self.app.logger, level="ERROR"):
                    response = self.client.post("/sync", follow_redirects=True)

        html = response.get_data(as_text=True)
        self.assertIn("Datos actualizados, pero no se guardo la foto diaria de conteos", html)
        self.assertNotIn("No se pudo actualizar", html)
        self.assertEqual(self.stored_rows(), [])

    def test_sync_reports_failed_refresh_and_records_nothing(self):
        import app as app_module

        self.login()
        with patch.object(app_module, "refrescar_snapshot", side_effect=RuntimeError("stripe down")):
            response = self.client.post("/sync", follow_redirects=True)

        self.assertIn("No se pudo actualizar: stripe down", response.get_data(as_text=True))
        self.assertEqual(self.stored_rows(), [])

    def test_stats_page_shows_weekly_counts_series(self):
        self.run_refresh(
            [customer_row(f"a{TEST_DOMAIN}", plan="VIP"), customer_row(f"b{TEST_DOMAIN}", estado="trial")],
            f"{FIRST_DAY}T04:00:00+00:00",
        )
        self.login()
        with self.app.app_context():
            test_weeks = count_snapshots.latest_per_week(
                count_snapshots.daily_counts_between(dt.date(2000, 1, 1), dt.date(2000, 12, 31))
            )

        with patch.object(count_snapshots, "recent_weekly_counts", return_value=test_weeks):
            response = self.client.get("/estadisticas")

        html = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Evolucion semanal de la base", html)
        self.assertIn(FIRST_DAY, html)
        self.assertIn("VIP 1", html)

    def test_snapshot_series_endpoint_requires_bearer_token(self):
        response = self.client.get(f"/api/ceo/customer-snapshots?start={FIRST_DAY}&end={SECOND_DAY}")

        self.assertEqual(response.status_code, 401)

    def test_snapshot_series_endpoint_rejects_invalid_period(self):
        response = self.client.get(
            "/api/ceo/customer-snapshots?start=nope&end=2000-01-01",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        self.assertEqual(response.status_code, 400)

    def test_snapshot_series_endpoint_returns_counts_in_range_without_customer_data(self):
        self.run_refresh([customer_row(f"a{TEST_DOMAIN}", plan="VIP")], f"{FIRST_DAY}T04:00:00+00:00")
        self.run_refresh(
            [customer_row(f"a{TEST_DOMAIN}", plan="VIP"), customer_row(f"b{TEST_DOMAIN}", estado="trial")],
            f"{SECOND_DAY}T04:00:00+00:00",
        )

        response = self.client.get(
            f"/api/ceo/customer-snapshots?start={SECOND_DAY}&end={SECOND_DAY}",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["period"], {"start": SECOND_DAY, "end": SECOND_DAY})
        [snapshot] = response.json["snapshots"]
        self.assertEqual(snapshot["date"], SECOND_DAY)
        self.assertEqual(snapshot["active_recurring"], 1)
        self.assertEqual(snapshot["trial"], 1)
        self.assertEqual(snapshot["active_by_plan"], {"VIP": 1})
        self.assertNotIn(TEST_DOMAIN, response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
