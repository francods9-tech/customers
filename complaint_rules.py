import datetime as dt
from collections import defaultdict


DEFAULT_COMPLAINT_CATEGORIES = [
    ("encuentra_links", "Encuentra links"),
    ("envia_links", "Envia links"),
    ("tiempos_gestion", "Tiempos de gestion"),
]

REQUEST_TYPES = ("queja", "solicitud")

TEAM_OPTIONS = [
    ("cs", "Customer Success"),
    ("ops", "Operaciones"),
]
TEAM_LABELS = dict(TEAM_OPTIONS)

REQUEST_STATUS_OPTIONS = [
    ("abierta", "Abierta"),
    ("en_gestion", "En gestion"),
    ("comunicar", "Comunicar al cliente"),
]
REQUEST_STATUS_LABELS = dict(REQUEST_STATUS_OPTIONS) | {
    "en_proceso": "En gestion",
    "esperando": "Comunicar al cliente",
    "resuelta": "Resuelta",
}

IMPORTANCE_OPTIONS = [
    ("baja", "Baja"),
    ("media", "Media"),
    ("alta", "Alta"),
]
IMPORTANCE_LABELS = dict(IMPORTANCE_OPTIONS)

STATUS_TEAM = {
    "abierta": "cs",
    "en_gestion": "ops",
    "comunicar": "cs",
    "en_proceso": "ops",
    "esperando": "cs",
    "resuelta": "cs",
}


def category_key(label):
    key = "".join(ch.lower() if ch.isalnum() else "_" for ch in (label or "").strip()).strip("_")
    while "__" in key:
        key = key.replace("__", "_")
    return key


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


def category_label(key, categories):
    if not key:
        return "Sin categoria"
    return categories.get(key, key)


def is_customer_request(item):
    return getattr(item, "tipo", "") in REQUEST_TYPES


def normalize_status(status):
    legacy = {"en_proceso": "en_gestion", "esperando": "comunicar"}
    return legacy.get(status or "", status or "abierta")


def team_for_status(status):
    return STATUS_TEAM.get(status or "abierta", "cs")


def _elapsed_days(start, end):
    if not start:
        return 0
    if end.tzinfo is None:
        end = end.replace(tzinfo=dt.timezone.utc)
    return max(0, (end - start).days)


def _age_class(days):
    if days > 14:
        return "age-danger"
    if days > 7:
        return "age-warn"
    return ""


def ticket_age(ticket, today=None):
    created = _parse_dt(getattr(ticket, "created_at", None))
    if not created:
        return {"dias": 0, "class": ""}
    today = today or dt.datetime.now(dt.timezone.utc)
    days = _elapsed_days(created, today)
    return {"dias": days, "class": _age_class(days)}


def ticket_duration(ticket, today=None):
    created = _parse_dt(getattr(ticket, "created_at", None))
    if not created:
        return {"dias": 0, "class": ""}
    today = today or dt.datetime.now(dt.timezone.utc)
    resolved_at = _parse_dt(getattr(ticket, "resolved_at", None))
    end = resolved_at if resolved_at else today
    days = _elapsed_days(created, end)
    return {"dias": days, "class": _age_class(days)}


def ticket_status_key(ticket):
    if bool(getattr(ticket, "resuelta", False)) or getattr(ticket, "estado_gestion", "") == "resuelta":
        return "resuelta"
    return normalize_status(getattr(ticket, "estado_gestion", "") or "abierta")


def ticket_status_class(ticket):
    return f"status-{ticket_status_key(ticket)}"


def request_stats(items):
    open_count = 0
    resolved_count = 0
    by_team = {"cs": 0, "ops": 0}
    by_status = {key: 0 for key, _ in REQUEST_STATUS_OPTIONS}

    for item in items:
        if not is_customer_request(item):
            continue
        resolved = bool(getattr(item, "resuelta", False)) or getattr(item, "estado_gestion", "") == "resuelta"
        status = normalize_status(getattr(item, "estado_gestion", "") or ("resuelta" if resolved else "abierta"))
        team = getattr(item, "equipo", "") or "cs"
        by_status[status] = by_status.get(status, 0) + 1
        if resolved:
            resolved_count += 1
        else:
            open_count += 1
            by_team[team] = by_team.get(team, 0) + 1

    return {
        "total_abiertas": open_count,
        "total_resueltas": resolved_count,
        "total": open_count + resolved_count,
        "por_equipo": by_team,
        "por_estado": by_status,
    }


def complaint_stats(complaints, today=None):
    today = today or dt.datetime.now(dt.timezone.utc)
    by_category = defaultdict(lambda: {"abiertas": 0, "resueltas": 0, "total": 0})
    total_open = 0
    total_resolved = 0
    max_open_days = 0

    for complaint in complaints:
        category = getattr(complaint, "categoria", "") or "sin_categoria"
        resolved = bool(getattr(complaint, "resuelta", False))
        bucket = by_category[category]
        bucket["total"] += 1
        if resolved:
            bucket["resueltas"] += 1
            total_resolved += 1
        else:
            bucket["abiertas"] += 1
            total_open += 1
            created = _parse_dt(getattr(complaint, "created_at", None))
            if created:
                max_open_days = max(max_open_days, max(0, (today - created).days))

    return {
        "total_abiertas": total_open,
        "total_resueltas": total_resolved,
        "total": total_open + total_resolved,
        "max_dias_abierta": max_open_days,
        "por_categoria": dict(by_category),
    }
