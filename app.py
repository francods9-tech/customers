import datetime as dt
from collections import Counter, defaultdict
from functools import wraps
from zoneinfo import ZoneInfo

from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, abort)
from sqlalchemy import inspect, text

import complaint_rules
import customer_rules
import message_rules
import metrics
from config import Config
from db import db
from db.models import (ChurnReason, ColabCreator, ComplaintCategory, CustomerMeta,
                       CustomerReminder, Interaccion, INSTAGRAM_ORIGEN_KEYS, INSTAGRAM_VARIANTS,
                       MessageCategory, MessageTemplate, ORIGENES, ORIGENES_BASE,
                       TicketComment,
                       ORIGEN_LABELS, origen_group_key)
from sync import refrescar_snapshot, ultimo_snapshot
from sync.health import salud_de_cuentas

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

CHURN_REASON_OPTIONS = [
    ("", "Sin motivo"),
    ("precio", "Precio"),
    ("no_uso", "No uso"),
    ("resultado", "No vio resultado"),
    ("soporte", "Soporte"),
    ("competencia", "Competencia"),
    ("pausa", "Pausa temporal"),
    ("otro", "Otro"),
]

COLAB_CREATOR_STATUS = [
    ("idea", "Idea"),
    ("contactado", "Contactado"),
    ("negociando", "Negociando"),
    ("activo", "Activo"),
    ("pausado", "Pausado"),
    ("cerrado", "Cerrado"),
]
COLAB_CREATOR_STATUS_LABELS = dict(COLAB_CREATOR_STATUS)
COLAB_CREATOR_TYPES = [
    ("free", "Free"),
    ("descuento", "Descuento"),
    ("pago", "Pago"),
    ("intercambio", "Intercambio"),
]
COLAB_CREATOR_TYPE_LABELS = dict(COLAB_CREATOR_TYPES)
MADRID_TZ = ZoneInfo("Europe/Madrid")
TASK_ASSIGNEE_OPTIONS = complaint_rules.COMMENT_AUTHOR_OPTIONS
TASK_ASSIGNEE_VALUES = {key for key, _ in TASK_ASSIGNEE_OPTIONS}
ONBOARDING_TASK_SOURCE = "onboarding"
ONBOARDING_TASK_ASSIGNEE = "Nicky"
ONBOARDING_TASK_TEXT = "Bienvenida pendiente"


def _ensure_local_schema():
    """SQLite create_all does not add columns to an existing local DB."""
    inspector = inspect(db.engine)
    if "customer_meta" not in inspector.get_table_names():
        return
    columns = {c["name"] for c in inspector.get_columns("customer_meta")}
    additions = {
        "manual_plan": "ALTER TABLE customer_meta ADD COLUMN manual_plan VARCHAR(32) NOT NULL DEFAULT ''",
        "manual_estado": "ALTER TABLE customer_meta ADD COLUMN manual_estado VARCHAR(32) NOT NULL DEFAULT ''",
        "tipo_cliente": "ALTER TABLE customer_meta ADD COLUMN tipo_cliente VARCHAR(32) NOT NULL DEFAULT ''",
        "whatsapp": "ALTER TABLE customer_meta ADD COLUMN whatsapp VARCHAR(80) NOT NULL DEFAULT ''",
        "usuario": "ALTER TABLE customer_meta ADD COLUMN usuario VARCHAR(120) NOT NULL DEFAULT ''",
        "colab_descuento": "ALTER TABLE customer_meta ADD COLUMN colab_descuento VARCHAR(80) NOT NULL DEFAULT ''",
        "colab_acuerdo": "ALTER TABLE customer_meta ADD COLUMN colab_acuerdo TEXT NOT NULL DEFAULT ''",
        "colab_inicio": "ALTER TABLE customer_meta ADD COLUMN colab_inicio VARCHAR(10) NOT NULL DEFAULT ''",
        "colab_revision": "ALTER TABLE customer_meta ADD COLUMN colab_revision VARCHAR(10) NOT NULL DEFAULT ''",
    }
    for name, sql in additions.items():
        if name not in columns:
            db.session.execute(text(sql))
    db.session.commit()

    interaction_additions = {
        "resuelta": "ALTER TABLE interacciones ADD COLUMN resuelta BOOLEAN NOT NULL DEFAULT 0",
        "categoria": "ALTER TABLE interacciones ADD COLUMN categoria VARCHAR(64) NOT NULL DEFAULT ''",
        "equipo": "ALTER TABLE interacciones ADD COLUMN equipo VARCHAR(16) NOT NULL DEFAULT 'cs'",
        "estado_gestion": "ALTER TABLE interacciones ADD COLUMN estado_gestion VARCHAR(32) NOT NULL DEFAULT 'abierta'",
        "importancia": "ALTER TABLE interacciones ADD COLUMN importancia VARCHAR(16) NOT NULL DEFAULT 'media'",
        "resolved_at": "ALTER TABLE interacciones ADD COLUMN resolved_at TIMESTAMP WITH TIME ZONE",
    }
    for name, sql in interaction_additions.items():
        columns = {c["name"] for c in inspect(db.engine).get_columns("interacciones")}
        if name not in columns:
            db.session.execute(text(sql))
            db.session.commit()

    if "customer_reminders" in inspector.get_table_names():
        reminder_columns = {c["name"] for c in inspect(db.engine).get_columns("customer_reminders")}
        if "assignee" not in reminder_columns:
            db.session.execute(text("ALTER TABLE customer_reminders ADD COLUMN assignee VARCHAR(120) NOT NULL DEFAULT ''"))
            db.session.commit()
        reminder_columns = {c["name"] for c in inspect(db.engine).get_columns("customer_reminders")}
        if "source" not in reminder_columns:
            db.session.execute(text("ALTER TABLE customer_reminders ADD COLUMN source VARCHAR(32) NOT NULL DEFAULT ''"))
            db.session.commit()


def _seed_complaint_categories():
    for key, label in complaint_rules.DEFAULT_COMPLAINT_CATEGORIES:
        if not db.session.get(ComplaintCategory, key):
            db.session.add(ComplaintCategory(key=key, label=label))
    db.session.commit()


def _seed_message_categories():
    for key, label in message_rules.DEFAULT_MESSAGE_CATEGORIES:
        if not db.session.get(MessageCategory, key):
            db.session.add(MessageCategory(key=key, label=label))
    db.session.commit()


def _seed_cs_pack_templates():
    existing = {
        row.titulo for row in MessageTemplate.query
        .filter(MessageTemplate.titulo.in_([t["titulo"] for t in message_rules.CS_PACK_TEMPLATES]))
        .all()
    }
    for tpl in message_rules.CS_PACK_TEMPLATES:
        if tpl["titulo"] in existing:
            continue
        db.session.add(MessageTemplate(
            titulo=tpl["titulo"],
            cuerpo=tpl["cuerpo"],
            categoria_key=tpl["categoria_key"],
            tags=message_rules.parse_tags(tpl["tags"]),
        ))
    db.session.commit()


with app.app_context():
    db.create_all()
    _ensure_local_schema()
    _seed_complaint_categories()
    _seed_message_categories()
    _seed_cs_pack_templates()


