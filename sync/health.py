"""Salud de cuenta (piratería) por accountId, desde MongoDB. Solo lectura.
Se consulta on-demand en la ficha del cliente (volumen chico de cuentas)."""
import os
from pymongo import MongoClient

_client = None


def _db():
    global _client
    if _client is None:
        _client = MongoClient(os.environ["MONGO_URI"])
    return _client["traqeer"]


_VACIO = {
    "checks": [],
    "detected_pendientes": 0,
    "detected_gestionados": 0,
    "impersonations_pendientes": 0,
    "impersonations_gestionadas": 0,
    "manual_reports": {"count": 0, "last_reported_at": "", "repeated_count": 0},
}


def salud_de_cuentas(account_ids: list) -> dict:
    """Resumen de salud para una lista de accountIds.
    No expone URLs ni screenshots (datos sensibles), solo conteos y estado."""
    if not account_ids or not os.environ.get("MONGO_URI"):
        return dict(_VACIO)
    db = _db()

    # Último health check por cuenta
    checks = list(db.account_health_checks.aggregate([
        {"$match": {"accountId": {"$in": account_ids}}},
        {"$sort": {"checkedAt": -1}},
        {"$group": {"_id": "$accountId", "last": {"$first": "$$ROOT"}}},
    ]))
    checks_out = [{
        "accountId": str(c["_id"]),
        "status": c["last"].get("status", "?"),
        "resultCount": c["last"].get("resultCount", 0),
    } for c in checks]

    # Items de piratería (excluir soft-deletes)
    det = list(db.detected_items.aggregate([
        {"$match": {"accountId": {"$in": account_ids}, "deleted": {"$ne": True}}},
        {"$group": {
            "_id": None,
            "pendientes": {"$sum": {"$cond": [{"$eq": ["$status", "pending"]}, 1, 0]}},
            "gestionados": {"$sum": {"$cond": [{"$in": ["$status", ["removed", "deindexed"]]}, 1, 0]}},
            "manual_reports_count": {"$sum": {"$cond": [
                {"$in": ["$metadata.reportedByRole", ["cliente", "customer", "usuario", "user"]]},
                1,
                0,
            ]}},
            "last_reported_at": {"$max": {"$cond": [
                {"$in": ["$metadata.reportedByRole", ["cliente", "customer", "usuario", "user"]]},
                {"$ifNull": ["$metadata.reportedAt", "$metadata.reported_at"]},
                "",
            ]}},
            "repeated_reports": {"$sum": {"$cond": [
                {"$and": [
                    {"$in": ["$metadata.reportedByRole", ["cliente", "customer", "usuario", "user"]]},
                    {"$or": [
                        {"$eq": ["$metadata.repeated", True]},
                        {"$eq": ["$metadata.duplicate", True]},
                    ]},
                ]},
                1,
                0,
            ]}},
        }},
    ]))
    det = det[0] if det else {"pendientes": 0, "gestionados": 0}

    imp = db.impersonations.count_documents(
        {"accountId": {"$in": account_ids}, "status": "pending"})
    imp_gestionadas = db.impersonations.count_documents(
        {"accountId": {"$in": account_ids}, "status": {"$in": ["reported", "removed"]}})

    return {
        "checks": checks_out,
        "detected_pendientes": det.get("pendientes", 0),
        "detected_gestionados": det.get("gestionados", 0),
        "impersonations_pendientes": imp,
        "impersonations_gestionadas": imp_gestionadas,
        "manual_reports": {
            "count": det.get("manual_reports_count", 0),
            "last_reported_at": det.get("last_reported_at") or "",
            "repeated_count": det.get("repeated_reports", 0),
        },
    }
