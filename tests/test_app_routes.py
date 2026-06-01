import unittest


class AppRoutesTest(unittest.TestCase):
    def setUp(self):
        from app import app

        self.app = app
        self.client = app.test_client()

    def tearDown(self):
        from db import db
        from db.models import CustomerMeta, Interaccion, Snapshot, TicketComment

        with self.app.app_context():
            TicketComment.query.filter(TicketComment.ticket.has(Interaccion.customer_email.like("%@example.test"))).delete(synchronize_session=False)
            Interaccion.query.filter(Interaccion.customer_email.like("%@example.test")).delete(synchronize_session=False)
            CustomerMeta.query.filter(CustomerMeta.email.like("%@example.test")).delete(synchronize_session=False)
            Snapshot.query.filter(Snapshot.payload["test_marker"].as_string() == "solicitudes_directas").delete(synchronize_session=False)
            db.session.commit()

    def login(self):
        with self.client.session_transaction() as sess:
            sess["auth"] = True

    def add_snapshot(self, clientes):
        from db import db
        from db.models import Snapshot

        with self.app.app_context():
            db.session.add(Snapshot(payload={
                "test_marker": "solicitudes_directas",
                "clientes": clientes,
                "eventos": {"altas": [], "bajas": []},
                "resumen": {},
            }))
            db.session.commit()

    def customer_row(self, nombre="Cliente Z", email="cliente-z@example.test"):
        return {
            "nombre": nombre,
            "email": email,
            "email_key": email,
            "plan": "Premium",
            "estado": "activo",
            "anual": False,
            "fecha_alta": "01/05/2026",
            "fecha_alta_raw": "2026-05-01T00:00:00+00:00",
            "dias_de_alta": 10,
            "account_ids": [],
        }

    def test_healthz_is_public(self):
        response = self.client.get("/healthz")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "ok")

    def test_colabs_route_requires_login(self):
        response = self.client.get("/colabs")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.location)

    def test_colab_creator_create_requires_login(self):
        response = self.client.post("/colabs/creadores", data={"nombre": "Creator"})

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.location)

    def test_bajas_route_requires_login(self):
        response = self.client.get("/bajas")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.location)

    def test_ficha_permita_guardar_contacto_whatsapp_y_usuario(self):
        self.login()
        self.add_snapshot([self.customer_row()])

        response = self.client.get("/cliente/cliente-z@example.test")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('name="whatsapp"', body)
        self.assertIn('name="usuario"', body)
        self.assertIn("customer-profile-grid", body)

        response = self.client.post(
            "/cliente/cliente-z@example.test/contacto",
            data={"whatsapp": "+54 9 11 2222 3333", "usuario": "@clientez"},
        )

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            from db.models import CustomerMeta
            meta = CustomerMeta.query.filter_by(email="cliente-z@example.test").one()
            self.assertEqual(meta.whatsapp, "+54 9 11 2222 3333")
            self.assertEqual(meta.usuario, "@clientez")

    def test_dashboard_no_muestra_finanzas_ni_gastos(self):
        self.login()

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertNotIn("Gastos", body)
        self.assertNotIn("MRR", body)
        self.assertNotIn("Stripe", body)
        self.assertNotIn("Mercury", body)

    def test_solicitud_directa_requires_login(self):
        response = self.client.post("/solicitudes/nueva", data={"texto": "Alta manual"})

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.location)

    def test_solicitud_directa_crea_interaccion_abierta(self):
        from db.models import Interaccion

        self.login()
        self.add_snapshot([{
            "nombre": "Cliente Z",
            "email": "cliente-z@example.test",
            "email_key": "cliente-z@example.test",
        }])

        response = self.client.post("/solicitudes/nueva", data={
            "customer_email": "cliente-z@example.test",
            "tipo": "solicitud",
            "categoria": "envia_links",
            "estado_gestion": "comunicar",
            "importancia": "alta",
            "agente": "Fran",
            "texto": "Necesita bajar tres enlaces.",
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/solicitudes"))
        with self.app.app_context():
            row = Interaccion.query.filter_by(customer_email="cliente-z@example.test").one()
            self.assertEqual(row.tipo, "solicitud")
            self.assertEqual(row.categoria, "envia_links")
            self.assertEqual(row.texto, "Necesita bajar tres enlaces.")
            self.assertIsNone(row.agente)
            self.assertEqual(row.importancia, "alta")
            self.assertEqual(row.equipo, "ops")
            self.assertEqual(row.estado_gestion, "abierta")
            self.assertFalse(row.resuelta)

    def test_solicitud_directa_ignora_estado_inicial_y_crea_abierta(self):
        from db.models import Interaccion

        self.login()
        self.add_snapshot([{
            "nombre": "Cliente Estado",
            "email": "estado@example.test",
            "email_key": "estado@example.test",
        }])

        response = self.client.post("/solicitudes/nueva", data={
            "customer_email": "estado@example.test",
            "tipo": "queja",
            "categoria": "tiempos_gestion",
            "estado_gestion": "comunicar",
            "texto": "Detalle default abierta",
        })
        self.assertEqual(response.status_code, 302)

        with self.app.app_context():
            row = Interaccion.query.filter_by(customer_email="estado@example.test").one()
            self.assertEqual(row.estado_gestion, "abierta")
            self.assertEqual(row.equipo, "ops")

    def test_solicitudes_muestra_formulario_con_clientes_ordenados(self):
        from db import db
        from db.models import CustomerMeta

        self.login()
        self.add_snapshot([
            {"nombre": "Zeta", "email": "zeta@example.test", "email_key": "zeta@example.test"},
            {"nombre": "Ana", "email": "ana@example.test", "email_key": "ana@example.test"},
        ])
        with self.app.app_context():
            db.session.add(CustomerMeta(email="ana@example.test", whatsapp="+54 9 11 5555 0000", usuario="@ana-user"))
            db.session.commit()

        response = self.client.get("/solicitudes")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Nueva solicitud", body)
        self.assertNotIn("Nueva categoria", body)
        self.assertNotIn("Categorias</h2>", body)
        self.assertNotIn("/quejas/categorias", body)
        self.assertIn("ana@example.test", body)
        self.assertIn("+54 9 11 5555 0000", body)
        self.assertIn("@ana-user", body)
        self.assertIn('type="search"', body)
        self.assertIn('data-customer-search', body)
        self.assertIn('name="importancia"', body)
        new_form = body[body.index('action="/solicitudes/nueva"'):]
        new_form = new_form[:new_form.index("</form>")]
        self.assertNotIn('name="estado_gestion"', new_form)
        self.assertNotIn('name="pelota"', body)
        self.assertNotIn('name="agente"', body)
        self.assertLess(body.index("Ana"), body.index("Zeta"))

    def test_solicitudes_abiertas_actualizan_estado_importancia_y_se_pueden_eliminar(self):
        import datetime as dt

        from db import db
        from db.models import Interaccion

        self.login()
        self.add_snapshot([self.customer_row()])
        with self.app.app_context():
            ticket = Interaccion(
                customer_email="cliente-z@example.test",
                tipo="solicitud",
                texto="Abrir para borrar",
                categoria="envia_links",
                equipo="cs",
                estado_gestion="abierta",
                importancia="media",
                created_at=dt.datetime.now(dt.timezone.utc),
            )
            db.session.add(ticket)
            db.session.commit()
            ticket_id = ticket.id

        response = self.client.get("/solicitudes")
        body = response.get_data(as_text=True)
        ticket_row = body[body.index(f"Ticket #{ticket_id}"):]
        ticket_row = ticket_row[:ticket_row.index("</li>")]
        self.assertIn("OPERACIONES", ticket_row)
        self.assertIn("Eliminar", ticket_row)
        self.assertEqual(ticket_row.count("Actualizar"), 1)
        self.assertNotIn('name="categoria"', ticket_row)

        response = self.client.post(
            f"/queja/{ticket_id}/gestion",
            data={"estado_gestion": "en_gestion", "importancia": "alta"},
        )
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            ticket = db.session.get(Interaccion, ticket_id)
            self.assertEqual(ticket.estado_gestion, "en_gestion")
            self.assertEqual(ticket.equipo, "ops")
            self.assertEqual(ticket.importancia, "alta")
            self.assertEqual(ticket.categoria, "envia_links")

        response = self.client.post(f"/solicitudes/{ticket_id}/eliminar")
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            self.assertIsNone(db.session.get(Interaccion, ticket_id))

    def test_ticket_muestra_numero_aging_y_comentarios(self):
        import datetime as dt

        from db import db
        from db.models import Interaccion, TicketComment

        self.login()
        self.add_snapshot([self.customer_row()])
        with self.app.app_context():
            ticket = Interaccion(
                customer_email="cliente-z@example.test",
                tipo="solicitud",
                texto="Revisar enlace activo",
                categoria="envia_links",
                equipo="ops",
                estado_gestion="en_gestion",
                importancia="alta",
                created_at=dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=8),
            )
            db.session.add(ticket)
            db.session.commit()
            ticket_id = ticket.id

        response = self.client.get("/solicitudes")
        body = response.get_data(as_text=True)
        self.assertIn(f"Ticket #{ticket_id}", body)
        self.assertIn("8 dias", body)
        self.assertIn("age-warn", body)
        self.assertIn("Alta", body)
        self.assertIn(f'/solicitudes/{ticket_id}', body)

        response = self.client.post(
            f"/solicitudes/{ticket_id}/comentarios",
            data={"texto": "Ops confirma que lo toma hoy."},
        )
        self.assertEqual(response.status_code, 302)

        response = self.client.get(f"/solicitudes/{ticket_id}")
        body = response.get_data(as_text=True)
        self.assertIn(f"Ticket #{ticket_id}", body)
        self.assertIn("Ops confirma que lo toma hoy.", body)
        self.assertIn("En gestion", body)
        self.assertIn("status-en_gestion", body)
        self.assertNotIn('name="agente"', body)
        self.assertNotIn("Autor", body)

        with self.app.app_context():
            comment = TicketComment.query.filter_by(interaccion_id=ticket_id).one()
            self.assertIsNone(comment.agente)

    def test_ticket_resuelto_muestra_dias_abierto_y_permite_reabrir(self):
        import datetime as dt

        from db import db
        from db.models import Interaccion

        self.login()
        self.add_snapshot([self.customer_row()])
        created = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=10)
        resolved = created + dt.timedelta(days=4)
        with self.app.app_context():
            ticket = Interaccion(
                customer_email="cliente-z@example.test",
                tipo="solicitud",
                texto="Ya resuelto por ops",
                categoria="envia_links",
                equipo="ops",
                estado_gestion="resuelta",
                importancia="media",
                resuelta=True,
                created_at=created,
                resolved_at=resolved,
            )
            db.session.add(ticket)
            db.session.commit()
            ticket_id = ticket.id

        response = self.client.get("/solicitudes")
        body = response.get_data(as_text=True)
        self.assertIn(f"Ticket #{ticket_id}", body)
        ticket_row = body[body.index(f"Ticket #{ticket_id}"):]
        ticket_row = ticket_row[:ticket_row.index("</li>")]
        self.assertIn("4 dias abierto", body)
        self.assertIn("status-resuelta", body)
        self.assertIn("Reabrir", body)
        self.assertNotIn(">OPERACIONES</span>", ticket_row)

        response = self.client.post(f"/solicitudes/{ticket_id}/reabrir")
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            ticket = db.session.get(Interaccion, ticket_id)
            self.assertFalse(ticket.resuelta)
            self.assertEqual(ticket.estado_gestion, "abierta")
            self.assertEqual(ticket.equipo, "ops")
            self.assertIsNone(ticket.resolved_at)

    def test_ticket_aging_rojo_mas_de_catorce_dias(self):
        import datetime as dt

        from db import db
        from db.models import Interaccion

        self.login()
        self.add_snapshot([self.customer_row()])
        with self.app.app_context():
            ticket = Interaccion(
                customer_email="cliente-z@example.test",
                tipo="queja",
                texto="Pendiente viejo",
                estado_gestion="abierta",
                created_at=dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=15),
            )
            db.session.add(ticket)
            db.session.commit()

        response = self.client.get("/solicitudes")
        body = response.get_data(as_text=True)
        self.assertIn("15 dias", body)
        self.assertIn("age-danger", body)

    def test_solicitudes_sin_snapshot_deshabilita_formulario(self):
        import app as app_module

        self.login()
        original = app_module.ultimo_snapshot
        app_module.ultimo_snapshot = lambda: None

        try:
            response = self.client.get("/solicitudes")
        finally:
            app_module.ultimo_snapshot = original

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("No hay clientes cargados", body)
        self.assertIn("disabled", body)


if __name__ == "__main__":
    unittest.main()
