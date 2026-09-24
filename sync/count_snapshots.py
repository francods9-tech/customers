"""Daily count-only snapshots of the customer base (no emails, no amounts)."""
import datetime as dt
from collections import Counter

import customer_rules
from db import db
from db.models import CustomerCountSnapshot

UNKNOWN_PLAN = "?"


def summarize_counts(customers):
    """Counts for one day, using the same rules as the dashboard summary."""
    summary = customer_rules.customer_summary(customers)
    active_by_plan = Counter(
        customer.get("plan") or UNKNOWN_PLAN
        for customer in customers
        if customer.get("cuenta_activo_recurrente")
    )
    return {
        "active_recurring": summary["activos_recurrentes"],
        "trial": summary["trial"],
        "unpaid": summary["impago"],
        "active_by_plan": dict(sorted(active_by_plan.items())),
        "summary": summary,
    }


def record_daily_counts(customers, captured_at):
    """Upsert the row of captured_at's UTC day; the latest capture of a day wins."""
    captured_at = captured_at.astimezone(dt.timezone.utc)
    snapshot_date = captured_at.date()
    row = CustomerCountSnapshot.query.filter_by(snapshot_date=snapshot_date).first()
    if row is None:
        row = CustomerCountSnapshot(snapshot_date=snapshot_date)
        db.session.add(row)
    counts = summarize_counts(customers)
    row.captured_at = captured_at
    row.active_recurring = counts["active_recurring"]
    row.trial = counts["trial"]
    row.unpaid = counts["unpaid"]
    row.active_by_plan = counts["active_by_plan"]
    row.summary = counts["summary"]
    db.session.commit()
    return row


def daily_counts_between(start_date, end_date):
    """Serialized rows with start_date <= snapshot_date <= end_date, oldest first."""
    rows = (CustomerCountSnapshot.query
            .filter(CustomerCountSnapshot.snapshot_date >= start_date,
                    CustomerCountSnapshot.snapshot_date <= end_date)
            .order_by(CustomerCountSnapshot.snapshot_date)
            .all())
    return [_serialize(row) for row in rows]


def _serialize(row):
    return {
        "date": row.snapshot_date.isoformat(),
        "captured_at": row.captured_at.isoformat(),
        "active_recurring": row.active_recurring,
        "trial": row.trial,
        "unpaid": row.unpaid,
        "active_by_plan": row.active_by_plan,
        "summary": row.summary,
    }
