import datetime as dt

import stripe

from db import db
from db.models import Snapshot
from sync import ultimo_snapshot


def _invoice_info(inv, now):
    amount_due = (getattr(inv, "amount_due", 0) or 0) / 100
    amount_paid = (getattr(inv, "amount_paid", 0) or 0) / 100
    pending = max(0, amount_due - amount_paid)
    created = getattr(inv, "created", None)
    created_dt = dt.datetime.fromtimestamp(created, tz=dt.timezone.utc) if created else None
    return {
        "ultima_factura_fecha": created_dt.strftime("%d/%m/%Y") if created_dt else "",
        "ultima_factura_fecha_raw": created_dt.isoformat() if created_dt else "",
        "ultima_factura_url": getattr(inv, "hosted_invoice_url", "") or "",
        "impago_monto_pendiente": round(pending, 2),
        "impago_dias": (now - created_dt).days if created_dt else None,
        "impago_estado_factura": getattr(inv, "status", "") or "",
    }


def _customer_email(customer):
    if isinstance(customer, str):
        customer = stripe.Customer.retrieve(customer)
    return (getattr(customer, "email", "") or "").lower()


def collect_unpaid_from_stripe():
    now = dt.datetime.now(dt.timezone.utc)
    unpaid = {}

    for status in ("past_due", "unpaid"):
        for sub in stripe.Subscription.list(
            status=status, limit=100, expand=["data.customer", "data.latest_invoice"]
        ).auto_paging_iter():
            inv = getattr(sub, "latest_invoice", None)
            if not inv:
                continue
            if isinstance(inv, str):
                inv = stripe.Invoice.retrieve(inv)
            email = _customer_email(sub.customer)
            if email:
                unpaid[email] = _invoice_info(inv, now)

    for status in ("active", "trialing"):
        for sub in stripe.Subscription.list(
            status=status, limit=100, expand=["data.customer", "data.latest_invoice"]
        ).auto_paging_iter():
            inv = getattr(sub, "latest_invoice", None)
            if not inv:
                continue
            if isinstance(inv, str):
                inv = stripe.Invoice.retrieve(inv)
            amount_due = getattr(inv, "amount_due", 0) or 0
            amount_paid = getattr(inv, "amount_paid", 0) or 0
            inv_status = getattr(inv, "status", "") or ""
            if inv_status in ("open", "void", "uncollectible") and amount_due > amount_paid:
                email = _customer_email(sub.customer)
                if email:
                    unpaid[email] = _invoice_info(inv, now)

    return unpaid


def merge_unpaid_details(payload, unpaid_by_email):
    matched = 0
    with_invoice_link = 0
    for customer in payload.get("clientes", []):
        email = (customer.get("email_key") or customer.get("email") or "").lower()
        info = unpaid_by_email.get(email)
        if not info:
            continue
        matched += 1
        customer["estado"] = "impago"
        customer.update(info)
        if info.get("ultima_factura_url"):
            with_invoice_link += 1
    return {"matched": matched, "with_invoice_link": with_invoice_link}


def refresh_unpaid_snapshot(stripe_key):
    stripe.api_key = stripe_key
    payload = ultimo_snapshot()
    if not payload:
        raise RuntimeError("No hay snapshot previo para enriquecer.")
    unpaid = collect_unpaid_from_stripe()
    stats = merge_unpaid_details(payload, unpaid)
    stats["stripe_unpaid"] = len(unpaid)
    db.session.add(Snapshot(payload=payload))
    db.session.commit()
    return stats
