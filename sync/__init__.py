"""Servicio de sync: construye el snapshot de producto y lo cachea en Postgres."""
from db import db
from db.models import Snapshot
from sync.snapshot import build_snapshot


def refrescar_snapshot():
    """Reconstruye el snapshot desde Mongo+Stripe y lo persiste. Devuelve el payload."""
    payload = build_snapshot()
    db.session.add(Snapshot(payload=payload))
    db.session.commit()
    return payload


def ultimo_snapshot():
    """Último snapshot guardado, o None si nunca se sincronizó."""
    snap = Snapshot.query.order_by(Snapshot.id.desc()).first()
    return snap.payload if snap else None
