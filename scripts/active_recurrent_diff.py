import customer_rules


def _meta_map(metas=None):
    return {(m.email or "").lower(): m for m in (metas or [])}


def _row_map(snapshot, metas=None):
    metas_by_email = _meta_map(metas)
    rows = {}
    for customer in snapshot.get("clientes", []):
        email = (customer.get("email_key") or customer.get("email") or "").lower()
        if not email:
            continue
        enriched = customer_rules.enrich_customer(customer, metas_by_email.get(email))
        rows[email] = enriched
    return rows


def _recurrent_emails(rows):
    return {email for email, row in rows.items() if row.get("cuenta_activo_recurrente")}


def latest_real_payloads(snapshot_rows, count=2):
    payloads = []
    for row in snapshot_rows:
        payload = row.payload or {}
        if payload.get("test_marker"):
            continue
        payloads.append(payload)
        if len(payloads) >= count:
            break
    return payloads


def _describe(email, before_rows, after_rows):
    before = before_rows.get(email) or {}
    after = after_rows.get(email) or {}
    source = after or before
    return {
        "email": email,
        "nombre": source.get("nombre", ""),
        "before_estado": before.get("estado", ""),
        "after_estado": after.get("estado", ""),
        "before_plan": before.get("plan", ""),
        "after_plan": after.get("plan", ""),
        "before_tipo": before.get("tipo_cliente", ""),
        "after_tipo": after.get("tipo_cliente", ""),
        "cancelacion_programada": bool(after.get("cancelacion_programada")),
    }


def diff_recurrent_customers(before_snapshot, after_snapshot, metas=None):
    before_rows = _row_map(before_snapshot, metas)
    after_rows = _row_map(after_snapshot, metas)
    before_emails = _recurrent_emails(before_rows)
    after_emails = _recurrent_emails(after_rows)
    removed = sorted(before_emails - after_emails)
    added = sorted(after_emails - before_emails)
    return {
        "before_count": len(before_emails),
        "after_count": len(after_emails),
        "delta": len(after_emails) - len(before_emails),
        "removed": [_describe(email, before_rows, after_rows) for email in removed],
        "added": [_describe(email, before_rows, after_rows) for email in added],
    }


def _print_rows(title, rows):
    print(title)
    if not rows:
        print("  - ninguno")
        return
    for row in rows:
        print(
            "  - "
            f"{row['nombre'] or row['email']} <{row['email']}> "
            f"{row['before_estado'] or '-'} -> {row['after_estado'] or '-'}; "
            f"{row['before_plan'] or '-'} -> {row['after_plan'] or '-'}; "
            f"{row['before_tipo'] or '-'} -> {row['after_tipo'] or '-'}"
        )


def main():
    from app import app
    from db.models import CustomerMeta, Snapshot

    with app.app_context():
        snapshots = Snapshot.query.order_by(Snapshot.id.desc()).limit(20).all()
        payloads = latest_real_payloads(snapshots, count=2)
        if len(payloads) < 2:
            print("No hay dos snapshots para comparar.")
            return 1
        metas = CustomerMeta.query.all()
        diff = diff_recurrent_customers(payloads[1], payloads[0], metas)

    print(f"Activos recurrentes: {diff['before_count']} -> {diff['after_count']} ({diff['delta']:+d})")
    _print_rows("Salieron de activos recurrentes", diff["removed"])
    _print_rows("Entraron a activos recurrentes", diff["added"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
