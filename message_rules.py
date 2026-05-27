DEFAULT_MESSAGE_CATEGORIES = [
    ("bienvenida", "Bienvenida"),
    ("pagos", "Pagos"),
    ("soporte", "Soporte"),
    ("quejas", "Quejas"),
    ("operacion_remocion", "Operacion / Remocion"),
    ("ventas_suscripcion", "Ventas / Suscripcion"),
    ("cierre_seguimiento", "Cierre / Seguimiento"),
]


CS_PACK_TEMPLATES = [
    {
        "titulo": "Baja de enlace - intake inicial",
        "categoria_key": "operacion_remocion",
        "tags": "whatsapp,baja_enlace,intake,links,remocion",
        "cuerpo": (
            "Hola {{nombre}}, gracias por avisarnos. Pasanos el {{enlace}} o captura "
            "donde aparece el contenido y lo revisamos hoy. Te confirmamos por este chat "
            "cuando quede cargado en gestion."
        ),
    },
    {
        "titulo": "Link activo - seguimiento con checkpoint",
        "categoria_key": "operacion_remocion",
        "tags": "whatsapp,link_activo,seguimiento,checkpoint",
        "cuerpo": (
            "Hola {{nombre}}, ya tomamos el caso del link activo. Vamos a validar la URL, "
            "plataforma y estado de gestion con Operaciones. Te damos una actualizacion "
            "concreta antes de {{hora}}."
        ),
    },
    {
        "titulo": "Queja o demora - contencion con checkpoint",
        "categoria_key": "quejas",
        "tags": "whatsapp,queja,demora,checkpoint,retencion",
        "cuerpo": (
            "Hola {{nombre}}, entiendo la molestia y lo reviso ahora. Para no hacerte "
            "repetir, voy a validar {{caso}} con el equipo y te doy una actualizacion "
            "concreta antes de {{hora}}."
        ),
    },
    {
        "titulo": "Consulta general - explicacion del servicio",
        "categoria_key": "soporte",
        "tags": "whatsapp,consulta,proceso,alcance",
        "cuerpo": (
            "Hola {{nombre}}, te explico. Traqeer busca y gestiona bajas de filtraciones "
            "asociadas a tus nombres de usuario, enlaces y plataformas. Si queres, "
            "revisamos tu caso puntual con {{dato_clave}}."
        ),
    },
    {
        "titulo": "Soporte tecnico - acceso o dashboard",
        "categoria_key": "soporte",
        "tags": "whatsapp,soporte,dashboard,acceso,pago",
        "cuerpo": (
            "Hola {{nombre}}, lo revisamos. Pasanos {{captura_o_error}} y el mail/usuario "
            "de la cuenta para validar acceso, dashboard o pago sin perder contexto."
        ),
    },
    {
        "titulo": "Alta y suscripcion - planes y proximo paso",
        "categoria_key": "ventas_suscripcion",
        "tags": "whatsapp,suscripcion,alta,planes,pago",
        "cuerpo": (
            "Hola {{nombre}}, podemos ayudarte. Estos son los planes disponibles: "
            "{{planes}}. Si queres avanzar, te acompano con el alta y revisamos tus "
            "usuarios/enlaces iniciales."
        ),
    },
    {
        "titulo": "Venta - prueba o auditoria inicial",
        "categoria_key": "ventas_suscripcion",
        "tags": "whatsapp,ventas,prueba,descuento,auditoria",
        "cuerpo": (
            "Hola {{nombre}}, vimos que podriamos ayudarte a reducir filtraciones y "
            "proteger tus links. Si te sirve, te comparto una prueba de {{prueba}} y "
            "revisamos tus plataformas principales."
        ),
    },
    {
        "titulo": "Cierre - accion responsable y plazo",
        "categoria_key": "cierre_seguimiento",
        "tags": "whatsapp,cierre,seguimiento,responsable,plazo",
        "cuerpo": (
            "Queda registrado {{accion_realizada}}. El responsable es {{responsable}} y "
            "el proximo checkpoint es {{fecha_hora}}. Si aparece otro link o novedad, "
            "mandanoslo por aca y lo sumamos al caso."
        ),
    },
]


def slugify(value):
    key = "".join(ch.lower() if ch.isalnum() else "_" for ch in (value or "").strip()).strip("_")
    while "__" in key:
        key = key.replace("__", "_")
    return key


def parse_tags(value):
    tags = []
    seen = set()
    for raw in (value or "").split(","):
        tag = slugify(raw)
        if tag and tag not in seen:
            tags.append(tag)
            seen.add(tag)
    return ",".join(tags)


def tag_list(value):
    return [tag for tag in (value or "").split(",") if tag]


def filter_messages(messages, q=None, category=None):
    rows = list(messages)
    if category:
        rows = [m for m in rows if getattr(m, "categoria_key", "") == category]
    if q:
        needle = q.strip().lower()
        rows = [
            m for m in rows
            if needle in (getattr(m, "titulo", "") or "").lower()
            or needle in (getattr(m, "cuerpo", "") or "").lower()
            or needle in (getattr(m, "tags", "") or "").lower()
        ]
    return rows
