"""
Snapshot de clientes desde el producto (MongoDB + Stripe).
Portado de la logica operativa de Traqeer. Clave de cliente = email (lowercase).

Produce una lista normalizada de clientes activos / trial / impago, con plan,
fecha de alta y los accountIds asociados (para consultar salud de cuenta).

Los overrides de negocio (clientes externos, exclusiones, discrepancias de plan)
estan confirmados manualmente y deben mantenerse sincronizados con Operaciones.
"""
import os
import datetime as dt

import stripe
from pymongo import MongoClient

# ── OVERRIDES DE NEGOCIO (confirmados con Operaciones) ───────────────────────
EXCLUIR_EMAILS = {"management@onlytop.co", "thualekksxto@gmail.com"}
EXCLUIR_NOMBRES = {"manolo lamin", "teresa noguera", "emiliano", "alex stiff"}
COLAB_NOMBRES = {"juana gomez", "carli cruz"}
COLAB_EMAILS = {"plopezdelacerda@gmail.com"}
CERRAR_ACCESO_NOMBRES = {
    "peach", "premium bukkake", "thomaz costa", "inocentefox", "milena azul",
    "jessica orozco", "luli garcia", "gabriela conejo rojas",
}
ONETIME_NOMBRES = {"jorge darek", "samuel lopez"}  # pagos únicos, no son activos recurrentes
EXTERNAL_OVERRIDE_EMAILS = {"aylenmoller.am@gmail.com"}

# Ventana de eventos (altas/bajas) que el dashboard puede filtrar por período.
EVENTOS_DIAS = 180
PAUSA_COMO_BAJA_EMAILS = {"ktcarvajal03@gmail.com"}
PLAN_OVERRIDE_EMAILS = {"canomarcoenric@gmail.com": "Premium"}
EXCLUIR_IMPAGOS_EMAILS = {"felipe.londono.montes@gmail.com"}
YA_CANCELADOS_EMAILS = {"ktcarvajal03@gmail.com", "marianfranco561@gmail.com"}

PLAN_LABELS = {
    "free": "Free", "starter": "Starter", "premium": "Premium",
    "vip": "VIP", "agency": "Agency",
}

NOW = lambda: dt.datetime.now(dt.timezone.utc)


def _plan_label(raw):
    return PLAN_LABELS.get((raw or "").lower(), raw or "?")


def _fmt_fecha(d):
    if not d:
        return ""
    if isinstance(d, dt.datetime):
        return d.strftime("%d/%m/%Y")
    return str(d)[:10]


def _dias_de_alta(d):
    if isinstance(d, dt.datetime):
        return (NOW().replace(tzinfo=None) - d.replace(tzinfo=None)).days
    return None


def _invoice_info(sub, now):
    inv = getattr(sub, "latest_invoice", None)
    if not inv:
        return {}
    if isinstance(inv, str):
        inv = stripe.Invoice.retrieve(inv)
    amount_due = (getattr(inv, "amount_due", 0) or 0) / 100
    amount_paid = (getattr(inv, "amount_paid", 0) or 0) / 100
    pending = max(0, amount_due - amount_paid)
    created = getattr(inv, "created", None)
    created_dt = dt.datetime.fromtimestamp(created, tz=dt.timezone.utc) if created else None
    return {
        "ultima_factura_fecha": _fmt_fecha(created_dt),
        "ultima_factura_fecha_raw": created_dt.isoformat() if created_dt else "",
        "ultima_factura_url": getattr(inv, "hosted_invoice_url", "") or "",
        "impago_monto_pendiente": round(pending, 2),
        "impago_dias": (now - created_dt).days if created_dt else None,
        "impago_estado_factura": getattr(inv, "status", "") or "",
    }


