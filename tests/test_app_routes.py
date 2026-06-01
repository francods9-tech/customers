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

    def test_ficha_permita_guardar_whatsapp(self):
        self.login()
        self.add_snapshot([self.customer_row()])

        response = self.client.get("/cliente/cliente-z@example.test")
        self.assertEqual(response.status_code, 200)
        self.assertIn('name="whatsapp"', response.get_data(as_text=True))

        response = self.client.post(
            "/cliente/cliente-z@example.test/contacto",
            data={"whatsapp": "+54 9 11 2222 3333"},
        )

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            from db.models import CustomerMeta
            meta = CustomerMeta.query.filter_by(email="cliente-z@example.test").one()
            self.assertEqual(meta.whatsapp, "+54 9 11 2222 3333")

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
            "pelota": "cs",
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
            self.assertEqual(row.equipo, "cs")
            self.assertEqual(row.estado_gestion, "abierta")
            self.assertFalse(row.resuelta)

    def test_solicitud_directa_mapea_pelota(self):
        from db.models import Interaccion

        self.login()
        self.add_snapshot([{
            "nombre": "Cliente Pelota",
            "email": "pelota@example.test",
            "email_key": "pelota@example.test",
        }])

        cases = [
            ("cs", "cs", "abierta"),
            ("ops", "ops", "en_gestion"),
            ("cliente", "cs", "comunicar"),
        ]
        for pelota, equipo, estado in cases:
            response = self.client.post("/solicitudes/nueva", data={
                "customer_email": "pelota@example.test",
                "tipo": "queja",
                "categoria": "tiempos_gestion",
                "pelota": pelota,
                "texto": f"Detalle {pelota}",
            })
            self.assertEqual(response.status_code, 302)

        with self.app.app_context():
            rows = Interaccion.query.filter_by(customer_email="pelota@example.test").order_by(Interaccion.id.asc()).all()
            self.assertEqual([(r.equipo, r.estado_gestion) for r in rows], [(c[1], c[2]) for c in cases])

    def test_solicitudes_muestra_formulario_con_clientes_ordenados(self):
        self.login()
        self.add_snapshot([
            {"nombre": "Zeta", "email": "zeta@example.test", "email_key": "zeta@example.test"},
            {"nombre": "Ana", "email": "ana@example.test", "email_key": "ana@example.test"},
        ])

        response = self.client.get("/solicitudes")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Nueva solicitud", body)
        self.assertIn("ana@example.test", body)
        self.assertIn('name="importancia"', body)
        self.assertNotIn('name="agente"', body)
        self.assertLess(body.index("Ana"), body.index("Zeta"))

    def test_ticket_muestra_numero_aging_y_comentarios(self):
        import datetime as dt

        from db import db
        from db.models import Interaccion

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