# ── Auth simple (clave compartida del equipo) ────────────────────────────────
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("auth"):
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return wrapper


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if app.config["APP_PASSWORD"] and request.form.get("password") == app.config["APP_PASSWORD"]:
            session["auth"] = True
            return redirect(request.args.get("next") or url_for("index"))
        flash("Clave incorrecta", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/healthz")
def healthz():
    return {"status": "ok"}


# ── Helpers ───────────────────────────────────────────────────────────────────
def _meta_map():
    return {m.email: m for m in CustomerMeta.query.all()}


def _get_or_create_meta(email):
    email = (email or "").lower()
    meta = db.session.get(CustomerMeta, email)
    if not meta:
        meta = CustomerMeta(email=email)
        db.session.add(meta)
        db.session.commit()
    return meta


def _complaint_categories(active_only=True):
    query = ComplaintCategory.query
    if active_only:
        query = query.filter_by(activa=True)
    return query.order_by(ComplaintCategory.label.asc()).all()


def _complaint_category_map():
    return {c.key: c.label for c in ComplaintCategory.query.all()}


def _parse_iso_date(value):
    try:
        return dt.date.fromisoformat((value or "").strip())
    except ValueError:
        return None


def _reminder_view(row, nombre_por_email=None):
    due = _parse_iso_date(row.due_date)
    today = dt.datetime.now(MADRID_TZ).date()
    days = (due - today).days if due else None
    if days is None:
        timing = "sin fecha"
    elif days < 0:
        timing = f"vencio hace {-days} dias"
    elif days == 0:
        timing = "hoy"
    else:
        timing = f"faltan {days} dias"
    is_completed = row.completed_at is not None
    if is_completed:
        status = "completed"
        status_label = "Completada"
        status_class = ""
    elif days is not None and days < 0:
        status = "overdue"
        status_label = "Vencida"
        status_class = "tag-warn"
    elif days == 0:
        status = "today"
        status_label = "Hoy"
        status_class = "tag-warn"
    else:
        status = "pending"
        status_label = "Pendiente"
        status_class = ""
    assignee = row.assignee or ""
    customer_email = row.customer_email or ""
    is_generic = not customer_email
    source = row.source or ""
    if source == ONBOARDING_TASK_SOURCE and not is_completed:
        status_class = "tag-warn"
    return {
        "id": row.id,
        "customer_email": customer_email,
        "customer_name": "Sin cliente" if is_generic else (nombre_por_email or {}).get(customer_email, customer_email),
        "is_generic": is_generic,
        "texto": row.texto,
        "due_date": row.due_date,
        "due_label": due.strftime("%d/%m/%Y") if due else row.due_date,
        "days": days,
        "timing": timing,
        "assignee": assignee,
        "assignee_label": assignee or "Sin asignar",
        "source": source,
        "status": status,
        "status_label": status_label,
        "status_class": status_class,
        "completed_at": row.completed_at,
    }


def _active_reminders(nombre_por_email=None):
    rows = (CustomerReminder.query
            .filter(CustomerReminder.completed_at.is_(None))
            .order_by(CustomerReminder.due_date.asc(), CustomerReminder.created_at.asc())
            .all())
    return [_reminder_view(row, nombre_por_email) for row in rows]


def _task_groups(rows, selected_date, nombre_por_email=None):
    groups = {"overdue": [], "today": [], "upcoming": [], "completed": []}
    for row in rows:
        item = _reminder_view(row, nombre_por_email)
        due = _parse_iso_date(row.due_date)
        if row.completed_at:
            groups["completed"].append(item)
        elif due and due < selected_date:
            groups["overdue"].append(item)
        elif due == selected_date:
            groups["today"].append(item)
        else:
            groups["upcoming"].append(item)
    return groups


def _task_query_from_request():
    selected_date = _parse_iso_date(request.args.get("date")) or dt.datetime.now(MADRID_TZ).date()
    assignee = (request.args.get("assignee") or "").strip()
    status = request.args.get("status") or "activas"
    query = CustomerReminder.query
    if assignee in TASK_ASSIGNEE_VALUES:
        query = query.filter(CustomerReminder.assignee == assignee)
    elif assignee == "sin_asignar":
        query = query.filter(CustomerReminder.assignee == "")
    if status == "completadas":
        query = query.filter(CustomerReminder.completed_at.is_not(None))
    elif status == "todas":
        pass
    else:
        query = query.filter(CustomerReminder.completed_at.is_(None))
    return selected_date, assignee, status, query


def _customer_signup_date(c):
    raw = c.get("fecha_alta_raw") or ""
    if raw:
        parsed = _parse_iso_date(raw[:10])
        if parsed:
            return parsed
    return dt.datetime.now(MADRID_TZ).date()


def _ensure_onboarding_tasks(clientes):
    pending = [c for c in clientes if c.get("estado") in ("activo", "trial") and not c.get("onboarding_hecho")]
    if not pending:
        return
    emails = [c["email_key"] for c in pending]
    existing = {
        row.customer_email
        for row in CustomerReminder.query
        .filter(CustomerReminder.customer_email.in_(emails),
                CustomerReminder.source == ONBOARDING_TASK_SOURCE)
        .all()
    }
    created = False
    for c in pending:
        email = c["email_key"]
        if email in existing:
            continue
        db.session.add(CustomerReminder(
            customer_email=email,
            texto=ONBOARDING_TASK_TEXT,
            due_date=_customer_signup_date(c).isoformat(),
            assignee=ONBOARDING_TASK_ASSIGNEE,
            source=ONBOARDING_TASK_SOURCE,
        ))
        created = True
    if created:
        db.session.commit()


def _bandeja_redirect_target():
    return request.referrer or url_for("bandeja")


def _churn_key(email, fecha):
    return (email or "").lower(), (fecha or "")[:10]


def _churn_reason_map():
    return {_churn_key(row.email, row.fecha): row for row in ChurnReason.query.all()}


def _request_events(rows):
    eventos = []
    for row in rows:
        if row.created_at:
            c = row.created_at
            if c.tzinfo is None:
                c = c.replace(tzinfo=dt.timezone.utc)
            eventos.append({"fecha": c.isoformat(), "email": row.customer_email})
    return eventos


def _clientes_snapshot(snap):
    metas = _meta_map()
    clientes = []
    for c in (snap or {}).get("clientes", []):
        email = (c.get("email_key") or c.get("email") or "").lower()
        if not email:
            continue
        meta = metas.get(email)
        clientes.append({
            "email": email,
            "nombre": c.get("nombre") or c.get("email") or email,
            "whatsapp": (meta.whatsapp if meta else "") or c.get("whatsapp") or "",
            "usuario": (meta.usuario if meta else "") or c.get("usuario") or "",
        })
    return sorted(clientes, key=lambda c: (c["nombre"] or "").lower())


def _ticket_context(ticket):
    status_key = complaint_rules.ticket_status_key(ticket)
    team_key = complaint_rules.team_for_status(status_key)
    comments_count = ticket.comentarios.count() if getattr(ticket, "comentarios", None) is not None else 0
    return {
        "age": complaint_rules.ticket_age(ticket),
        "duration": complaint_rules.ticket_duration(ticket),
        "comments_count": comments_count,
        "status_class": complaint_rules.ticket_status_class(ticket),
        "status_key": status_key,
        "team_key": team_key,
        "team_label": complaint_rules.TEAM_LABELS.get(team_key, team_key),
        "importance_label": complaint_rules.IMPORTANCE_LABELS.get(
            getattr(ticket, "importancia", "") or "media",
            getattr(ticket, "importancia", "") or "Media",
        ),
    }


def _clientes_enriquecidos():
    """Snapshot de producto + origen del AM, cruzado por email."""
    snap = ultimo_snapshot()
    if not snap:
        return None, None
    metas = _meta_map()
    bajas = snap.get("eventos", {}).get("bajas", [])
    for c in snap["clientes"]:
        m = metas.get(c["email_key"])
        c.update(customer_rules.enrich_customer(c, m))
        c["reactivacion"] = customer_rules.reactivation_summary(c, bajas)
        c["origen"] = m.origen if m else "sin_asignar"
        c["origen_label"] = ORIGEN_LABELS.get(c["origen"], c["origen"])
        c["onboarding_hecho"] = bool(m and m.onboarding_hecho)
        c["whatsapp"] = (m.whatsapp if m else "") or c.get("whatsapp") or ""
        c["usuario"] = (m.usuario if m else "") or c.get("usuario") or ""
        if c["estado"] in customer_rules.UNPAID_STATES:
            c["impago"] = customer_rules.unpaid_summary(c)
        c["churn_risk"] = customer_rules.churn_risk_summary(c)
    return snap, metas


def _churn_risk_rows(clientes):
    rows_by_email = {}
    for c in clientes:
        risk = customer_rules.churn_risk_summary(c)
        if risk.get("activo"):
            row = dict(c)
            row["churn_risk"] = risk
            rows_by_email[c["email_key"]] = row

    manuales = (Interaccion.query
                .filter_by(tipo="churn", resuelta=False)
                .order_by(Interaccion.created_at.desc())
                .all())
    clientes_by_email = {c["email_key"]: c for c in clientes}
    for risk in manuales:
        email = (risk.customer_email or "").lower()
        customer = clientes_by_email.get(email)
        if not customer:
            continue
        row = rows_by_email.get(email) or dict(customer)
        manual_summary = {
            "activo": True,
            "tipo": row.get("churn_risk", {}).get("tipo") or "manual",
            "label": row.get("churn_risk", {}).get("label") or "riesgo marcado manualmente",
            "dias": row.get("churn_risk", {}).get("dias"),
            "fecha": row.get("churn_risk", {}).get("fecha", ""),
            "fecha_raw": row.get("churn_risk", {}).get("fecha_raw", ""),
            "manual_texto": risk.texto,
            "created_at_raw": risk.created_at.isoformat() if risk.created_at else "",
        }
        row["churn_risk"] = manual_summary
        rows_by_email[email] = row

    return customer_rules.sort_churn_risk_priority(rows_by_email.values())


# ── Vistas ──────────────────────────────────────────────────────────────────
def _quejas_en(rango_desde, rango_hasta):
    """Cuenta quejas (interacciones tipo=queja) por created_at. Filtra en Python
    para evitar diferencias de timezone entre SQLite y Postgres."""
    n = 0
    for q in Interaccion.query.filter(Interaccion.tipo.in_(complaint_rules.REQUEST_TYPES)).all():
        c = q.created_at
        if c is None:
            continue
        if c.tzinfo is None:
            c = c.replace(tzinfo=dt.timezone.utc)
        if rango_desde <= c < rango_hasta:
            n += 1
    return n


def _emails_base_actual(clientes):
    return {
        (c.get("email_key") or c.get("email") or "").lower()
        for c in clientes
        if c.get("cuenta_activo_recurrente") or c.get("estado") == "trial"
    }


def _trial_emails(clientes):
    return {
        (c.get("email_key") or c.get("email") or "").lower()
        for c in clientes
        if c.get("estado") == "trial"
    }


def _complete_todo_altas_with_current_recurrentes_and_bajas(altas, clientes, bajas):
    emails_con_alta = {(e.get("email") or "").lower() for e in altas}
    completadas = list(altas)
    for c in clientes:
        email = (c.get("email_key") or c.get("email") or "").lower()
        if not email or email in emails_con_alta or not c.get("cuenta_activo_recurrente"):
            continue
        fecha = c.get("fecha_alta_raw")
        if not fecha:
            continue
        completadas.append({"email": email, "fecha": fecha, "origen": c.get("origen", "sin_asignar")})
        emails_con_alta.add(email)
    for baja in bajas:
        email = (baja.get("email") or "").lower()
        if not email or email in emails_con_alta:
            continue
        fecha = baja.get("fecha")
        if not fecha:
            continue
        completadas.append({"email": email, "fecha": fecha, "origen": baja.get("origen", "sin_asignar")})
        emails_con_alta.add(email)
    return completadas


@app.route("/")
@login_required
def index():
    snap, _ = _clientes_enriquecidos()
    if not snap or not snap.get("eventos"):
        return render_template("dashboard.html", snap=snap, origenes=ORIGENES_BASE,
                               presets=metrics.PRESETS)
    metas = _meta_map()
    canal = request.args.get("canal") or None

    altas = metrics.enriquecer(snap["eventos"].get("altas", []), metas)
    trial_emails = _trial_emails(snap["clientes"])
    altas = [e for e in altas if (e.get("email") or "").lower() not in trial_emails]
    bajas = metrics.enriquecer(
        customer_rules.remove_reactivated_cancellations(snap["eventos"].get("bajas", []), snap["clientes"]),
        metas,
    )
    trials = metrics.trial_events(snap["clientes"])
    if request.args.get("preset") == "todo" and not request.args.get("desde") and not request.args.get("hasta"):
        altas = _complete_todo_altas_with_current_recurrentes_and_bajas(altas, snap["clientes"], bajas)
    desde, hasta, label, pdesde, phasta = metrics.resolver_periodo(request.args, eventos=altas + bajas + trials)
    altas_p = metrics.filtrar(altas, desde, hasta, canal)
    bajas_p = metrics.filtrar(bajas, desde, hasta, canal)
    trials_p = metrics.filtrar(trials, desde, hasta, canal)
    altas_prev = metrics.filtrar(altas, pdesde, phasta, canal)
    bajas_prev = metrics.filtrar(bajas, pdesde, phasta, canal)

    pargs = {k: v for k, v in request.args.items()}  # preservar período al navegar
    estado_summary = customer_rules.customer_summary(snap["clientes"])
    northstar = metrics.recurrent_northstar_delta(
        estado_summary["activos_recurrentes"],
        altas_p,
        bajas_p,
    )

    kpis = [
        {"label": "Activos recurrentes", "valor": northstar["valor"], "delta": northstar["delta"],
         "href": url_for("clientes_list", recurrente=1)},
        {"label": "Altas", "valor": len(altas_p), "delta": metrics.delta_pct(len(altas_p), len(altas_prev)),
         "href": url_for("eventos", tipo="altas", **pargs)},
        {"label": "Bajas", "valor": len(bajas_p), "delta": metrics.delta_pct(len(bajas_p), len(bajas_prev)),
         "invertir": True, "href": url_for("bajas_list", **pargs)},
        {"label": "Neto", "valor": len(altas_p) - len(bajas_p),
         "delta": metrics.delta_pct(len(altas_p) - len(bajas_p), len(altas_prev) - len(bajas_prev))},
    ]

    if request.args.get("preset") == "todo" and not request.args.get("desde") and not request.args.get("hasta"):
        clientes_canal = [
            c for c in snap["clientes"]
            if c.get("cuenta_activo_recurrente") or c.get("estado") == "trial"
        ]
        if canal:
            clientes_canal = [c for c in clientes_canal if origen_group_key(c.get("origen")) == canal]
        canal_counts = Counter(origen_group_key(c.get("origen")) for c in clientes_canal)
        canales_titulo = "Base actual por canal"
    else:
        eventos_canal = [
            e for e in altas_p + trials_p
            if origen_group_key(e.get("origen")) != "sin_asignar"
        ]
        canal_counts = metrics.por_canal(eventos_canal)
        canales_titulo = "Altas y trials por canal"
    canales = [(ORIGEN_LABELS.get(k, k), canal_counts.get(k, 0)) for k, _ in ORIGENES_BASE if canal_counts.get(k, 0)]
    serie_altas = metrics.serie_temporal(altas_p, desde, hasta)
    serie_bajas = metrics.serie_temporal(bajas_p, desde, hasta)
    serie_trials = metrics.serie_temporal(trials_p, desde, hasta)
    serie = {
        "labels": serie_altas["labels"],
        "agrupado": serie_altas["agrupado"],
        "altas": serie_altas["valores"],
        "bajas": serie_bajas["valores"],
        "trials": serie_trials["valores"],
    }

    return render_template(
        "dashboard.html", snap=snap, origenes=ORIGENES_BASE, presets=metrics.PRESETS,
        kpis=kpis, label=label, canal=canal, canales=canales, canales_titulo=canales_titulo, serie=serie,
        desde=desde.strftime("%Y-%m-%d"), hasta=(hasta - dt.timedelta(days=1)).strftime("%Y-%m-%d"),
        estado={
            **estado_summary,
            "activos": estado_summary["activos_recurrentes"],
        },
    )


@app.route("/clientes")
@login_required
def clientes_list():
    snap, _ = _clientes_enriquecidos()
    estado = request.args.get("estado") or None
    origen = request.args.get("origen") or None
    tipo = request.args.get("tipo") or None
    recurrente = request.args.get("recurrente") == "1"
    q = (request.args.get("q") or "").strip()
    sort_key = request.args.get("sort") or "cliente"
    if sort_key not in {"cliente", "tipo", "plan", "estado", "atencion", "origen", "alta"}:
        sort_key = "cliente"
    sort_dir = "desc" if request.args.get("dir") == "desc" else "asc"
    titulo = "Clientes"
    if snap:
        snap = dict(snap)
        clientes = customer_rules.filter_customers(
            snap["clientes"], estado=estado, origen=origen, tipo=tipo, q=q,
            recurrente=recurrente,
        )
        clientes = customer_rules.sort_customers(clientes, sort_key=sort_key, direction=sort_dir)
        if recurrente:
            titulo = "Clientes activos recurrentes"
        if estado:
            titulo = {"activo": "Clientes activos", "trial": "Clientes en trial",
                      "impago": "Clientes con impago",
                      "pausado_impago": "Clientes pausados por impago",
                      "inactivo_impago": "Clientes inactivos por impago",
                      "inactivo": "Clientes inactivos"}.get(estado, titulo)
        if tipo:
            titulo = customer_rules.TYPE_LABELS.get(tipo, titulo)
        if origen == "sin_asignar":
            titulo = "Clientes sin origen asignado"
        snap["clientes"] = clientes
    resumen = customer_rules.customer_summary(snap["clientes"]) if snap else {}
    base_args = {
        "estado": estado,
        "origen": origen,
        "tipo": tipo,
        "q": q,
        "sort": sort_key,
        "dir": sort_dir,
    }
    if recurrente:
        base_args["recurrente"] = 1
    base_args = {k: v for k, v in base_args.items() if v not in (None, "", False)}
    sort_links = {}
    for key in ("cliente", "tipo", "plan", "estado", "atencion", "origen", "alta"):
        args = dict(base_args)
        args["sort"] = key
        args["dir"] = "desc" if sort_key == key and sort_dir == "asc" else "asc"
        sort_links[key] = url_for("clientes_list", **args)
    return render_template("clientes.html", snap=snap, origenes=ORIGENES,
                           tipos=customer_rules.TYPE_OPTIONS, resumen=resumen,
                           titulo=titulo, estado=estado, origen=origen,
                           tipo=tipo, q=q, recurrente=recurrente,
                           sort=sort_key, dir=sort_dir, sort_links=sort_links)


@app.route("/eventos")
@login_required
def eventos():
    """Lista de altas o bajas del período (cada una es un cliente con su fecha)."""
    tipo = request.args.get("tipo", "altas")
    tipo = tipo if tipo in ("altas", "bajas") else "altas"
    snap = ultimo_snapshot()
    if not snap or not snap.get("eventos"):
        return redirect(url_for("index"))
    metas = _meta_map()
    canal = request.args.get("canal") or None
    raw_events = snap["eventos"].get(tipo, [])
    if tipo == "bajas":
        raw_events = customer_rules.remove_reactivated_cancellations(raw_events, snap["clientes"])
    desde, hasta, label, _, _ = metrics.resolver_periodo(request.args, eventos=raw_events)
    evs = metrics.enriquecer(raw_events, metas)
    evs = metrics.filtrar(evs, desde, hasta, canal)
    nombre_por_email = {c["email_key"]: c["nombre"] for c in snap["clientes"]}
    filas = sorted([{
        "email": e.get("email", ""),
        "nombre": nombre_por_email.get((e.get("email") or "").lower(), e.get("email") or "—"),
        "plan": e.get("plan", "?"),
        "origen_label": ORIGEN_LABELS.get(e.get("origen"), e.get("origen")),
        "fecha": (e.get("fecha") or "")[:10],
        "es_cliente": (e.get("email") or "").lower() in nombre_por_email,
    } for e in evs], key=lambda x: x["fecha"], reverse=True)
    return render_template("eventos.html", filas=filas, tipo=tipo, label=label)


@app.route("/bajas")
@login_required
def bajas_list():
    snap = ultimo_snapshot()
    if not snap or not snap.get("eventos"):
        return redirect(url_for("index"))
    metas = _meta_map()
    canal = request.args.get("canal") or None
    raw_bajas = customer_rules.remove_reactivated_cancellations(
        snap["eventos"].get("bajas", []),
        snap["clientes"],
    )
    desde, hasta, label, _, _ = metrics.resolver_periodo(request.args, eventos=raw_bajas)
    bajas = metrics.enriquecer(raw_bajas, metas)
    bajas = metrics.filtrar(bajas, desde, hasta, canal)
    nombre_por_email = {c["email_key"]: c["nombre"] for c in snap["clientes"]}
    reasons = _churn_reason_map()
    filas = []
    for e in bajas:
        email = (e.get("email") or "").lower()
        fecha = (e.get("fecha") or "")[:10]
        filas.append({
            "email": e.get("email", ""),
            "nombre": nombre_por_email.get(email, e.get("email") or "-"),
            "plan": e.get("plan", "?"),
            "origen_label": ORIGEN_LABELS.get(e.get("origen"), e.get("origen")),
            "fecha": fecha,
            "reason": reasons.get(_churn_key(email, fecha)),
            "es_cliente": email in nombre_por_email,
        })
    filas = sorted(filas, key=lambda x: x["fecha"], reverse=True)
    con_motivo = sum(1 for f in filas if f["reason"] and f["reason"].motivo)
    return render_template(
        "bajas.html", filas=filas, label=label, presets=metrics.PRESETS,
        origenes=ORIGENES, canal=canal, motivos=CHURN_REASON_OPTIONS,
        con_motivo=con_motivo,
        desde=desde.strftime("%Y-%m-%d"),
        hasta=(hasta - dt.timedelta(days=1)).strftime("%Y-%m-%d"),
    )


@app.route("/bajas/motivo", methods=["POST"])
@login_required
def guardar_motivo_baja():
    email = (request.form.get("email") or "").lower()
    fecha = (request.form.get("fecha") or "")[:10]
    motivo = request.form.get("motivo") or ""
    detalle = (request.form.get("detalle") or "").strip()
    if email and fecha:
        row = ChurnReason.query.filter_by(email=email, fecha=fecha).first()
        if not row:
            row = ChurnReason(email=email, fecha=fecha)
            db.session.add(row)
        row.motivo = motivo
        row.detalle = detalle
        db.session.commit()
        flash("Motivo de baja guardado", "ok")
    return redirect(request.referrer or url_for("bajas_list"))


@app.route("/quejas")
@app.route("/solicitudes")
@login_required
def quejas_list():
    todas = (Interaccion.query
             .filter(Interaccion.tipo.in_(complaint_rules.REQUEST_TYPES))
             .order_by(Interaccion.created_at.desc()).all())
    desde, hasta, label, _, _ = metrics.resolver_periodo(request.args, eventos=_request_events(todas))
    period_events = []
    period_requests = []
    for row in todas:
        eventos = _request_events([row])
        if eventos and metrics.filtrar(eventos, desde, hasta):
            period_events.extend(eventos)
            period_requests.append(row)
    abiertas = (Interaccion.query
                .filter(Interaccion.tipo.in_(complaint_rules.REQUEST_TYPES), Interaccion.resuelta.is_(False))
                .order_by(Interaccion.created_at.desc()).all())
    abiertas = customer_rules.sort_oldest_first(abiertas)
    resueltas = (Interaccion.query
                 .filter(Interaccion.tipo.in_(complaint_rules.REQUEST_TYPES), Interaccion.resuelta.is_(True))
                 .order_by(Interaccion.created_at.desc()).limit(50).all())
    snap = ultimo_snapshot() or {}
    nombre_por_email = {c["email_key"]: c["nombre"] for c in snap.get("clientes", [])}
    clientes = _clientes_snapshot(snap)
    categorias = _complaint_categories()
    category_map = _complaint_category_map()
    stats = complaint_rules.complaint_stats(abiertas + resueltas)
    request_stats = complaint_rules.request_stats(abiertas + resueltas)
    period_stats = complaint_rules.request_stats(period_requests)
    serie_solicitudes = metrics.serie_temporal(period_events, desde, hasta)
    return render_template("quejas.html", abiertas=abiertas, resueltas=resueltas,
                           nombres=nombre_por_email, categorias=categorias,
                           category_map=category_map, stats=stats,
                           request_stats=request_stats,
                           period_stats=period_stats,
                           serie_solicitudes=serie_solicitudes,
                           clientes=clientes,
                           presets=metrics.PRESETS, label=label,
                           equipos=complaint_rules.TEAM_OPTIONS,
                           estados_solicitud=complaint_rules.REQUEST_STATUS_OPTIONS,
                           team_labels=complaint_rules.TEAM_LABELS,
                           status_labels=complaint_rules.REQUEST_STATUS_LABELS,
                           importancias=complaint_rules.IMPORTANCE_OPTIONS,
                           importance_labels=complaint_rules.IMPORTANCE_LABELS,
                           ticket_context=_ticket_context,
                           category_label=complaint_rules.category_label)


@app.route("/solicitudes/nueva", methods=["POST"])
@login_required
def add_solicitud_directa():
    snap = ultimo_snapshot() or {}
    clientes = _clientes_snapshot(snap)
    valid_emails = {c["email"] for c in clientes}
    customer_email = (request.form.get("customer_email") or "").lower()
    texto = (request.form.get("texto") or "").strip()
    tipo = request.form.get("tipo") if request.form.get("tipo") in complaint_rules.REQUEST_TYPES else "solicitud"
    estado_gestion = "abierta"
    equipo = complaint_rules.team_for_status(estado_gestion)

    if not clientes:
        flash("No hay clientes cargados para crear solicitudes", "error")
    elif customer_email not in valid_emails:
        flash("Selecciona un cliente valido", "error")
    elif not texto:
        flash("El detalle es obligatorio", "error")
    else:
        db.session.add(Interaccion(
            customer_email=customer_email,
            tipo=tipo,
            texto=texto,
            agente=None,
            categoria=request.form.get("categoria", ""),
            equipo=equipo,
            estado_gestion=estado_gestion,
            importancia=request.form.get("importancia") or "media",
            resuelta=False,
        ))
        db.session.commit()
        flash("Solicitud creada", "ok")
    return redirect(url_for("quejas_list"))


@app.route("/queja/<int:qid>/resolver", methods=["POST"])
@login_required
def resolver_queja(qid):
    q = db.session.get(Interaccion, qid)
    if q and complaint_rules.is_customer_request(q):
        q.resuelta = True
        q.estado_gestion = "resuelta"
        q.resolved_at = dt.datetime.now(dt.timezone.utc)
        db.session.commit()
        flash("Solicitud marcada como resuelta", "ok")
    return redirect(request.referrer or url_for("quejas_list"))


@app.route("/solicitudes/<int:qid>/reabrir", methods=["POST"])
@login_required
def reabrir_ticket(qid):
    ticket = db.session.get(Interaccion, qid)
    if ticket and complaint_rules.is_customer_request(ticket):
        ticket.resuelta = False
        ticket.estado_gestion = "abierta"
        ticket.equipo = complaint_rules.team_for_status("abierta")
        ticket.resolved_at = None
        db.session.commit()
        flash("Ticket reabierto", "ok")
    return redirect(request.referrer or url_for("ticket_detail", qid=qid))


@app.route("/queja/<int:qid>/categoria", methods=["POST"])
@login_required
def set_queja_categoria(qid):
    q = db.session.get(Interaccion, qid)
    if q and complaint_rules.is_customer_request(q):
        q.categoria = request.form.get("categoria", "")
        db.session.commit()
        flash("Solicitud categorizada", "ok")
    return redirect(request.referrer or url_for("quejas_list"))


@app.route("/queja/<int:qid>/gestion", methods=["POST"])
@login_required
def set_queja_gestion(qid):
    q = db.session.get(Interaccion, qid)
    if q and complaint_rules.is_customer_request(q):
        estado = complaint_rules.normalize_status(request.form.get("estado_gestion", "abierta"))
        q.estado_gestion = estado
        q.equipo = complaint_rules.team_for_status(estado)
        q.importancia = request.form.get("importancia") or q.importancia or "media"
        q.resuelta = q.estado_gestion == "resuelta"
        q.resolved_at = dt.datetime.now(dt.timezone.utc) if q.resuelta else None
        db.session.commit()
        flash("Gestion actualizada", "ok")
    return redirect(request.referrer or url_for("quejas_list"))


@app.route("/solicitudes/<int:qid>/eliminar", methods=["POST"])
@login_required
def eliminar_ticket(qid):
    ticket = db.session.get(Interaccion, qid)
    if ticket and complaint_rules.is_customer_request(ticket) and not ticket.resuelta:
        db.session.delete(ticket)
        db.session.commit()
        flash("Ticket eliminado", "ok")
    return redirect(url_for("quejas_list"))


@app.route("/solicitudes/<int:qid>")
@login_required
def ticket_detail(qid):
    ticket = db.session.get(Interaccion, qid)
    if not ticket or not complaint_rules.is_customer_request(ticket):
        abort(404)
    snap = ultimo_snapshot() or {}
    nombres = {c["email_key"]: c["nombre"] for c in snap.get("clientes", [])}
    comments = ticket.comentarios.order_by(TicketComment.created_at.asc()).all()
    return render_template(
        "ticket.html",
        ticket=ticket,
        comments=comments,
        nombre=nombres.get(ticket.customer_email, ticket.customer_email),
        categorias=_complaint_categories(),
        category_map=_complaint_category_map(),
        category_label=complaint_rules.category_label,
        estados_solicitud=complaint_rules.REQUEST_STATUS_OPTIONS,
        status_labels=complaint_rules.REQUEST_STATUS_LABELS,
        importancias=complaint_rules.IMPORTANCE_OPTIONS,
        importance_labels=complaint_rules.IMPORTANCE_LABELS,
        comment_authors=complaint_rules.COMMENT_AUTHOR_OPTIONS,
        task_assignees=TASK_ASSIGNEE_OPTIONS,
        task_default_due_date=dt.datetime.now(MADRID_TZ).date().isoformat(),
        ctx=_ticket_context(ticket),
        team_labels=complaint_rules.TEAM_LABELS,
    )


@app.route("/solicitudes/<int:qid>/tareas", methods=["POST"])
@login_required
def add_ticket_task(qid):
    ticket = db.session.get(Interaccion, qid)
    if not ticket or not complaint_rules.is_customer_request(ticket):
        abort(404)
    if ticket.resuelta:
        flash("El ticket ya esta resuelto; reabrilo antes de crear una tarea", "error")
        return redirect(url_for("ticket_detail", qid=qid))

    texto = (request.form.get("texto") or "").strip()
    due = _parse_iso_date(request.form.get("due_date"))
    assignee = (request.form.get("assignee") or "").strip()
    if not texto or not due or assignee not in TASK_ASSIGNEE_VALUES:
        flash("Completa titulo, fecha y asignado de la tarea", "error")
        return redirect(url_for("ticket_detail", qid=qid))

    db.session.add(CustomerReminder(
        customer_email=ticket.customer_email,
        texto=f"Ticket #{ticket.id} · {texto}",
        due_date=due.isoformat(),
        assignee=assignee,
        source="ticket",
    ))
    db.session.commit()
    flash("Tarea creada desde ticket", "ok")
    return redirect(url_for("ticket_detail", qid=qid))


@app.route("/solicitudes/<int:qid>/comentarios", methods=["POST"])
@login_required
def add_ticket_comment(qid):
    ticket = db.session.get(Interaccion, qid)
    texto = (request.form.get("texto") or "").strip()
    agente = request.form.get("agente") or ""
    if not ticket or not complaint_rules.is_customer_request(ticket):
        abort(404)
    if agente not in complaint_rules.COMMENT_AUTHOR_VALUES:
        flash("Selecciona quien deja el comentario", "error")
    elif texto:
        db.session.add(TicketComment(
            interaccion_id=ticket.id,
            texto=texto,
            agente=agente,
        ))
        db.session.commit()
        flash("Comentario agregado", "ok")
    return redirect(url_for("ticket_detail", qid=qid))


@app.route("/quejas/categorias", methods=["POST"])
@login_required
def add_queja_categoria():
    label = (request.form.get("label") or "").strip()
    if label:
        key = complaint_rules.category_key(label)
        if key and not db.session.get(ComplaintCategory, key):
            db.session.add(ComplaintCategory(key=key, label=label))
            db.session.commit()
            flash("Categoria agregada", "ok")
    return redirect(url_for("quejas_list"))


@app.route("/quejas/categorias/<key>", methods=["POST"])
@login_required
def update_queja_categoria(key):
    category = db.session.get(ComplaintCategory, key)
    if category:
        action = request.form.get("action", "rename")
        if action == "deactivate":
            category.activa = False
            flash("Categoria desactivada", "ok")
        else:
            label = (request.form.get("label") or "").strip()
            if label:
                category.label = label
                flash("Categoria actualizada", "ok")
        db.session.commit()
    return redirect(url_for("quejas_list"))


def _message_categories(active_only=True):
    query = MessageCategory.query
    if active_only:
        query = query.filter_by(activa=True)
    return query.order_by(MessageCategory.label.asc()).all()


def _message_category_map():
    return {c.key: c.label for c in MessageCategory.query.all()}


@app.route("/mensajes")
@login_required
def mensajes_list():
    q = (request.args.get("q") or "").strip()
    category = request.args.get("categoria") or ""
    rows = (MessageTemplate.query.filter_by(activo=True)
            .order_by(MessageTemplate.updated_at.desc(), MessageTemplate.id.desc()).all())
    rows = message_rules.filter_messages(rows, q=q, category=category)
    return render_template("mensajes.html", mensajes=rows, categorias=_message_categories(),
                           category_map=_message_category_map(), q=q, categoria=category,
                           tag_list=message_rules.tag_list)


@app.route("/mensajes", methods=["POST"])
@login_required
def add_mensaje():
    titulo = (request.form.get("titulo") or "").strip()
    cuerpo = (request.form.get("cuerpo") or "").strip()
    if titulo and cuerpo:
        db.session.add(MessageTemplate(
            titulo=titulo,
            cuerpo=cuerpo,
            categoria_key=request.form.get("categoria_key") or "bienvenida",
            tags=message_rules.parse_tags(request.form.get("tags")),
        ))
        db.session.commit()
        flash("Mensaje agregado", "ok")
    return redirect(url_for("mensajes_list"))


@app.route("/mensajes/<int:mid>", methods=["POST"])
@login_required
def update_mensaje(mid):
    msg = db.session.get(MessageTemplate, mid)
    if msg:
        action = request.form.get("action", "save")
        if action == "archive":
            msg.activo = False
            flash("Mensaje archivado", "ok")
        else:
            msg.titulo = (request.form.get("titulo") or "").strip()
            msg.cuerpo = (request.form.get("cuerpo") or "").strip()
            msg.categoria_key = request.form.get("categoria_key") or "bienvenida"
            msg.tags = message_rules.parse_tags(request.form.get("tags"))
            flash("Mensaje actualizado", "ok")
        db.session.commit()
    return redirect(url_for("mensajes_list"))


@app.route("/mensajes/categorias", methods=["POST"])
@login_required
def add_mensaje_categoria():
    label = (request.form.get("label") or "").strip()
    if label:
        key = message_rules.slugify(label)
        if key and not db.session.get(MessageCategory, key):
            db.session.add(MessageCategory(key=key, label=label))
            db.session.commit()
            flash("Categoria agregada", "ok")
    return redirect(url_for("mensajes_list"))


def _apply_colab_creator_form(row):
    row.nombre = (request.form.get("nombre") or "").strip()
    row.contacto = (request.form.get("contacto") or "").strip()
    row.red = (request.form.get("red") or "").strip()
    row.estado = request.form.get("estado") or "idea"
    row.tipo = request.form.get("tipo") or "free"
    row.idea = (request.form.get("idea") or "").strip()
    row.detalles = (request.form.get("detalles") or "").strip()
    row.duracion = (request.form.get("duracion") or "").strip()
    row.fecha_inicio = (request.form.get("fecha_inicio") or "").strip()
    row.fecha_fin = (request.form.get("fecha_fin") or "").strip()
    row.proxima_accion = (request.form.get("proxima_accion") or "").strip()
    row.responsable = (request.form.get("responsable") or "").strip()


@app.route("/colabs")
@login_required
def colabs_list():
    snap, _ = _clientes_enriquecidos()
    rows = []
    resumen = {"total": 0, "free": 0, "descuento": 0, "revision": 0}
    if snap:
        rows = [c for c in snap["clientes"] if (c.get("colab") or {}).get("es_colab")]
        rows = sorted(
            rows,
            key=lambda c: (
                0 if (c.get("colab") or {}).get("revision_pendiente") else 1,
                -((c.get("colab") or {}).get("dias_revision") or 0),
                (c.get("nombre") or "").lower(),
            ),
        )
        resumen = {
            "total": len(rows),
            "free": sum(1 for c in rows if c.get("tipo_cliente_key") == "free_colab"),
            "descuento": sum(1 for c in rows if c.get("tipo_cliente_key") == "colab_descuento"),
            "revision": sum(1 for c in rows if (c.get("colab") or {}).get("revision_pendiente")),
        }
    creators = (ColabCreator.query.filter_by(activo=True)
                .order_by(ColabCreator.updated_at.desc(), ColabCreator.id.desc()).all())
    creator_stats = {
        "total": len(creators),
        "activos": sum(1 for c in creators if c.estado == "activo"),
        "negociando": sum(1 for c in creators if c.estado == "negociando"),
        "proximas": sum(1 for c in creators if c.proxima_accion),
    }
    return render_template(
        "colabs.html", snap=snap, colabs=rows, resumen=resumen,
        creators=creators, creator_stats=creator_stats,
        creator_status=COLAB_CREATOR_STATUS,
        creator_status_labels=COLAB_CREATOR_STATUS_LABELS,
        creator_types=COLAB_CREATOR_TYPES,
        creator_type_labels=COLAB_CREATOR_TYPE_LABELS,
    )


@app.route("/colabs/creadores", methods=["POST"])
@login_required
def add_colab_creator():
    row = ColabCreator()
    _apply_colab_creator_form(row)
    if row.nombre:
        db.session.add(row)
        db.session.commit()
        flash("Creador agregado a colabs", "ok")
    return redirect(url_for("colabs_list"))


@app.route("/colabs/creadores/<int:cid>", methods=["POST"])
@login_required
def update_colab_creator(cid):
    row = db.session.get(ColabCreator, cid)
    if row:
        if request.form.get("action") == "archive":
            row.activo = False
            flash("Creador archivado", "ok")
        else:
            _apply_colab_creator_form(row)
            flash("Colab actualizada", "ok")
        db.session.commit()
    return redirect(url_for("colabs_list"))


@app.route("/bandeja")
@login_required
def bandeja():
    snap, _ = _clientes_enriquecidos()
    pendientes = {"onboarding": [], "impago": [], "trial": [], "churn": []}
    if snap:
        for c in snap["clientes"]:
            if c["estado"] in customer_rules.UNPAID_STATES:
                pendientes["impago"].append(c)
            elif c["estado"] == "trial":
                pendientes["trial"].append(c)
            if c["estado"] in ("activo", "trial") and not c["onboarding_hecho"]:
                pendientes["onboarding"].append(c)
        pendientes["churn"] = _churn_risk_rows(snap["clientes"])
    pendientes["impago"] = customer_rules.sort_unpaid_priority(pendientes["impago"])
    pendientes["trial"] = sorted(
        pendientes["trial"],
        key=lambda c: (((c.get("trial") or {}).get("fecha_raw") or "9999"), (c.get("nombre") or "").lower()),
    )
    clientes = snap["clientes"] if snap else []
    _ensure_onboarding_tasks(clientes)
    nombre_por_email = {c["email_key"]: c["nombre"] for c in clientes}
    selected_date, assignee, status, task_query = _task_query_from_request()
    task_rows = task_query.order_by(CustomerReminder.due_date.asc(), CustomerReminder.created_at.asc()).all()
    task_groups = _task_groups(task_rows, selected_date, nombre_por_email)
    task_total = sum(len(v) for v in task_groups.values())
    return render_template("bandeja.html", pendientes=pendientes,
                           nombres=nombre_por_email,
                           recordatorios=[item for group in task_groups.values() for item in group],
                           task_groups=task_groups,
                           selected_date=selected_date.isoformat(),
                           selected_assignee=assignee,
                           selected_status=status,
                           task_assignees=TASK_ASSIGNEE_OPTIONS,
                           task_total=task_total,
                           task_customer_options=[(c["email_key"], c["nombre"]) for c in clientes])


@app.route("/tareas", methods=["GET"])
@login_required
def tareas_list():
    return redirect(url_for("bandeja", **request.args.to_dict(flat=True)))


@app.route("/tareas", methods=["POST"])
@login_required
def add_tarea():
    snap = ultimo_snapshot()
    customer_email = (request.form.get("customer_email") or "").strip().lower()
    valid_customers = {c.get("email_key") for c in snap.get("clientes", [])} if snap else set()
    if customer_email and customer_email not in valid_customers:
        flash("El cliente elegido no es valido", "error")
        return redirect(url_for("bandeja"))
    texto = (request.form.get("texto") or "").strip()
    due = _parse_iso_date(request.form.get("due_date"))
    assignee = (request.form.get("assignee") or "").strip()
    if not texto or not due or assignee not in TASK_ASSIGNEE_VALUES:
        flash("Completa titulo, fecha y asignado de la tarea", "error")
        return redirect(url_for("bandeja"))
    db.session.add(CustomerReminder(
        customer_email=customer_email,
        texto=texto,
        due_date=due.isoformat(),
        assignee=assignee,
        source="",
    ))
    db.session.commit()
    flash("Tarea creada", "ok")
    return redirect(url_for("bandeja", date=due.isoformat(), assignee=assignee))


@app.route("/clientes/marcar-bienvenidos", methods=["POST"])
@login_required
def marcar_bienvenidos():
    """Backfill: marca a todos los clientes actuales como ya onboardeados.
    El onboarding pendiente aplica a los nuevos de ahora en más."""
    snap = ultimo_snapshot()
    n = 0
    if snap:
        for c in snap["clientes"]:
            meta = _get_or_create_meta(c["email_key"])
            if not meta.onboarding_hecho:
                meta.onboarding_hecho = True
                n += 1
            for task in CustomerReminder.query.filter_by(
                customer_email=c["email_key"],
                source=ONBOARDING_TASK_SOURCE,
                completed_at=None,
            ).all():
                task.completed_at = dt.datetime.now(dt.timezone.utc)
        db.session.commit()
    flash(f"{n} clientes marcados con bienvenida hecha", "ok")
    return redirect(request.referrer or url_for("bandeja"))


@app.route("/sync", methods=["POST"])
@login_required
def sync():
    try:
        refrescar_snapshot()
        flash("Datos actualizados", "ok")
    except Exception as e:
        flash(f"No se pudo actualizar: {e}", "error")
    return redirect(request.referrer or url_for("index"))


@app.route("/cliente/<path:email>")
@login_required
def cliente(email):
    snap = ultimo_snapshot()
    if not snap:
        return redirect(url_for("index"))
    email_key = email.lower()
    metas = _meta_map()
    bajas = snap.get("eventos", {}).get("bajas", [])
    for row in snap["clientes"]:
        m = metas.get(row["email_key"])
        row.update(customer_rules.enrich_customer(row, m))
        row["reactivacion"] = customer_rules.reactivation_summary(row, bajas)
        row["churn_risk"] = customer_rules.churn_risk_summary(row)
    c = next((x for x in snap["clientes"] if x["email_key"] == email_key), None)
    if not c:
        abort(404)
    meta = _get_or_create_meta(email_key)
    salud = salud_de_cuentas(c.get("account_ids", []))
    interacciones = (Interaccion.query
                     .filter_by(customer_email=email_key)
                     .order_by(Interaccion.created_at.desc()).all())
    recordatorios_activos = (CustomerReminder.query
                             .filter_by(customer_email=email_key, completed_at=None)
                             .order_by(CustomerReminder.due_date.asc(), CustomerReminder.created_at.asc()).all())
    recordatorios_completados = (CustomerReminder.query
                                 .filter(CustomerReminder.customer_email == email_key,
                                         CustomerReminder.completed_at.is_not(None))
                                 .order_by(CustomerReminder.completed_at.desc()).limit(5).all())
    quejas_abiertas = [i for i in interacciones if complaint_rules.is_customer_request(i) and not i.resuelta]
    churn_abiertos = [i for i in interacciones if i.tipo == "churn" and not i.resuelta]
    atencion = {
        "impago": customer_rules.unpaid_summary(c) if c.get("estado") in customer_rules.UNPAID_STATES else None,
        "quejas_abiertas": len(quejas_abiertas),
        "churn": c.get("churn_risk") if (c.get("churn_risk") or {}).get("activo") else None,
        "churn_manual": len(churn_abiertos),
        "trial": c.get("trial") if c.get("estado") == "trial" else None,
        "onboarding_pendiente": c.get("estado") in ("activo", "trial") and not meta.onboarding_hecho,
    }
    origen_base = "instagram" if meta.origen in INSTAGRAM_ORIGEN_KEYS else meta.origen
    instagram_variante = meta.origen if meta.origen in INSTAGRAM_ORIGEN_KEYS else "instagram"
    return render_template("ficha.html", c=c, meta=meta, salud=salud,
                           interacciones=interacciones, origenes=ORIGENES_BASE,
                           origen_base=origen_base,
                           instagram_variante=instagram_variante,
                           instagram_variants=INSTAGRAM_VARIANTS,
                           planes=customer_rules.PLAN_OPTIONS,
                           estados=customer_rules.STATUS_OPTIONS,
                           tipos=customer_rules.TYPE_OPTIONS,
                           atencion=atencion, categorias=_complaint_categories(),
                           equipos=complaint_rules.TEAM_OPTIONS,
                           estados_solicitud=complaint_rules.REQUEST_STATUS_OPTIONS,
                           importancias=complaint_rules.IMPORTANCE_OPTIONS,
                           task_assignees=TASK_ASSIGNEE_OPTIONS,
                           category_map=_complaint_category_map(),
                           category_label=complaint_rules.category_label,
                           recordatorios_activos=[_reminder_view(r) for r in recordatorios_activos],
                           recordatorios_completados=[_reminder_view(r) for r in recordatorios_completados])


@app.route("/cliente/<path:email>/origen", methods=["POST"])
@login_required
def set_origen(email):
    meta = _get_or_create_meta(email.lower())
    origen = request.form.get("origen_base") or request.form.get("origen") or "sin_asignar"
    if origen == "instagram":
        origen = request.form.get("instagram_variante") or "instagram"
    if origen not in ORIGEN_LABELS:
        origen = "sin_asignar"
    meta.origen = origen
    meta.referido_por = ((request.form.get("referido_por") or "").strip().lower() or None) if origen == "referido" else None
    db.session.commit()
    flash("Origen actualizado", "ok")
    return redirect(url_for("cliente", email=email))


@app.route("/cliente/<path:email>/suscripcion", methods=["POST"])
@login_required
def set_suscripcion(email):
    meta = _get_or_create_meta(email.lower())
    meta.manual_plan = request.form.get("manual_plan", "")
    meta.manual_estado = request.form.get("manual_estado", "")
    meta.tipo_cliente = request.form.get("tipo_cliente", "")
    meta.colab_descuento = (request.form.get("colab_descuento") or "").strip()
    meta.colab_acuerdo = (request.form.get("colab_acuerdo") or "").strip()
    meta.colab_inicio = (request.form.get("colab_inicio") or "").strip()
    meta.colab_revision = (request.form.get("colab_revision") or "").strip()
    db.session.commit()
    flash("Suscripcion actualizada", "ok")
    return redirect(url_for("cliente", email=email))


@app.route("/cliente/<path:email>/contacto", methods=["POST"])
@login_required
def set_contacto_cliente(email):
    meta = _get_or_create_meta(email.lower())
    meta.whatsapp = (request.form.get("whatsapp") or "").strip()
    meta.usuario = (request.form.get("usuario") or "").strip()
    db.session.commit()
    flash("Contacto actualizado", "ok")
    return redirect(url_for("cliente", email=email))


@app.route("/cliente/<path:email>/interaccion", methods=["POST"])
@login_required
def add_interaccion(email):
    texto = (request.form.get("texto") or "").strip()
    tipo = request.form.get("tipo", "nota")
    if texto:
        estado = complaint_rules.normalize_status(request.form.get("estado_gestion", "abierta"))
        db.session.add(Interaccion(
            customer_email=email.lower(),
            tipo=tipo,
            texto=texto,
            agente=None,
            categoria=request.form.get("categoria", "") if tipo in complaint_rules.REQUEST_TYPES else "",
            equipo=complaint_rules.team_for_status(estado) if tipo in complaint_rules.REQUEST_TYPES else "cs",
            estado_gestion=estado if tipo in complaint_rules.REQUEST_TYPES else "",
            importancia=request.form.get("importancia", "media") if tipo in complaint_rules.REQUEST_TYPES else "media",
        ))
        db.session.commit()
        flash("Nota agregada", "ok")
    return redirect(url_for("cliente", email=email))


@app.route("/cliente/<path:email>/recordatorios", methods=["POST"])
@login_required
def add_recordatorio(email):
    email_key = email.lower()
    texto = (request.form.get("texto") or "").strip()
    due = _parse_iso_date(request.form.get("due_date"))
    assignee = (request.form.get("assignee") or "").strip()
    if not texto or not due:
        flash("Completa fecha y detalle de la tarea", "error")
        return redirect(url_for("cliente", email=email_key))
    if assignee and assignee not in TASK_ASSIGNEE_VALUES:
        flash("El asignado no es valido", "error")
        return redirect(url_for("cliente", email=email_key))
    db.session.add(CustomerReminder(
        customer_email=email_key,
        texto=texto,
        due_date=due.isoformat(),
        assignee=assignee,
        source="",
    ))
    db.session.commit()
    flash("Tarea creada", "ok")
    return redirect(url_for("cliente", email=email_key))


@app.route("/recordatorios/<int:reminder_id>/completar", methods=["POST"])
@login_required
def complete_recordatorio(reminder_id):
    reminder = db.session.get(CustomerReminder, reminder_id)
    if not reminder:
        abort(404)
    if not reminder.completed_at:
        reminder.completed_at = dt.datetime.now(dt.timezone.utc)
        if reminder.source == ONBOARDING_TASK_SOURCE and reminder.customer_email:
            meta = _get_or_create_meta(reminder.customer_email)
            meta.onboarding_hecho = True
        db.session.commit()
        flash("Tarea completada", "ok")
    return redirect(request.referrer or url_for("bandeja"))


@app.route("/recordatorios/<int:reminder_id>/editar", methods=["POST"])
@login_required
def edit_recordatorio(reminder_id):
    reminder = db.session.get(CustomerReminder, reminder_id)
    if not reminder:
        abort(404)
    redirect_target = _bandeja_redirect_target()
    if reminder.completed_at:
        flash("La tarea completada no se puede editar", "error")
        return redirect(redirect_target)

    assignee = (request.form.get("assignee") or "").strip()
    if assignee and assignee not in TASK_ASSIGNEE_VALUES:
        flash("El asignado no es valido", "error")
        return redirect(redirect_target)

    if reminder.source == ONBOARDING_TASK_SOURCE:
        reminder.assignee = assignee
        db.session.commit()
        flash("Responsable actualizado", "ok")
        return redirect(redirect_target)

    snap = ultimo_snapshot()
    valid_customers = {c.get("email_key") for c in snap.get("clientes", [])} if snap else set()
    customer_email = (request.form.get("customer_email") or "").strip().lower()
    if customer_email and customer_email not in valid_customers:
        flash("El cliente elegido no es valido", "error")
        return redirect(redirect_target)

    texto = (request.form.get("texto") or "").strip()
    due = _parse_iso_date(request.form.get("due_date"))
    if not texto or not due:
        flash("Completa titulo y fecha de la tarea", "error")
        return redirect(redirect_target)

    reminder.texto = texto
    reminder.due_date = due.isoformat()
    reminder.assignee = assignee
    reminder.customer_email = customer_email
    db.session.commit()
    flash("Tarea actualizada", "ok")
    return redirect(redirect_target)


@app.route("/cliente/<path:email>/onboarding", methods=["POST"])
@login_required
def toggle_onboarding(email):
    meta = _get_or_create_meta(email.lower())
    meta.onboarding_hecho = not meta.onboarding_hecho
    db.session.commit()
    return redirect(url_for("cliente", email=email))


@app.route("/estadisticas")
@login_required
def estadisticas():
    snap, _ = _clientes_enriquecidos()
    por_origen, por_mes = Counter(), defaultdict(Counter)
    if snap:
        for c in snap["clientes"]:
            por_origen[c["origen"]] += 1
            raw = c.get("fecha_alta_raw") or ""
            if raw:
                por_mes[raw[:7]][c["origen"]] += 1
    stats = {
        "por_origen": [(ORIGEN_LABELS.get(k, k), por_origen.get(k, 0)) for k, _ in ORIGENES],
        "meses": sorted(por_mes.keys()),
        "por_mes": por_mes,
    }
    return render_template("estadisticas.html", snap=snap, stats=stats, origenes=ORIGENES)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
