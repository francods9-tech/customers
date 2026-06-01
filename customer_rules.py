import datetime as dt

PLAN_OPTIONS = [
    ("", "Sin ajuste manual"),
    ("starter", "Starter"),
    ("premium", "Premium"),
    ("vip", "VIP"),
    ("agency", "Agency"),
    ("one_time", "One time payment"),
    ("free_colab", "Free por colab"),
]
PLAN_LABELS = dict(PLAN_OPTIONS)

STATUS_OPTIONS = [
    ("", "Sin ajuste manual"),
    ("activo", "Activo"),
    ("trial", "Trial"),
    ("impago", "Impago"),
    ("pausado_impago", "Pausado por impago"),
    ("inactivo_impago", "Inactivo por impago"),
    ("inactivo", "Inactivo"),
]
STATUS_LABELS = dict(STATUS_OPTIONS)
UNPAID_STATES = {"impago", "pausado_impago", "inactivo_impago"}

TYPE_OPTIONS = [
    ("", "Automatico"),
    ("individual", "Individual"),
    ("agencia", "Agencia"),
    ("one_time", "One time payment"),
    ("free_colab", "Free por colab"),
    ("colab_descuento", "Colab con descuento"),
]
TYPE_LABELS = dict(TYPE_OPTIONS)


def _meta_value(meta, name, default=""):
    return (getattr(meta, name, default) or "").strip()


def _infer_type(plan):
    plan_l = (plan or "").strip().lower()
    if plan_l == "agency":
        return "agencia"
    if plan_l == "one time payment":
        return "one_time"
    if plan_l == "free por colab":
        return "free_colab"
    return "individual"


def _parse_date(value):
    parsed = _parse_dt(value)
    return parsed.date() if parsed else None


def _fmt_date_es(value):
    parsed = _parse_dt(value)
    return parsed.strftime("%d/%m/%Y") if parsed else ""


def colab_summary(meta=None, today=None):
    tipo = _meta_value(meta, "tipo_cliente") if meta else ""
    manual_plan = _meta_value(meta, "manual_plan") if meta else ""
    es_colab = tipo in ("free_colab", "colab_descuento") or manual_plan == "free_colab"
    today = today or dt.datetime.now(dt.timezone.utc).date()
    revision = _parse_date(_meta_value(meta, "colab_revision") if meta else "")
    dias_revision = None
    revision_pendiente = False
    if revision:
        dias_revision = (today - revision).days
        revision_pendiente = dias_revision >= 0
    return {
        "es_colab": es_colab,
        "tipo": tipo or ("free_colab" if manual_plan == "free_colab" else ""),
        "label": TYPE_LABELS.get(tipo or manual_plan, ""),
        "descuento": _meta_value(meta, "colab_descuento") if meta else "",
        "acuerdo": _meta_value(meta, "colab_acuerdo") if meta else "",
        "inicio": _meta_value(meta, "colab_inicio") if meta else "",
        "revision": _meta_value(meta, "colab_revision") if meta else "",
        "revision_pendiente": revision_pendiente,
        "dias_revision": dias_revision,
    }


def trial_summary(customer, today=None, warning_days=7):
    today = today or dt.datetime.now(dt.timezone.utc).date()
    end_dt = _parse_dt(customer.get("trial_fin_raw") or customer.get("trial_fin"))
    if not end_dt:
        start_dt = _parse_dt(customer.get("fecha_alta_raw"))
        end_dt = start_dt + dt.timedelta(days=7) if start_dt else None
    if not end_dt:
        return {"fecha": "", "fecha_raw": "", "dias": None, "por_vencer": False, "vencido": False}
    end_date = end_dt.date()
    days = (end_date - today).days
    return {
        "fecha": end_dt.strftime("%d/%m/%Y"),
        "fecha_raw": end_dt.isoformat(),
        "dias": days,
        "por_vencer": days <= warning_days,
        "vencido": days < 0,
    }


def reactivation_summary(customer, bajas):
    email = (customer.get("email_key") or customer.get("email") or "").lower()
    if customer.get("estado") != "activo" or not email:
        return {"reactivado": False, "ultima_baja": "", "ultima_baja_raw": ""}
    matches = [b for b in bajas if (b.get("email") or "").lower() == email and _parse_dt(b.get("fecha"))]
    if not matches:
        return {"reactivado": False, "ultima_baja": "", "ultima_baja_raw": ""}
    last = max(matches, key=lambda b: _parse_dt(b.get("fecha")))
    return {
        "reactivado": True,
        "ultima_baja": _fmt_date_es(last.get("fecha")),
        "ultima_baja_raw": last.get("fecha") or "",
    }


def remove_reactivated_cancellations(bajas, customers):
    active_emails = {
        (c.get("email_key") or c.get("email") or "").lower()
        for c in customers
        if c.get("estado") == "activo"
    }
    return [b for b in bajas if (b.get("email") or "").lower() not in active_emails]


def enrich_customer(customer, meta=None):
    """Apply AM manual overrides to one customer row without mutating input."""
    out = dict(customer)
    original_plan = out.get("plan") or "?"
    original_status = out.get("estado") or ""

    manual_plan = _meta_value(meta, "manual_plan") if meta else ""
    manual_status = _meta_value(meta, "manual_estado") if meta else ""
    manual_type = _meta_value(meta, "tipo_cliente") if meta else ""

    if manual_plan:
        out["plan"] = PLAN_LABELS.get(manual_plan, original_plan)
    else:
        out["plan"] = original_plan

    if manual_status:
        out["estado"] = manual_status
    else:
        out["estado"] = original_status
        if original_status == "impago":
            out["estado"] = unpaid_operational_status(unpaid_summary(out).get("dias")).get("estado")

    if manual_plan in ("one_time", "free_colab"):
        tipo_key = manual_plan
    elif manual_type:
        tipo_key = manual_type
    else:
        tipo_key = _infer_type(out["plan"])

    out["plan_original"] = original_plan
    out["estado_original"] = original_status
    out["manual_plan"] = manual_plan
    out["manual_estado"] = manual_status
    out["tipo_cliente_key"] = tipo_key
    out["tipo_cliente"] = TYPE_LABELS.get(tipo_key, "Individual")
    out["colab"] = colab_summary(meta)
    out["trial"] = trial_summary(out) if out["estado"] == "trial" else None
    out["cuenta_activo_recurrente"] = (
        out["estado"] == "activo" and tipo_key not in ("one_time", "free_colab")
    )
    return out