def build_snapshot() -> dict:
    mongo_uri = os.environ["MONGO_URI"]
    stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
    db = MongoClient(mongo_uri)["traqeer"]
    now = NOW()

    # ── Indices Mongo: email -> uid, uid -> cuentas ──────────────────────────
    email_to_uid, uid_to_email = {}, {}
    for u in db.users.find({}, {"_id": 1, "email": 1}):
        if u.get("email"):
            email_to_uid[u["email"].lower()] = u["_id"]
            uid_to_email[u["_id"]] = u["email"].lower()
    acc_by_uid = {}
    accounts_raw = list(db.accounts.find({}, {"allowedUsers": 1, "plan": 1, "createdAt": 1, "name": 1}))
    for acc in accounts_raw:
        for uid in acc.get("allowedUsers", []):
            acc_by_uid.setdefault(uid, []).append({
                "id": acc["_id"],
                "plan": acc.get("plan", "?"),
                "fecha_alta": acc.get("createdAt"),
                "name": acc.get("name", ""),
            })

    def db_info(email):
        uid = email_to_uid.get((email or "").lower())
        cuentas = acc_by_uid.get(uid, []) if uid else []
        if cuentas:
            return {
                "plan": cuentas[0].get("plan", "?"),
                "fecha_alta": cuentas[0].get("fecha_alta"),
                "account_ids": [c["id"] for c in cuentas],
            }
        return {"plan": "?", "fecha_alta": None, "account_ids": []}

    clientes = []
    emails_vistos = set()
    clientes_stripe = set()

    def _row(nombre, email, plan, fecha_alta, estado, anual=False, extra=None):
        return {
            "nombre": nombre,
            "email": email or "",
            "email_key": (email or "").lower(),
            "plan": plan,
            "estado": estado,           # activo | trial | impago
            "anual": anual,
            "fecha_alta": _fmt_fecha(fecha_alta),
            "fecha_alta_raw": fecha_alta.isoformat() if isinstance(fecha_alta, dt.datetime) else "",
            "dias_de_alta": _dias_de_alta(fecha_alta),
            "account_ids": db_info(email)["account_ids"],
        } | (extra or {})

    # ── Stripe: suscripciones activas ────────────────────────────────────────
    for sub in stripe.Subscription.list(status="active", limit=100).auto_paging_iter():
        cus = stripe.Customer.retrieve(sub.customer)
        email = (cus.email or "").lower()
        name = cus.name or cus.email or "?"
        nl = name.lower()
        if email in EXCLUIR_EMAILS or nl in EXCLUIR_NOMBRES:
            continue
        if nl in CERRAR_ACCESO_NOMBRES or nl in COLAB_NOMBRES or email in COLAB_EMAILS:
            continue
        if nl in ONETIME_NOMBRES:
            continue
        if email in YA_CANCELADOS_EMAILS or sub.customer in clientes_stripe:
            continue
        clientes_stripe.add(sub.customer)
        emails_vistos.add(email)

        items = sub["items"]["data"]
        anual = any(i["price"]["recurring"]["interval"] == "year" for i in items)
        info = db_info(email)
        plan = PLAN_OVERRIDE_EMAILS.get(email) or _plan_label(info["plan"])
        clientes.append(_row(name, cus.email, plan, info["fecha_alta"], "activo", anual))

    # ── Mongo: activos externos (provider=external) ──────────────────────────
    pipeline = [
        {"$match": {"status": "active", "provider": "external"}},
        {"$lookup": {"from": "accounts", "localField": "userId", "foreignField": "allowedUsers", "as": "acc"}},
        {"$unwind": "$acc"},
        {"$lookup": {"from": "users", "localField": "userId", "foreignField": "_id", "as": "user"}},
        {"$unwind": {"path": "$user", "preserveNullAndEmptyArrays": True}},
        {"$project": {"acc.name": 1, "acc.plan": 1, "acc.createdAt": 1, "user.email": 1}},
    ]
    for r in db.subscriptions.aggregate(pipeline):
        name = r.get("acc", {}).get("name", "?")
        email = (r.get("user", {}).get("email", "") or "").lower()
        nl = name.lower()
        if email in EXCLUIR_EMAILS or nl in EXCLUIR_NOMBRES:
            continue
        if email in emails_vistos or nl in CERRAR_ACCESO_NOMBRES or nl in COLAB_NOMBRES:
            continue
        if nl in ONETIME_NOMBRES:
            continue
        emails_vistos.add(email)
        clientes.append(_row(
            name, r.get("user", {}).get("email", ""),
            _plan_label(r.get("acc", {}).get("plan", "?")),
            r.get("acc", {}).get("createdAt"), "activo",
        ))

    # ── Overrides: pagan por fuera, sub no activa pero cuenta con plan ────────
    for email_ov in EXTERNAL_OVERRIDE_EMAILS:
        if email_ov in emails_vistos:
            continue
        uid = email_to_uid.get(email_ov)
        cuentas = acc_by_uid.get(uid, []) if uid else []
        if not cuentas:
            continue
        c = cuentas[0]
        emails_vistos.add(email_ov)
        clientes.append(_row(c.get("name", email_ov), email_ov,
                             _plan_label(c.get("plan", "?")), c.get("fecha_alta"), "activo"))

    # ── Trials ───────────────────────────────────────────────────────────────
    pipeline_trial = [
        {"$match": {"status": "trial"}},
        {"$lookup": {"from": "accounts", "localField": "userId", "foreignField": "allowedUsers", "as": "acc"}},
        {"$unwind": "$acc"},
        {"$lookup": {"from": "users", "localField": "userId", "foreignField": "_id", "as": "user"}},
        {"$unwind": {"path": "$user", "preserveNullAndEmptyArrays": True}},
        {"$project": {"acc.name": 1, "acc.plan": 1, "acc.createdAt": 1, "user.email": 1}},
    ]
    for r in db.subscriptions.aggregate(pipeline_trial):
        name = r.get("acc", {}).get("name", "?")
        email = (r.get("user", {}).get("email", "") or "")
        if email.lower() in emails_vistos:
            continue
        emails_vistos.add(email.lower())
        clientes.append(_row(name, email, _plan_label(r.get("acc", {}).get("plan", "?")),
                             r.get("acc", {}).get("createdAt"), "trial"))

    # ── Impagos (past_due / unpaid) ──────────────────────────────────────────
    for status in ("past_due", "unpaid"):
        for sub in stripe.Subscription.list(status=status, limit=100, expand=["data.customer", "data.latest_invoice"]).auto_paging_iter():
            cus = sub.customer if not isinstance(sub.customer, str) else stripe.Customer.retrieve(sub.customer)
            email = (cus.email or "").lower()
            if email in YA_CANCELADOS_EMAILS or email in EXCLUIR_IMPAGOS_EMAILS:
                continue
            name = cus.name or cus.email or "?"
            info = db_info(email)
            inv_info = _invoice_info(sub, now)
            # Si ya estaba listado como activo, marcarlo como impago (estado mas urgente)
            existing = next((c for c in clientes if c["email_key"] == email), None)
            if existing:
                existing["estado"] = "impago"
                existing.update(inv_info)
                continue
            clientes.append(_row(name, cus.email, _plan_label(info["plan"]),
                                 info["fecha_alta"], "impago", extra=inv_info))

    clientes.sort(key=lambda c: (c["estado"] != "impago", c["nombre"].lower()))

    # ── EVENTOS por fecha (para métricas por período) ────────────────────────
    desde_eventos = now - dt.timedelta(days=EVENTOS_DIAS)
    desde_ts = int(desde_eventos.timestamp())

    # Altas = PRIMER PAGO confirmado (>$0) del cliente, con su fecha real.
    # 1) primera factura pagada dentro de la ventana, por cliente.
    primera_en_ventana = {}
    for inv in stripe.Invoice.list(status="paid", created={"gte": desde_ts}, limit=100).auto_paging_iter():
        if (inv.amount_paid or 0) <= 0 or not inv.customer:
            continue
        prev = primera_en_ventana.get(inv.customer)
        if prev is None or inv.created < prev["ts"]:
            primera_en_ventana[inv.customer] = {
                "ts": inv.created, "email": (inv.customer_email or "").lower()}
    # 2) descartar a los que ya habían pagado antes de la ventana (no son altas nuevas).
    altas = []
    for cid, info in primera_en_ventana.items():
        antes = stripe.Invoice.list(customer=cid, status="paid", created={"lt": desde_ts}, limit=5)
        if any((i.amount_paid or 0) > 0 for i in antes.data):
            continue
        idb = db_info(info["email"])
        altas.append({
            "fecha": dt.datetime.fromtimestamp(info["ts"], tz=dt.timezone.utc).isoformat(),
            "email": info["email"],
            "plan": _plan_label(idb["plan"]),
        })

    # Bajas = cancelaciones de pago reales (tuvieron al menos un pago). Fuente: Stripe.
    bajas = []
    bajas_vistos = set()
    for sub in stripe.Subscription.list(status="canceled", limit=100).auto_paging_iter():
        sd = sub.to_dict()
        cancel_ts = sd.get("ended_at") or sd.get("canceled_at") or 0
        if not cancel_ts:
            continue
        fecha_cancel = dt.datetime.fromtimestamp(cancel_ts, tz=dt.timezone.utc)
        if fecha_cancel < desde_eventos or sub.customer in bajas_vistos:
            continue
        bajas_vistos.add(sub.customer)
        # ¿Tuvo algún pago real? Si no, fue trial que no convirtió, no es baja.
        pagas = stripe.Invoice.list(customer=sub.customer, status="paid", limit=1)
        if not pagas.data or (pagas.data[0].amount_paid or 0) <= 0:
            continue
        cus = stripe.Customer.retrieve(sub.customer)
        email = (cus.email or "").lower()
        info = db_info(email)
        bajas.append({
            "fecha": fecha_cancel.isoformat(),
            "email": email,
            "plan": _plan_label(info["plan"]),
        })

    resumen = {
        "total": len(clientes),
        "activos": sum(1 for c in clientes if c["estado"] == "activo"),
        "trial": sum(1 for c in clientes if c["estado"] == "trial"),
        "impago": sum(1 for c in clientes if c["estado"] == "impago"),
    }
    return {
        "generado": now.isoformat(),
        "clientes": clientes,
        "resumen": resumen,
        "eventos": {"altas": altas, "bajas": bajas, "ventana_dias": EVENTOS_DIAS},
    }
