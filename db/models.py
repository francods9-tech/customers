import datetime as dt
from db import db

# Canales de origen. La clave se guarda en DB; el label se muestra en UI.
ORIGENES = [
    ("sin_asignar", "Sin asignar"),
    ("referido", "Referidos"),
    ("email", "Email"),
    ("instagram", "Instagram"),
    ("ig_en", "Instagram inglés"),
    ("ig_es", "Instagram español"),
    ("ig_pt", "Instagram portugués"),
    ("whatsapp", "WhatsApp"),
    ("telegram", "Telegram"),
    ("xbiz", "XBIZ"),
    ("sky", "Sky"),
    ("reactivacion", "Reactivacion"),
    ("directo", "No se sabe (directo)"),
]
ORIGEN_LABELS = dict(ORIGENES)
ORIGEN_KEYS = [k for k, _ in ORIGENES]
INSTAGRAM_ORIGEN_KEYS = {"instagram", "ig_en", "ig_es", "ig_pt"}
INSTAGRAM_VARIANTS = [
    ("instagram", "Sin idioma"),
    ("ig_en", "Ingles"),
    ("ig_es", "Español"),
    ("ig_pt", "Portugues"),
]
ORIGENES_BASE = [(k, label) for k, label in ORIGENES if k not in {"ig_en", "ig_es", "ig_pt"}]


def origen_group_key(origen):
    return "instagram" if origen in INSTAGRAM_ORIGEN_KEYS else (origen or "sin_asignar")


def origen_group_label(origen):
    return ORIGEN_LABELS.get(origen_group_key(origen), origen_group_key(origen))


def _now():
    return dt.datetime.now(dt.timezone.utc)


class CustomerMeta(db.Model):
    """Datos operativos del AM, keyed por email (la clave que une Stripe+Mongo).
    El estado de suscripción/plan/pagos NO vive acá: viene del snapshot de producto."""
    __tablename__ = "customer_meta"

    email = db.Column(db.String(320), primary_key=True)
    origen = db.Column(db.String(32), nullable=False, default="sin_asignar")
    # Si origen == 'referido', email del cliente que lo refirió (puede ser libre).
    referido_por = db.Column(db.String(320), nullable=True)
    onboarding_hecho = db.Column(db.Boolean, nullable=False, default=False)
    manual_plan = db.Column(db.String(32), nullable=False, default="")
    manual_estado = db.Column(db.String(32), nullable=False, default="")
    tipo_cliente = db.Column(db.String(32), nullable=False, default="")
    whatsapp = db.Column(db.String(80), nullable=False, default="")
    usuario = db.Column(db.String(120), nullable=False, default="")
    colab_descuento = db.Column(db.String(80), nullable=False, default="")
    colab_acuerdo = db.Column(db.Text, nullable=False, default="")
    colab_inicio = db.Column(db.String(10), nullable=False, default="")
    colab_revision = db.Column(db.String(10), nullable=False, default="")
    created_at = db.Column(db.DateTime(timezone=True), default=_now)
    updated_at = db.Column(db.DateTime(timezone=True), default=_now, onupdate=_now)

    interacciones = db.relationship(
        "Interaccion", backref="cliente", lazy="dynamic",
        cascade="all, delete-orphan",
        primaryjoin="CustomerMeta.email == foreign(Interaccion.customer_email)",
    )

    @property
    def origen_label(self):
        return ORIGEN_LABELS.get(self.origen, self.origen)


class Interaccion(db.Model):
    """Cada contacto/nota que el AM registra sobre un cliente."""
    __tablename__ = "interacciones"

    id = db.Column(db.Integer, primary_key=True)
    customer_email = db.Column(db.String(320), nullable=False, index=True)
    tipo = db.Column(db.String(32), nullable=False, default="nota")  # nota, onboarding, queja, churn, upsell
    texto = db.Column(db.Text, nullable=False)
    agente = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=_now)
    # Solo aplica a tipo == "queja": una queja arranca abierta hasta resolverla.
    resuelta = db.Column(db.Boolean, nullable=False, default=False)
    categoria = db.Column(db.String(64), nullable=False, default="")
    equipo = db.Column(db.String(16), nullable=False, default="cs")
    estado_gestion = db.Column(db.String(32), nullable=False, default="abierta")
    importancia = db.Column(db.String(16), nullable=False, default="media")
    resolved_at = db.Column(db.DateTime(timezone=True), nullable=True)