def filter_customers(customers, estado=None, origen=None, tipo=None, q=None, recurrente=False):
    rows = list(customers)
    if recurrente:
        rows = [c for c in rows if c.get("cuenta_activo_recurrente")]
    if estado:
        if estado == "impago":
            rows = [c for c in rows if c.get("estado") in UNPAID_STATES]
        else:
            rows = [c for c in rows if c.get("estado") == estado]
    if origen:
        rows = [c for c in rows if c.get("origen") == origen]
    if tipo:
        rows = [c for c in rows if c.get("tipo_cliente_key") == tipo]
    if q:
        needle = q.strip().lower()
        rows = [
            c for c in rows
            if needle in (c.get("nombre") or "").lower()
            or needle in (c.get("email") or "").lower()
        ]
    return rows


def customer_summary(customers):
    rows = list(customers)
    return {
        "total": len(rows),
        "activos_recurrentes": sum(1 for c in rows if c.get("cuenta_activo_recurrente")),
        "trial": sum(1 for c in rows if c.get("estado") == "trial"),
        "impago": sum(1 for c in rows if c.get("estado") in UNPAID_STATES),
        "pausado_impago": sum(1 for c in rows if c.get("estado") == "pausado_impago"),
        "inactivo_impago": sum(1 for c in rows if c.get("estado") == "inactivo_impago"),
        "inactivo": sum(1 for c in rows if c.get("estado") == "inactivo"),
        "agencias": sum(1 for c in rows if c.get("tipo_cliente_key") == "agencia"),
        "one_time": sum(1 for c in rows if c.get("tipo_cliente_key") == "one_time"),
        "free_colab": sum(1 for c in rows if c.get("tipo_cliente_key") == "free_colab"),
        "colab_descuento": sum(1 for c in rows if c.get("tipo_cliente_key") == "colab_descuento"),
        "colabs_total": sum(1 for c in rows if (c.get("colab") or {}).get("es_colab")),
        "colabs_revision_pendiente": sum(
            1 for c in rows if (c.get("colab") or {}).get("revision_pendiente")
        ),
    }


def _parse_dt(value):
    if not value:
        return None
    if isinstance(value, dt.datetime):
        return value if value.tzinfo else value.replace(tzinfo=dt.timezone.utc)
    try:
        parsed = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.timezone.utc)


def unpaid_summary(customer, today=None):
    today = today or dt.datetime.now(dt.timezone.utc)
    invoices = _pending_invoices(customer)
    invoice_date = _parse_dt(invoices[0].get("fecha_raw")) if invoices else _parse_dt(
        customer.get("ultima_factura_fecha_raw") or customer.get("impago_desde_raw")
    )
    days = None
    if invoice_date:
        days = max(0, (today - invoice_date).days)
    amount = round(sum((invoice.get("monto_pendiente") or 0) for invoice in invoices), 2) if invoices else customer.get("impago_monto_pendiente")
    status = unpaid_operational_status(days)
    return {
        "dias": days,
        "label": f"{days} dias" if days is not None else "sin fecha",
        "factura_url": (invoices[0].get("url") if invoices else "") or customer.get("ultima_factura_url") or "",
        "monto": amount,
        "facturas": invoices,
        "facturas_count": len(invoices) if invoices else (1 if customer.get("ultima_factura_url") else 0),
        "estado_operativo": status["estado"],
        "estado_label": status["label"],
        "acceso_free": _looks_free_access(customer),
    }


def _pending_invoices(customer):
    invoices = []
    for invoice in customer.get("facturas_pendientes") or []:
        copied = dict(invoice)
        copied.setdefault("url", copied.get("factura_url", ""))
        copied.setdefault("monto_pendiente", copied.get("monto", 0))
        invoices.append(copied)
    return sorted(
        invoices,
        key=lambda invoice: _parse_dt(invoice.get("fecha_raw")) or dt.datetime.max.replace(tzinfo=dt.timezone.utc),
    )


def unpaid_operational_status(days):
    if days is None or days < 30:
        return {"estado": "impago", "label": "Impago"}
    if days < 90:
        return {"estado": "pausado_impago", "label": "Pausado por impago"}
    return {"estado": "inactivo_impago", "label": "Inactivo por impago"}


def _looks_free_access(customer):
    plan = (customer.get("plan") or "").lower()
    original = (customer.get("plan_original") or "").lower()
    return "free" in plan or "free" in original


def sort_unpaid_priority(customers):
    def key(customer):
        days = (customer.get("impago") or {}).get("dias")
        if days is None:
            return (1, 0, (customer.get("nombre") or "").lower())
        return (0, -days, (customer.get("nombre") or "").lower())

    return sorted(customers, key=key)


def sort_oldest_first(items):
    def key(item):
        created = getattr(item, "created_at", None)
        parsed = _parse_dt(created)
        return parsed or dt.datetime.max.replace(tzinfo=dt.timezone.utc)

    return sorted(items, key=key)
