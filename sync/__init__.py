"""Servicio de sync: construye el snapshot de producto y lo cachea en Postgres."""
from db import db
from db.models import Snapshot
from sync.snapshot import build_snapshot


def _recompute_summary(payload):
    clientes = payload.get("clientes", [])
    payload["resumen"] = {
        "total": len(clientes),
        "activos": sum(1 for c in clientes if c.get("estado") == "activo"),
        "trial": sum(1 for c in clientes if c.get("estado") == "trial"),
        "impago": sum(1 for c in clientes if c.get("estado") == "impago"),
    }


def refrescar_snapshot():
    """Reconstruye el snapshot desde Mongo+Stripe y lo persiste. Devuelve el payload."""
    from sync import stripe_unpaid

    payload = build_snapshot()
    unpaid = stripe_unpaid.collect_unpaid_from_stripe()
    stripe_unpaid.merge_unpaid_details(payload, unpaid)
    _recompute_summary(payload)
    db.session.add(Snapshot(payload=payload))
    db.session.commit()
    return payload


def ultimo_snapshot():
    """Último snapshot guardado, o None si nunca se sincronizó."""
    snap = Snapshot.query.order_by(Snapshot.id.desc()).first()
    return snap.payload if snap else None