class CustomerReminder(db.Model):
    """Recordatorio operativo con fecha limite para contactar o accionar sobre un cliente."""
    __tablename__ = "customer_reminders"

    id = db.Column(db.Integer, primary_key=True)
    customer_email = db.Column(db.String(320), nullable=False, index=True)
    texto = db.Column(db.Text, nullable=False)
    due_date = db.Column(db.String(10), nullable=False, index=True)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=_now)


class TicketComment(db.Model):
    """Comentario interno dentro de una solicitud/queja operativa."""
    __tablename__ = "ticket_comments"

    id = db.Column(db.Integer, primary_key=True)
    interaccion_id = db.Column(db.Integer, db.ForeignKey("interacciones.id"), nullable=False, index=True)
    texto = db.Column(db.Text, nullable=False)
    agente = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=_now)

    ticket = db.relationship(
        "Interaccion",
        backref=db.backref("comentarios", lazy="dynamic", cascade="all, delete-orphan"),
    )


class ComplaintCategory(db.Model):
    """Categorias editables para clasificar quejas."""
    __tablename__ = "complaint_categories"

    key = db.Column(db.String(64), primary_key=True)
    label = db.Column(db.String(120), nullable=False)
    activa = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=_now)


class MessageCategory(db.Model):
    """Categorias editables de la wiki de mensajes."""
    __tablename__ = "message_categories"

    key = db.Column(db.String(64), primary_key=True)
    label = db.Column(db.String(120), nullable=False)
    activa = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=_now)


class MessageTemplate(db.Model):
    """Texto reutilizable para atencion, onboarding y pagos."""
    __tablename__ = "message_templates"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(160), nullable=False)
    cuerpo = db.Column(db.Text, nullable=False)
    categoria_key = db.Column(db.String(64), nullable=False, default="bienvenida", index=True)
    tags = db.Column(db.String(240), nullable=False, default="")
    activo = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=_now)
    updated_at = db.Column(db.DateTime(timezone=True), default=_now, onupdate=_now)


class ChurnReason(db.Model):
    """Motivo operativo asociado a una baja historica del snapshot."""
    __tablename__ = "churn_reasons"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(320), nullable=False, index=True)
    fecha = db.Column(db.String(32), nullable=False, index=True)
    motivo = db.Column(db.String(80), nullable=False, default="")
    detalle = db.Column(db.Text, nullable=False, default="")
    updated_at = db.Column(db.DateTime(timezone=True), default=_now, onupdate=_now)


class ColabCreator(db.Model):
    """Pipeline de creadores/prospectos para colaboraciones."""
    __tablename__ = "colab_creators"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(160), nullable=False)
    contacto = db.Column(db.String(240), nullable=False, default="")
    red = db.Column(db.String(80), nullable=False, default="")
    estado = db.Column(db.String(32), nullable=False, default="idea")
    tipo = db.Column(db.String(32), nullable=False, default="free")
    idea = db.Column(db.Text, nullable=False, default="")
    detalles = db.Column(db.Text, nullable=False, default="")
    duracion = db.Column(db.String(120), nullable=False, default="")
    fecha_inicio = db.Column(db.String(10), nullable=False, default="")
    fecha_fin = db.Column(db.String(10), nullable=False, default="")
    proxima_accion = db.Column(db.Text, nullable=False, default="")
    responsable = db.Column(db.String(120), nullable=False, default="")
    activo = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=_now)
    updated_at = db.Column(db.DateTime(timezone=True), default=_now, onupdate=_now)


class Snapshot(db.Model):
    """Cache del snapshot de producto (Mongo+Stripe). Guardamos el último para
    no pegarle a las APIs en cada carga y sobrevivir reinicios de Railway."""
    __tablename__ = "snapshots"

    id = db.Column(db.Integer, primary_key=True)
    generado = db.Column(db.DateTime(timezone=True), default=_now)
    payload = db.Column(db.JSON, nullable=False)
