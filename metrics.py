"""Cálculo de métricas por período sobre los eventos del snapshot.
Todo en UTC (Stripe y Mongo guardan en UTC)."""
import datetime as dt
from collections import Counter, OrderedDict

PRESETS = [
    ("todo", "Todo"),
    ("7d", "Últimos 7 días"),
    ("30d", "Últimos 30 días"),
    ("90d", "Últimos 90 días"),
    ("mes", "Este mes"),
    ("mes_pasado", "Mes pasado"),
]
PRESET_LABELS = dict(PRESETS)


def _parse_date(s):
    try:
        return dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc)
    except (ValueError, TypeError):
        return None


def resolver_periodo(args, eventos=None):
    """Devuelve (desde, hasta, label, prev_desde, prev_hasta).
    Acepta ?preset= o ?desde=&hasta= (YYYY-MM-DD). Default: 30d."""
    now = dt.datetime.now(dt.timezone.utc)
    desde = _parse_date(args.get("desde"))
    hasta = _parse_date(args.get("hasta"))
    preset = args.get("preset")

    if desde and hasta:
        hasta = hasta + dt.timedelta(days=1)  # inclusivo del día elegido
        label = f"{desde:%d/%m/%Y} – {(hasta - dt.timedelta(days=1)):%d/%m/%Y}"
    elif preset == "todo":
        fechas = [_parse_date(e.get("fecha")) for e in (eventos or [])]
        fechas = [f for f in fechas if f]
        desde = min(fechas).replace(hour=0, minute=0, second=0, microsecond=0) if fechas else now - dt.timedelta(days=180)
        hasta = now
        label = PRESET_LABELS["todo"]
    elif preset == "mes":
        desde = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        hasta = now
        label = PRESET_LABELS["mes"]
    elif preset == "mes_pasado":
        primero_este = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        hasta = primero_este
        desde = (primero_este - dt.timedelta(days=1)).replace(day=1)
        label = PRESET_LABELS["mes_pasado"]
    else:
        dias = {"7d": 7, "90d": 90}.get(preset, 30)
        preset = preset if preset in ("7d", "90d") else "30d"
        hasta = now
        desde = now - dt.timedelta(days=dias)
        label = PRESET_LABELS[preset]

    delta = hasta - desde
    return desde, hasta, label, desde - delta, desde


def _en_rango(ev, desde, hasta):
    f = _parse_date(ev.get("fecha"))
    return f is not None and desde <= f < hasta


def enriquecer(eventos, metas):
    """Agrega el origen (canal) del AM a cada evento, cruzando por email."""
    out = []
    for ev in eventos:
        m = metas.get((ev.get("email") or "").lower())
        out.append({**ev, "origen": m.origen if m else "sin_asignar"})
    return out


def filtrar(eventos, desde, hasta, canal=None):
    res = [e for e in eventos if _en_rango(e, desde, hasta)]
    if canal:
        res = [e for e in res if e.get("origen") == canal]
    return res


def por_canal(eventos):
    return Counter(e.get("origen", "sin_asignar") for e in eventos)


def serie_temporal(eventos, desde, hasta):
    """Conteo por día (o por semana si el rango supera 70 días)."""
    dias = (hasta - desde).days
    semanal = dias > 70
    buckets = OrderedDict()
    cur = desde
    paso = dt.timedelta(days=7 if semanal else 1)
    while cur < hasta:
        buckets[cur.strftime("%Y-%m-%d")] = 0
        cur += paso
    claves = list(buckets.keys())
    for e in eventos:
        f = _parse_date(e.get("fecha"))
        if not f:
            continue
        idx = (f - desde).days // (7 if semanal else 1)
        if 0 <= idx < len(claves):
            buckets[claves[idx]] += 1
    etiqueta = "semana" if semanal else "día"
    return {"labels": list(buckets.keys()), "valores": list(buckets.values()), "agrupado": etiqueta}


def delta_pct(actual, anterior):
    if anterior == 0:
        return None if actual == 0 else 100.0
    return round((actual - anterior) / anterior * 100, 1)


def recurrent_northstar_delta(current_count, altas_periodo, bajas_periodo):
    previous_count = current_count - len(altas_periodo) + len(bajas_periodo)
    return {
        "valor": current_count,
        "previo": previous_count,
        "delta": delta_pct(current_count, previous_count),
    }
