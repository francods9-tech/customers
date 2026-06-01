import unittest


class AppRoutesTest(unittest.TestCase):
    def setUp(self):
        from app import app

        self.app = app
        self.client = app.test_client()

    def tearDown(self):
        from db import db
        from db.models import Interaccion, Snapshot

        with self.app.app_context():
            Interaccion.query.filter(Interaccion.customer_email.like("%@example.test")).delete(synchronize_session=False)
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
            self.assertEqual(row.agente, "Fran")
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
            ("ops", "ops", "abierta"),
            ("cliente", "cs", "esperando"),
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
        self.assertLess(body.index("Ana"), body.index("Zeta"))

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
