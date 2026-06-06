import unittest


class AppRoutesTest(unittest.TestCase):
    def setUp(self):
        from app import app

        self.app = app
        self.client = app.test_client()

    def tearDown(self):
        from db import db
        from db.models import (ChurnReason, ColabCreator, CustomerMeta,
                               CustomerReminder, Interaccion, MessageCategory,
                               MessageTemplate, Snapshot, TicketComment)

        with self.app.app_context():
            TicketComment.query.filter(TicketComment.ticket.has(Interaccion.customer_email.like("%@example.test"))).delete(synchronize_session=False)
            Interaccion.query.filter(Interaccion.customer_email.like("%@example.test")).delete(synchronize_session=False)
            CustomerReminder.query.filter(CustomerReminder.customer_email.like("%@example.test")).delete(synchronize_session=False)
            CustomerReminder.query.filter(CustomerReminder.customer_email == "").delete(synchronize_session=False)
            CustomerMeta.query.filter(CustomerMeta.email.like("%@example.test")).delete(synchronize_session=False)
            ChurnReason.query.filter(ChurnReason.email.like("%@example.test")).delete(synchronize_session=False)
            ColabCreator.query.filter(ColabCreator.contacto.like("%@example.test")).delete(synchronize_session=False)
            MessageTemplate.query.filter(MessageTemplate.titulo.like("Test UI%")).delete(synchronize_session=False)
            MessageCategory.query.filter(MessageCategory.key.like("test_ui_%")).delete(synchronize_session=False)
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
                "generado": "2026-06-03T00:00:00+00:00",
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

    def test_colabs_usa_layout_admin_redisenado(self):
        from db import db
        from db.models import ColabCreator, CustomerMeta

        self.login()
        self.add_snapshot([self.customer_row(nombre="Cliente Colab", email="colab@example.test")])
        with self.app.app_context():
            db.session.add(CustomerMeta(
                email="colab@example.test",
                tipo_cliente="colab_descuento",
                colab_descuento="50%",
                colab_acuerdo="Dos historias por mes",
                colab_revision="2026-06-01",
            ))
            db.session.add(ColabCreator(
                nombre="Test UI Creator",
                contacto="creator@example.test",
                red="Instagram",
                estado="negociando",
                tipo="descuento",
                proxima_accion="Enviar propuesta",
                responsable="Frank",
            ))
            db.session.commit()

        response = self.client.get("/colabs")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('class="collabs-page page polish-v5"', body)
        self.assertIn('class="page-head collabs-head"', body)
        self.assertIn('class="collabs-kpi-strip mini-kpis"', body)
        self.assertIn('class="collab-form-panel panel v5-form-panel"', body)
        self.assertIn('action="/colabs/creadores"', body)
        self.assertIn('class="creator-pipeline"', body)
        self.assertIn("Test UI Creator", body)
        self.assertIn("Enviar propuesta", body)
        self.assertIn('class="collab-clients-table"', body)
        self.assertIn("Cliente Colab", body)

    def test_bajas_usa_layout_admin_redisenado(self):
        from db import db
        from db.models import ChurnReason, Snapshot

        self.login()
        with self.app.app_context():
            db.session.add(Snapshot(payload={
                "test_marker": "solicitudes_directas",
                "generado": "2026-06-03T00:00:00+00:00",
                "clientes": [self.customer_row(nombre="Cliente Activo", email="activo-bajas@example.test")],
                "eventos": {
                    "altas": [],
                    "bajas": [{
                        "email": "baja@example.test",
                        "fecha": "2026-06-02T00:00:00+00:00",
                        "plan": "Premium",
                        "origen": "instagram",
                    }],
                },
                "resumen": {},
            }))
            db.session.add(ChurnReason(
                email="baja@example.test",
                fecha="2026-06-02",
                motivo="precio",
                detalle="Pidio bajar costos",
            ))
            db.session.commit()

        response = self.client.get("/bajas?preset=todo")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('class="churn-page page polish-v5"', body)
        self.assertIn('class="page-head churn-head"', body)
        self.assertIn('class="churn-toolbar periodo-bar v5-toolbar"', body)
        self.assertIn('class="churn-kpi-strip mini-kpis"', body)
        self.assertIn('class="churn-table"', body)
        self.assertIn("baja@example.test", body)
        self.assertIn('action="/bajas/motivo"', body)
        self.assertIn('name="motivo"', body)
        self.assertIn("Pidio bajar costos", body)

    def test_mensajes_usa_layout_admin_redisenado(self):
        from db import db
        from db.models import MessageCategory, MessageTemplate

        self.login()
        with self.app.app_context():
            db.session.add(MessageCategory(key="test_ui_soporte", label="Test UI Soporte"))
            db.session.add(MessageTemplate(
                titulo="Test UI Mensaje",
                cuerpo="Hola, revisamos tu caso y te escribimos con novedades.",
                categoria_key="test_ui_soporte",
                tags="soporte,seguimiento",
            ))
            db.session.commit()

        response = self.client.get("/mensajes?q=seguimiento")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('class="messages-page page polish-v5"', body)
        self.assertIn('class="page-head messages-head"', body)
        self.assertIn('class="message-toolbar panel v5-toolbar"', body)
        self.assertIn('action="/mensajes/categorias"', body)
        self.assertIn('class="message-form-panel panel"', body)
        self.assertIn('action="/mensajes"', body)
        self.assertIn('class="message-list redesigned-message-list"', body)
        self.assertIn("Test UI Mensaje", body)
        self.assertIn("copy-message", body)

    def test_polish_v5_renderiza_todas_las_pantallas_principales(self):
        import datetime as dt

        from db import db
        from db.models import Interaccion

        self.login()
        self.add_snapshot([
            self.customer_row(nombre="Cliente V5", email="cliente-v5@example.test"),
            {**self.customer_row(nombre="Trial V5", email="trial-v5@example.test"), "estado": "trial"},
        ])
        with self.app.app_context():
            ticket = Interaccion(
                customer_email="cliente-v5@example.test",
                tipo="solicitud",
                texto="Revisar experiencia V5",
                categoria="envia_links",
                estado_gestion="abierta",
                importancia="alta",
                created_at=dt.datetime.now(dt.timezone.utc),
            )
            db.session.add(ticket)
            db.session.commit()
            ticket_id = ticket.id

        pages = [
            ("/", ['class="dashboard-page page polish-v5"', 'class="dashboard-main-grid dashboard-chart-row v5-dashboard-grid"']),
            ("/clientes", ['class="clients-page page polish-v5"', 'class="client-toolbar v5-toolbar"']),
            ("/cliente/cliente-v5@example.test", ['class="customer-page page polish-v5"', 'class="customer-command-grid v5-two-column"']),
            ("/bandeja", ['class="inbox-page page polish-v5"', 'class="inbox-buckets v5-panel-stack"']),
            ("/solicitudes", ['class="requests-page page polish-v5"', 'class="request-board panel v5-board-panel"']),
            (f"/solicitudes/{ticket_id}", ['class="ticket-page page polish-v5"', 'class="ticket-layout ticket-layout-compact"']),
            ("/colabs", ['class="collabs-page page polish-v5"', 'class="collab-form-panel panel v5-form-panel"']),
            ("/bajas?preset=todo", ['class="churn-page page polish-v5"', 'class="churn-toolbar periodo-bar v5-toolbar"']),
            ("/mensajes", ['class="messages-page page polish-v5"', 'class="message-toolbar panel v5-toolbar"']),
        ]

        for path, expected_snippets in pages:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                body = response.get_data(as_text=True)
                for snippet in expected_snippets:
                    self.assertIn(snippet, body)

        body = self.client.get("/solicitudes").get_data(as_text=True)
        self.assertIn('action="/solicitudes/nueva"', body)
        self.assertIn('action="/queja/', body)
        body = self.client.get(f"/solicitudes/{ticket_id}").get_data(as_text=True)
        self.assertIn(f'action="/solicitudes/{ticket_id}/comentarios"', body)
        self.assertIn(f'action="/queja/{ticket_id}/gestion"', body)

    def test_ficha_permita_guardar_contacto_whatsapp_y_usuario(self):
        from db import db
        from db.models import CustomerMeta

        self.login()
        self.add_snapshot([self.customer_row()])
        with self.app.app_context():
            db.session.add(CustomerMeta(email="cliente-z@example.test", whatsapp_status="manager"))
            db.session.commit()

        response = self.client.get("/cliente/cliente-z@example.test")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('name="whatsapp"', body)
        self.assertIn('name="usuario"', body)
        self.assertIn('name="manager"', body)
        self.assertIn('name="manual_nombre"', body)
        self.assertNotIn('name="whatsapp_status"', body)
        self.assertNotIn("Estado WhatsApp", body)
        self.assertIn("customer-profile-grid", body)
        self.assertIn("profile-overview-grid", body)
        self.assertIn("profile-secondary-grid", body)
        self.assertNotIn("client-action-form", body)

        response = self.client.post(
            "/cliente/cliente-z@example.test/contacto",
            data={
                "whatsapp": "+54 9 11 2222 3333",
                "usuario": "@clientez",
                "manager": "Dalila",
                "manual_nombre": "Patri Castillo",
            },
        )

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            meta = CustomerMeta.query.filter_by(email="cliente-z@example.test").one()
            self.assertEqual(meta.whatsapp, "+54 9 11 2222 3333")
            self.assertEqual(meta.usuario, "@clientez")
            self.assertEqual(meta.manager, "Dalila")
            self.assertEqual(meta.manual_nombre, "Patri Castillo")
            self.assertEqual(meta.whatsapp_status, "manager")

        response = self.client.get("/cliente/cliente-z@example.test")
        body = response.get_data(as_text=True)
        self.assertIn("<h1>Patri Castillo</h1>", body)
        self.assertIn("Antes: Cliente Z", body)

    def test_customer_meta_acepta_manager_y_estado_whatsapp(self):
        from db import db
        from db.models import CustomerMeta

        with self.app.app_context():
            db.session.add(CustomerMeta(
                email="manager-status@example.test",
                manager="Frank",
                whatsapp_status="manager",
            ))
            db.session.commit()

            meta = CustomerMeta.query.filter_by(email="manager-status@example.test").one()
            self.assertEqual(meta.manager, "Frank")
            self.assertEqual(meta.whatsapp_status, "manager")

    def test_clientes_busca_por_usuario_y_whatsapp_con_placeholder_simple(self):
        from db import db
        from db.models import CustomerMeta

        self.login()
        self.add_snapshot([
            self.customer_row(nombre="Ana", email="ana@example.test"),
            self.customer_row(nombre="Mia", email="mia@example.test"),
        ])
        with self.app.app_context():
            db.session.add(CustomerMeta(email="ana@example.test", whatsapp="+54 9 11 5555 0000", usuario="@ana-user"))
            db.session.commit()

        response = self.client.get("/clientes?q=ana-user")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('class="app-shell"', body)
        self.assertIn('class="sidebar"', body)
        self.assertIn('class="client-filters"', body)
        self.assertIn('name="q"', body)
        self.assertIn('placeholder="Buscar cliente"', body)
        self.assertIn('onclick="document.getElementById(\'create-client-dialog\').showModal()"', body)
        self.assertIn('id="create-client-dialog"', body)
        self.assertIn('action="/clientes/manual"', body)
        self.assertIn('value="colab_descuento" selected>Colab con descuento', body)
        self.assertIn('value="activo" selected>Activo', body)
        self.assertNotIn("<h2>Cliente manual</h2>", body)
        self.assertIn("Ana", body)
        self.assertNotIn("Mia", body)

        response = self.client.get("/clientes?q=5555")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Ana", body)
        self.assertNotIn("Mia", body)

    def test_clientes_usa_cards_como_filtros_y_no_muestra_chips_de_estado(self):
        self.login()
        self.add_snapshot([
            {**self.customer_row(nombre="Agencia Norte", email="agencia@example.test"), "tipo_cliente_key": "agencia", "tipo_cliente": "Agencia", "origen": "instagram"},
            {**self.customer_row(nombre="One Shot", email="one-time@example.test"), "tipo_cliente_key": "one_time", "tipo_cliente": "One time payment", "cuenta_activo_recurrente": False, "origen": "instagram"},
            {**self.customer_row(nombre="Free Partner", email="free-colab@example.test"), "tipo_cliente_key": "free_colab", "tipo_cliente": "Free por colab", "cuenta_activo_recurrente": False, "origen": "instagram"},
            {**self.customer_row(nombre="Colab Paid", email="colab-paid@example.test"), "tipo_cliente_key": "colab_descuento", "tipo_cliente": "Colab con descuento", "origen": "instagram"},
        ])

        response = self.client.get("/clientes?origen=instagram&q=example")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('class="segmented-filter"', body)
        self.assertNotIn("Pausados impago", body)
        self.assertNotIn("Inactivos impago", body)
        self.assertIn('placeholder="Buscar cliente"', body)
        self.assertIn('name="origen"', body)
        self.assertIn('name="tipo"', body)
        self.assertIn("Crear cliente", body)
        self.assertIn('href="/clientes?recurrente=1&amp;origen=instagram&amp;q=example"', body)
        self.assertIn('href="/clientes?tipo=agencia&amp;origen=instagram&amp;q=example"', body)
        self.assertIn('href="/clientes?tipo=one_time&amp;origen=instagram&amp;q=example"', body)
        self.assertIn('href="/clientes?tipo=free_colab&amp;origen=instagram&amp;q=example"', body)
        self.assertIn('href="/clientes?tipo=colab_descuento&amp;origen=instagram&amp;q=example"', body)
        self.assertNotIn("Colabs a revisar", body)

    def test_clientes_card_bajas_cuenta_historico_y_enlaza_a_bajas_todo(self):
        from db import db
        from db.models import Snapshot

        self.login()
        with self.app.app_context():
            db.session.add(Snapshot(payload={
                "test_marker": "solicitudes_directas",
                "generado": "2026-06-03T00:00:00+00:00",
                "clientes": [
                    self.customer_row(nombre="Activo Reactivado", email="activo-reactivado@example.test"),
                    {**self.customer_row(nombre="Cliente Actual", email="actual@example.test"), "email_key": "actual@example.test"},
                ],
                "eventos": {"altas": [], "bajas": [
                    {"nombre": "Baja Real", "email": "baja-real@example.test", "fecha": "2026-05-01T00:00:00+00:00"},
                    {"nombre": "Activo Reactivado", "email": "activo-reactivado@example.test", "fecha": "2026-05-02T00:00:00+00:00"},
                ]},
                "resumen": {},
            }))
            db.session.commit()

        response = self.client.get("/clientes")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("<span>Bajas</span>", body)
        bajas_block = body[body.index("<span>Bajas</span>") - 80:body.index("<span>Bajas</span>") + 40]
        self.assertIn('href="/bajas?preset=todo"', bajas_block)
        self.assertIn("<strong>1</strong>", bajas_block)

    def test_clientes_ordena_por_columnas_y_preserva_filtros(self):
        self.login()
        self.add_snapshot([
            {**self.customer_row(nombre="Beta", email="beta@example.test"), "fecha_alta": "03/06/2026", "fecha_alta_raw": "2026-06-03T00:00:00+00:00"},
            {**self.customer_row(nombre="Ana", email="ana@example.test"), "fecha_alta": "01/06/2026", "fecha_alta_raw": "2026-06-01T00:00:00+00:00"},
        ])

        response = self.client.get("/clientes?sort=alta&dir=desc&q=example")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertLess(body.index("Beta"), body.index("Ana"))
        self.assertIn("sort=cliente", body)
        self.assertIn("sort=tipo", body)
        self.assertIn("sort=plan", body)
        self.assertIn("sort=estado", body)
        self.assertIn("sort=atencion", body)
        self.assertIn("sort=origen", body)
        self.assertIn("sort=alta", body)
        self.assertIn("q=example", body)
        self.assertIn('class="clientes-mobile-list v5-mobile-list"', body)

        response = self.client.get("/clientes?sort=cliente&dir=asc")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertLess(body.index("Ana"), body.index("Beta"))

    def test_clientes_default_ordena_por_alta_desc_y_oculta_inactivos(self):
        from db import db
        from db.models import CustomerMeta

        self.login()
        self.add_snapshot([
            {**self.customer_row(nombre="Alta Vieja", email="alta-vieja@example.test"), "fecha_alta": "01/06/2026", "fecha_alta_raw": "2026-06-01T00:00:00+00:00"},
            {**self.customer_row(nombre="Alta Nueva", email="alta-nueva@example.test"), "fecha_alta": "03/06/2026", "fecha_alta_raw": "2026-06-03T00:00:00+00:00"},
        ])
        with self.app.app_context():
            db.session.add(CustomerMeta(
                email="oculto@example.test",
                manual_customer=True,
                manual_nombre="Cliente Oculto",
                manual_fecha_alta="2026-06-04",
                manual_estado="inactivo",
                tipo_cliente="colab_descuento",
            ))
            db.session.commit()

        response = self.client.get("/clientes")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertLess(body.index("Alta Nueva"), body.index("Alta Vieja"))
        self.assertNotIn("Cliente Oculto", body)

        response = self.client.get("/clientes?estado=inactivo")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Cliente Oculto", body)

    def test_migracion_manual_customer_usa_default_boolean_postgres(self):
        import inspect
        import app as app_module

        source = inspect.getsource(app_module._ensure_local_schema)

        self.assertIn("manual_customer BOOLEAN NOT NULL DEFAULT FALSE", source)
        self.assertNotIn("manual_customer BOOLEAN NOT NULL DEFAULT 0", source)
        self.assertIn("manager VARCHAR(120) NOT NULL DEFAULT ''", source)
        self.assertIn("whatsapp_status VARCHAR(32) NOT NULL DEFAULT 'sin_dato'", source)

    def test_crear_cliente_manual_persiste_aparece_y_abre_ficha(self):
        from db.models import CustomerMeta

        self.login()
        self.add_snapshot([])

        response = self.client.post("/clientes/manual", data={
            "manual_nombre": "Manual Colab",
            "email": "manual-colab@example.test",
            "manual_fecha_alta": "2026-06-04",
            "tipo_cliente": "free_colab",
            "manual_estado": "activo",
            "origen": "whatsapp",
        })

        self.assertEqual(response.status_code, 302)
        self.assertIn("/cliente/manual-colab@example.test", response.location)
        with self.app.app_context():
            meta = CustomerMeta.query.filter_by(email="manual-colab@example.test").one()
            self.assertTrue(meta.manual_customer)
            self.assertEqual(meta.manual_nombre, "Manual Colab")
            self.assertEqual(meta.manual_fecha_alta, "2026-06-04")
            self.assertEqual(meta.tipo_cliente, "free_colab")
            self.assertEqual(meta.manual_estado, "activo")
            self.assertEqual(meta.origen, "whatsapp")

        response = self.client.get("/clientes")
        body = response.get_data(as_text=True)
        self.assertIn("Manual Colab", body)
        self.assertIn("Free por colab", body)

        response = self.client.get("/cliente/manual-colab@example.test")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Manual Colab", response.get_data(as_text=True))

    def test_crear_cliente_manual_rechaza_datos_minimos_incompletos(self):
        from db.models import CustomerMeta

        self.login()
        self.add_snapshot([])

        response = self.client.post("/clientes/manual", data={
            "manual_nombre": "",
            "email": "incompleto@example.test",
            "manual_fecha_alta": "2026-06-04",
            "tipo_cliente": "colab_descuento",
            "manual_estado": "activo",
            "origen": "whatsapp",
        })

        self.assertEqual(response.status_code, 302)
        self.assertIn("/clientes", response.location)
        with self.app.app_context():
            meta = CustomerMeta.query.filter_by(email="incompleto@example.test").first()
            self.assertIsNone(meta)

    def test_cliente_manual_no_duplica_si_email_existe_en_snapshot_real(self):
        from db import db
        from db.models import CustomerMeta

        self.login()
        self.add_snapshot([self.customer_row(nombre="Nombre Stripe", email="dup@example.test")])
        with self.app.app_context():
            db.session.add(CustomerMeta(
                email="dup@example.test",
                manual_customer=True,
                manual_nombre="Nombre Manual",
                manual_fecha_alta="2026-06-04",
                manual_estado="activo",
                tipo_cliente="colab_descuento",
            ))
            db.session.commit()

        response = self.client.get("/clientes")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(body.count('class="client-name" href="/cliente/dup@example.test"'), 1)
        self.assertIn("Nombre Manual", body)
        self.assertNotIn("Nombre Stripe", body)
        self.assertIn("Colab con descuento", body)

    def test_ficha_permita_marcar_cliente_como_inactivo(self):
        from db.models import CustomerMeta

        self.login()
        self.add_snapshot([self.customer_row(nombre="Cliente Ocultable", email="ocultable@example.test")])

        response = self.client.get("/cliente/ocultable@example.test")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('action="/cliente/ocultable@example.test/inactivar"', body)
        self.assertNotIn("Marcar inactivo", body)

        response = self.client.post("/cliente/ocultable@example.test/inactivar")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/clientes", response.location)
        with self.app.app_context():
            meta = CustomerMeta.query.filter_by(email="ocultable@example.test").one()
            self.assertEqual(meta.manual_estado, "inactivo")

        response = self.client.get("/clientes")
        self.assertNotIn("Cliente Ocultable", response.get_data(as_text=True))

    def test_ficha_origen_instagram_permita_elegir_idioma(self):
        self.login()
        self.add_snapshot([self.customer_row()])

        response = self.client.get("/cliente/cliente-z@example.test")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('name="origen_base"', body)
        self.assertIn('name="instagram_variante"', body)
        origen_form = body[body.index('action="/cliente/cliente-z@example.test/origen"'):]
        origen_form = origen_form[:origen_form.index("</form>")]
        origen_select = origen_form[origen_form.index('name="origen_base"'):]
        origen_select = origen_select[:origen_select.index("</select>")]
        self.assertNotIn('value="ig_en"', origen_select)

        response = self.client.post(
            "/cliente/cliente-z@example.test/origen",
            data={"origen_base": "instagram", "instagram_variante": "ig_es"},
        )

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            from db.models import CustomerMeta
            meta = CustomerMeta.query.filter_by(email="cliente-z@example.test").one()
            self.assertEqual(meta.origen, "ig_es")

    def test_dashboard_no_muestra_finanzas_ni_gastos(self):
        self.login()

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertNotIn("Gastos", body)
        self.assertNotIn("MRR", body)
        self.assertNotIn("Stripe", body)
        self.assertNotIn("Mercury", body)

    def test_dashboard_usa_layout_core_redisenado(self):
        self.login()
        self.add_snapshot([
            self.customer_row(nombre="Cliente Activo", email="activo@example.test"),
            {**self.customer_row(nombre="Cliente Trial", email="trial@example.test"), "estado": "trial"},
            {**self.customer_row(nombre="Cliente Impago", email="impago@example.test"), "estado": "impago"},
        ])

        response = self.client.get("/?preset=todo")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('class="dashboard-page page polish-v5"', body)
        self.assertIn('class="page-head dashboard-head"', body)
        self.assertIn('class="dashboard-kpi-strip dashboard-kpi-grid"', body)
        self.assertIn('class="dashboard-main-grid dashboard-chart-row v5-dashboard-grid"', body)
        self.assertIn('class="dashboard-main-grid dashboard-ops-row v5-dashboard-grid"', body)
        self.assertIn('class="dashboard-action-panel panel"', body)
        self.assertIn("Requiere accion", body)
        self.assertIn('href="/bandeja"', body)
        self.assertIn('href="/clientes?estado=impago"', body)
        self.assertIn('href="/clientes?estado=trial"', body)
        self.assertIn('class="base-state-grid"', body)

    def test_dashboard_inicio_pulido_muestra_kpis_en_grilla_y_tickets_reales(self):
        import datetime as dt
        from pathlib import Path

        from db import db
        from db.models import CustomerReminder, Interaccion

        self.login()
        self.add_snapshot([
            self.customer_row(nombre="Cliente Activo", email="activo@example.test"),
            {**self.customer_row(nombre="Cliente Trial", email="trial@example.test"), "estado": "trial"},
            {**self.customer_row(nombre="Cliente Impago", email="impago@example.test"), "estado": "impago"},
        ])
        with self.app.app_context():
            Interaccion.query.filter(Interaccion.customer_email.like("%@example.test")).delete(synchronize_session=False)
            CustomerReminder.query.filter(CustomerReminder.customer_email.like("%@example.test")).delete(synchronize_session=False)
            db.session.add(Interaccion(
                customer_email="activo@example.test",
                tipo="solicitud",
                texto="Ticket abierto uno",
                estado_gestion="abierta",
                created_at=dt.datetime.now(dt.timezone.utc),
            ))
            db.session.add(Interaccion(
                customer_email="trial@example.test",
                tipo="queja",
                texto="Ticket abierto dos",
                estado_gestion="en_gestion",
                created_at=dt.datetime.now(dt.timezone.utc),
            ))
            db.session.add(Interaccion(
                customer_email="impago@example.test",
                tipo="solicitud",
                texto="Ticket resuelto",
                estado_gestion="resuelta",
                resuelta=True,
                resolved_at=dt.datetime.now(dt.timezone.utc),
                created_at=dt.datetime.now(dt.timezone.utc),
            ))
            db.session.add(CustomerReminder(
                customer_email="activo@example.test",
                texto="Tarea activa Inicio",
                due_date="2026-06-04",
                assignee="Luis",
            ))
            db.session.add(CustomerReminder(
                customer_email="trial@example.test",
                texto="Tarea completada Inicio",
                due_date="2026-06-04",
                assignee="Nicky",
                completed_at=dt.datetime.now(dt.timezone.utc),
            ))
            db.session.commit()

        response = self.client.get("/?preset=todo")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('class="dashboard-kpi-strip dashboard-kpi-grid"', body)
        self.assertIn('class="periodo-bar dashboard-period dashboard-period-compact"', body)
        self.assertIn('class="dashboard-main-grid dashboard-chart-row v5-dashboard-grid"', body)
        self.assertIn('class="dashboard-main-grid dashboard-ops-row v5-dashboard-grid"', body)
        self.assertIn('class="panel dashboard-chart-panel dashboard-channel-panel"', body)
        self.assertIn('class="panel dashboard-state-panel"', body)
        self.assertNotIn("Ver bandeja", body)
        self.assertLess(body.index("chartSerie"), body.index("chartCanal"))
        self.assertLess(body.index("chartCanal"), body.index("Requiere accion"))
        self.assertLess(body.index("Requiere accion"), body.index("Estado actual de la base"))
        tickets_row = body[body.index("Tickets abiertos"):]
        tickets_row = tickets_row[:tickets_row.index("</a>")]
        self.assertIn("<b>2</b>", tickets_row)
        self.assertNotIn("<b>CS</b>", tickets_row)
        tareas_start = body.rindex('<a class="action-row"', 0, body.index("Tareas pendientes"))
        tareas_row = body[tareas_start:]
        tareas_row = tareas_row[:tareas_row.index("</a>")]
        self.assertIn('href="/bandeja"', tareas_row)
        self.assertIn("<b>1</b>", tareas_row)

        css = Path("static/style.css").read_text(encoding="utf-8")
        grid_rule_start = css.index(".dashboard-kpi-grid")
        grid_rule = css[grid_rule_start:css.index("}", grid_rule_start)]
        self.assertIn("display: grid", grid_rule)
        self.assertIn(".dashboard-chart-row", css)
        self.assertIn(".dashboard-ops-row", css)
        ops_rule_start = css.index(".dashboard-ops-row")
        ops_rule = css[ops_rule_start:css.index("}", ops_rule_start)]
        self.assertIn("align-items: stretch", ops_rule)
        self.assertIn(".dashboard-state-panel", css)

    def test_bandeja_muestra_cancelaciones_programadas_y_riesgos_manuales_de_churn(self):
        import datetime as dt

        from db import db
        from db.models import Interaccion

        self.login()
        scheduled = {
            **self.customer_row(nombre="Cancelacion Programada", email="scheduled@example.test"),
            "cancelacion_programada": True,
            "cancelacion_fecha": "10/06/2026",
            "cancelacion_fecha_raw": "2026-06-10T00:00:00+00:00",
        }
        manual = self.customer_row(nombre="Riesgo Manual", email="manual@example.test")
        self.add_snapshot([scheduled, manual])
        with self.app.app_context():
            db.session.add(Interaccion(
                customer_email="manual@example.test",
                tipo="churn",
                texto="Pidio cancelar si no mejora el soporte",
                created_at=dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=1),
            ))
            db.session.commit()

        response = self.client.get("/bandeja")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Riesgo de churn (2)", body)
        self.assertIn("Cancelacion Programada", body)
        self.assertIn("cancelacion programada", body)
        self.assertIn("Riesgo Manual", body)
        self.assertIn("Pidio cancelar si no mejora el soporte", body)

    def test_bandeja_usa_layout_operativo_redisenado(self):
        from db import db
        from db.models import CustomerReminder

        self.login()
        self.add_snapshot([
            {**self.customer_row(nombre="Cliente Impago", email="impago@example.test"), "estado": "impago"},
            {**self.customer_row(nombre="Cliente Trial", email="trial@example.test"), "estado": "trial"},
        ])
        with self.app.app_context():
            db.session.add(CustomerReminder(
                customer_email="trial@example.test",
                due_date="2026-06-15",
                texto="Revisar trial antes del cierre",
            ))
            db.session.commit()

        response = self.client.get("/bandeja")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('class="inbox-page page polish-v5"', body)
        self.assertIn('class="page-head inbox-head"', body)
        self.assertIn('class="inbox-summary"', body)
        self.assertIn('class="tag tag-churn"', body)
        self.assertIn('class="tag tag-danger"', body)
        self.assertIn('class="tag tag-warning"', body)
        self.assertIn('class="tag tag-tasks"', body)
        self.assertIn("0 churn", body)
        self.assertIn('class="inbox-buckets v5-panel-stack"', body)
        self.assertIn('class="inbox-ops-panel panel"', body)
        ops_panel = body[body.index('class="inbox-ops-panel panel"'):body.index('class="inbox-buckets v5-panel-stack"')]
        self.assertNotIn("Nueva tarea", ops_panel)
        self.assertIn('class="filters-form task-filters"', ops_panel)
        self.assertIn("Fecha", ops_panel)
        self.assertIn("Asignado", ops_panel)
        self.assertIn("Estado", ops_panel)
        self.assertIn(">Filtrar</button>", ops_panel)
        self.assertIn('class="task-command-panel compact-task-command"', body)
        self.assertLess(body.index('class="filters-form task-filters"'), body.index('class="task-command-panel compact-task-command"'))
        self.assertIn('class="inbox-panel panel tone-tasks"', body)
        self.assertIn('class="inbox-panel panel secondary-panel tone-churn"', body)
        self.assertIn('class="inbox-panel panel secondary-panel tone-danger"', body)
        self.assertIn('class="inbox-panel panel secondary-panel tone-onboarding"', body)
        self.assertIn('class="inbox-panel panel secondary-panel tone-warning"', body)
        self.assertIn("<details", body)
        self.assertIn("<summary", body)
        self.assertIn('class="inbox-row"', body)
        self.assertIn("Bandeja operativa", body)
        self.assertIn("Cliente Impago", body)
        self.assertIn("Cliente Trial", body)
        self.assertIn("Completar", body)

    def test_bandeja_premium_colapsa_nueva_tarea_y_no_duplica_onboarding(self):
        from pathlib import Path

        from db import db
        from db.models import CustomerReminder

        self.login()
        self.add_snapshot([
            {**self.customer_row(nombre="Cliente Impago", email="impago@example.test"), "estado": "impago"},
            {**self.customer_row(nombre="Cliente Trial", email="trial@example.test"), "estado": "trial"},
            self.customer_row(nombre="Cliente Bienvenida", email="bienvenida@example.test"),
        ])
        with self.app.app_context():
            db.session.add(CustomerReminder(
                customer_email="impago@example.test",
                due_date="2026-06-02",
                texto="Llamar por deuda",
                assignee="Luis",
            ))
            db.session.add(CustomerReminder(
                customer_email="trial@example.test",
                due_date="2026-06-04",
                texto="Revisar trial",
                assignee="Dalila",
            ))
            db.session.commit()

        response = self.client.get("/bandeja?date=2026-06-04")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('class="task-command-panel compact-task-command"', body)
        self.assertIn("<summary", body)
        self.assertIn('action="/tareas"', body)
        self.assertIn('name="texto"', body)
        self.assertIn('name="due_date"', body)
        self.assertIn('name="assignee"', body)
        self.assertIn('name="customer_email"', body)
        self.assertIn("Vencidas (", body)
        self.assertIn("Hoy (", body)
        self.assertIn("Proximas (", body)
        self.assertNotIn("Para la fecha", body)
        self.assertIn("Onboarding pendiente (", body)
        self.assertIn("Bienvenida pendiente", body)
        self.assertLess(body.index("Tareas ("), body.index("Riesgo de churn"))
        self.assertLess(body.index("Riesgo de churn"), body.index("Impagos ("))
        self.assertLess(body.index("Impagos ("), body.index("Onboarding pendiente ("))
        self.assertLess(body.index("Onboarding pendiente ("), body.index("En trial ("))
        self.assertIn('class="task-group task-group-overdue"', body)
        self.assertIn('class="inbox-panel panel tone-tasks"', body)
        self.assertIn('class="inbox-panel panel secondary-panel tone-churn"', body)
        self.assertIn('class="inbox-panel panel secondary-panel tone-danger"', body)
        self.assertIn('class="inbox-panel panel secondary-panel tone-onboarding"', body)
        self.assertIn('class="inbox-panel panel secondary-panel tone-warning"', body)
        self.assertIn("Sin pendientes.", body)

        css = Path("static/style.css").read_text(encoding="utf-8")
        self.assertIn(".tag-churn", css)
        self.assertIn(".tag-tasks", css)
        self.assertIn(".tag-onboarding", css)
        self.assertIn(".tag-warning", css)
        self.assertIn(".tag-danger", css)
        self.assertIn(".inbox-panel.tone-tasks .panel-head", css)
        self.assertIn(".inbox-panel.tone-churn .panel-head", css)
        self.assertIn(".inbox-panel.tone-onboarding .panel-head", css)
        self.assertIn(".inbox-ops-panel", css)
        filters_button_rule_start = css.index(".task-filters button")
        filters_button_rule = css[filters_button_rule_start:css.index("}", filters_button_rule_start)]
        self.assertIn("width: auto", filters_button_rule)
        self.assertIn("justify-self: start", filters_button_rule)

    def test_bandeja_mobile_muestra_filtros_compactos_sin_boton_full_width(self):
        from pathlib import Path

        css = Path("static/style.css").read_text(encoding="utf-8")
        mobile_css = css[css.index("@media (max-width: 820px)"):]

        self.assertIn(".inbox-ops-panel .task-filters", mobile_css)
        mobile_filters_start = mobile_css.index(".inbox-ops-panel .task-filters")
        mobile_filters_rule = mobile_css[mobile_filters_start:mobile_css.index("}", mobile_filters_start)]
        self.assertIn("grid-template-columns: repeat(2, minmax(0, 1fr))", mobile_filters_rule)
        self.assertIn("align-items: end", mobile_filters_rule)

        mobile_filter_label_start = mobile_css.index(".inbox-ops-panel .task-filters label")
        mobile_filter_label_rule = mobile_css[mobile_filter_label_start:mobile_css.index("}", mobile_filter_label_start)]
        self.assertIn("min-width: 0", mobile_filter_label_rule)

        mobile_filter_button_start = mobile_css.index(".inbox-ops-panel .task-filters button")
        mobile_filter_button_rule = mobile_css[mobile_filter_button_start:mobile_css.index("}", mobile_filter_button_start)]
        self.assertIn("width: auto", mobile_filter_button_rule)
        self.assertIn("min-width: 0", mobile_filter_button_rule)
        self.assertIn("grid-column: auto", mobile_filter_button_rule)

    def test_bandeja_con_customer_abre_tareas_y_nueva_tarea_preseleccionada(self):
        self.login()
        self.add_snapshot([self.customer_row(nombre="Ana Cliente", email="ana@example.test")])

        response = self.client.get("/bandeja?customer=ana@example.test")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('class="inbox-ops-panel panel"', body)
        self.assertIn('class="inbox-panel panel tone-tasks" open', body)
        self.assertLess(body.index("Tareas ("), body.index('class="task-command-panel compact-task-command"'))
        self.assertLess(body.index('class="task-command-panel compact-task-command"'), body.index('value="ana@example.test" selected>Ana Cliente'))
        self.assertIn('value="ana@example.test" selected>Ana Cliente', body)

    def test_ficha_crea_tarea_con_fecha_texto_y_asignado(self):
        from db.models import CustomerReminder

        self.login()
        self.add_snapshot([self.customer_row()])

        response = self.client.get("/cliente/cliente-z@example.test")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Crear tarea", body)
        self.assertIn('href="/bandeja?customer=cliente-z@example.test"', body)
        self.assertNotIn('action="/cliente/cliente-z@example.test/recordatorios"', body)

        response = self.client.post(
            "/cliente/cliente-z@example.test/recordatorios",
            data={"due_date": "2026-06-15", "texto": "Escribirle para revisar avance", "assignee": "Luis"},
        )

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            reminder = CustomerReminder.query.filter_by(customer_email="cliente-z@example.test").one()
            self.assertEqual(reminder.due_date, "2026-06-15")
            self.assertEqual(reminder.texto, "Escribirle para revisar avance")
            self.assertEqual(reminder.assignee, "Luis")
            self.assertIsNone(reminder.completed_at)

    def test_ficha_usa_layout_core_en_columnas(self):
        self.login()
        self.add_snapshot([self.customer_row()])

        response = self.client.get("/cliente/cliente-z@example.test")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('class="customer-page page polish-v5"', body)
        self.assertIn('class="page-head customer-head"', body)
        self.assertIn('class="customer-head-copy"', body)
        self.assertIn('class="customer-head-actions"', body)
        self.assertIn('class="btn-primary" href="/solicitudes?customer=cliente-z@example.test"', body)
        self.assertIn('class="btn-primary" href="/bandeja?customer=cliente-z@example.test"', body)
        self.assertIn('class="btn-sync" href="/clientes"', body)
        self.assertIn('class="customer-health-strip customer-operational-summary"', body)
        self.assertIn('class="customer-command-grid v5-two-column"', body)
        self.assertIn('class="customer-main-column"', body)
        self.assertIn('class="customer-side-column"', body)
        self.assertIn('action="/cliente/cliente-z@example.test/suscripcion"', body)
        self.assertIn('action="/cliente/cliente-z@example.test/contacto"', body)
        self.assertNotIn('action="/cliente/cliente-z@example.test/interaccion"', body)
        self.assertNotIn('action="/cliente/cliente-z@example.test/recordatorios"', body)
        with open("static/style.css", encoding="utf-8") as css_file:
            css = css_file.read()
        self.assertIn(".btn-primary", css)
        self.assertIn(".customer-head-actions .btn-primary", css)

    def test_ficha_operativa_muestra_salud_contacto_links_y_no_urls_reportadas(self):
        import app as app_module
        from db import db
        from db.models import CustomerMeta, CustomerReminder, Interaccion

        self.login()
        customer = {
            **self.customer_row(nombre="Cliente Operativo", email="operativo@example.test"),
            "account_ids": ["acc-1"],
            "cuenta_activo_recurrente": True,
        }
        self.add_snapshot([customer])
        with self.app.app_context():
            db.session.add(CustomerMeta(
                email="operativo@example.test",
                whatsapp="+54 9 11 1111 2222",
                usuario="@operativo",
                manager="Dalila",
                manual_nombre="Nombre Operativo",
            ))
            db.session.add(Interaccion(
                customer_email="operativo@example.test",
                tipo="nota",
                texto="Nota operativa",
            ))
            db.session.add(Interaccion(
                customer_email="operativo@example.test",
                tipo="solicitud",
                texto="Pide revisar enlaces",
                categoria="envia_links",
            ))
            db.session.add(CustomerReminder(
                customer_email="operativo@example.test",
                texto="Llamar",
                due_date="2026-06-12",
                assignee="Luis",
            ))
            db.session.commit()

        original = app_module.salud_de_cuentas
        app_module.salud_de_cuentas = lambda account_ids: {
            "checks": [{"accountId": "acc-1", "status": "ok", "resultCount": 3}],
            "detected_pendientes": 2,
            "detected_gestionados": 4,
            "impersonations_pendientes": 1,
            "impersonations_gestionadas": 5,
            "manual_reports": {
                "count": 3,
                "last_reported_at": "2026-06-02",
                "repeated_count": 1,
                "sample_url": "https://pirata.example.test/video",
            },
        }
        try:
            response = self.client.get("/cliente/operativo@example.test")
        finally:
            app_module.salud_de_cuentas = original

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Suscripcion y salud", body)
        self.assertIn("Pirateria pendiente", body)
        self.assertIn("Suplantaciones gestionadas", body)
        self.assertIn("Contacto e identificacion", body)
        self.assertIn("<h1>Nombre Operativo</h1>", body)
        self.assertIn("Antes: Cliente Operativo", body)
        self.assertIn("Dalila", body)
        self.assertNotIn("Estado WhatsApp", body)
        self.assertNotIn("Links reportados por el cliente", body)
        self.assertIn("3 reportes", body)
        self.assertIn("2026-06-02", body)
        self.assertIn("1 repetido", body)
        self.assertNotIn("pirata.example.test", body)
        self.assertIn("Historial operativo", body)
        self.assertIn("Nota operativa", body)
        self.assertIn("Pide revisar enlaces", body)
        self.assertIn("Llamar", body)
        self.assertIn('href="/solicitudes?customer=operativo@example.test"', body)
        self.assertIn('href="/bandeja?customer=operativo@example.test"', body)
        self.assertNotIn("<h2>Acciones</h2>", body)
        self.assertNotIn("Marcar inactivo", body)
        self.assertNotIn("Nuevo contacto o solicitud", body)
        self.assertNotIn('action="/cliente/operativo@example.test/interaccion"', body)
        self.assertNotIn('action="/cliente/operativo@example.test/recordatorios"', body)

    def test_bandeja_muestra_tareas_activas_y_permite_completarlas(self):
        from db import db
        from db.models import CustomerReminder

        self.login()
        self.add_snapshot([self.customer_row(nombre="Cliente Recordado")])
        with self.app.app_context():
            reminder = CustomerReminder(
                customer_email="cliente-z@example.test",
                due_date="2026-06-15",
                texto="Mandar seguimiento de WhatsApp",
                assignee="Dalila",
            )
            db.session.add(reminder)
            db.session.commit()
            reminder_id = reminder.id

        response = self.client.get("/bandeja")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Tareas (2)", body)
        self.assertIn("Cliente Recordado", body)
        self.assertIn("Mandar seguimiento de WhatsApp", body)
        self.assertIn("Dalila", body)
        self.assertIn("Bienvenida pendiente", body)
        self.assertIn("Nicky", body)
        self.assertIn("15/06/2026", body)
        self.assertIn("Completar", body)

        response = self.client.post(f"/recordatorios/{reminder_id}/completar")

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            reminder = db.session.get(CustomerReminder, reminder_id)
            self.assertIsNotNone(reminder.completed_at)

        response = self.client.get("/bandeja")
        body = response.get_data(as_text=True)
        self.assertIn("Tareas (1)", body)
        self.assertNotIn("Mandar seguimiento de WhatsApp", body)

    def test_bandeja_crea_tarea_de_bienvenida_para_nicky_sin_duplicar(self):
        from db.models import CustomerReminder

        self.login()
        self.add_snapshot([self.customer_row(nombre="Cliente Nuevo")])

        response = self.client.get("/bandeja?date=2026-05-01")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Bienvenida pendiente", body)
        self.assertIn("Cliente Nuevo", body)
        self.assertIn("Nicky", body)
        self.assertIn("Vencida", body)
        with self.app.app_context():
            task = CustomerReminder.query.filter_by(customer_email="cliente-z@example.test", source="onboarding").one()
            self.assertEqual(task.texto, "Bienvenida pendiente")
            self.assertEqual(task.assignee, "Nicky")
            self.assertEqual(task.due_date, "2026-05-01")
            self.assertIsNone(task.completed_at)

        self.client.get("/bandeja?date=2026-05-01")
        with self.app.app_context():
            self.assertEqual(CustomerReminder.query.filter_by(customer_email="cliente-z@example.test", source="onboarding").count(), 1)

    def test_completar_tarea_de_bienvenida_marca_onboarding_hecho(self):
        from db import db
        from db.models import CustomerMeta, CustomerReminder

        self.login()
        self.add_snapshot([self.customer_row(nombre="Cliente Nuevo")])
        self.client.get("/bandeja?date=2026-05-01")
        with self.app.app_context():
            task = CustomerReminder.query.filter_by(customer_email="cliente-z@example.test", source="onboarding").one()
            task_id = task.id

        response = self.client.post(f"/recordatorios/{task_id}/completar")

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            task = db.session.get(CustomerReminder, task_id)
            meta = CustomerMeta.query.filter_by(email="cliente-z@example.test").one()
            self.assertIsNotNone(task.completed_at)
            self.assertTrue(meta.onboarding_hecho)

        response = self.client.get("/bandeja?date=2026-05-01")
        body = response.get_data(as_text=True)
        self.assertNotIn("Bienvenida pendiente", body)

    def test_tarea_requiere_fecha_texto_y_asignado_valido(self):
        from db.models import CustomerReminder

        self.login()
        self.add_snapshot([self.customer_row()])

        response = self.client.post(
            "/cliente/cliente-z@example.test/recordatorios",
            data={"due_date": "", "texto": "   "},
        )

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            self.assertEqual(CustomerReminder.query.filter_by(customer_email="cliente-z@example.test").count(), 0)

        response = self.client.post(
            "/cliente/cliente-z@example.test/recordatorios",
            data={"due_date": "2026-06-15", "texto": "Escribirle", "assignee": "Persona Invalida"},
        )

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            self.assertEqual(CustomerReminder.query.filter_by(customer_email="cliente-z@example.test").count(), 0)

    def test_tareas_filtra_por_fecha_asignado_y_marca_vencidas(self):
        from db import db
        from db.models import CustomerReminder

        self.login()
        self.add_snapshot([
            self.customer_row(nombre="Cliente Vencido", email="vencido@example.test"),
            self.customer_row(nombre="Cliente Futuro", email="futuro@example.test"),
        ])
        with self.app.app_context():
            db.session.add(CustomerReminder(
                customer_email="vencido@example.test",
                due_date="2026-06-03",
                texto="Llamar por impago",
                assignee="Luis",
            ))
            db.session.add(CustomerReminder(
                customer_email="futuro@example.test",
                due_date="2026-06-15",
                texto="Enviar resumen mensual",
                assignee="Frank",
            ))
            db.session.commit()

        response = self.client.get("/bandeja?assignee=Luis&date=2026-06-03")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Tareas", body)
        self.assertIn('action="/tareas"', body)
        self.assertIn("Cliente Vencido", body)
        self.assertIn("Llamar por impago", body)
        self.assertIn("Luis", body)
        self.assertIn("Vencida", body)
        self.assertNotIn("Enviar resumen mensual", body)

    def test_tareas_redirige_a_bandeja_con_filtros(self):
        self.login()

        response = self.client.get("/tareas?assignee=Luis&date=2026-06-03")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/bandeja?assignee=Luis&date=2026-06-03", response.location)

    def test_bandeja_crea_tarea_generica_y_vinculada(self):
        from db.models import CustomerReminder

        self.login()
        self.add_snapshot([self.customer_row(nombre="Cliente Tarea")])

        response = self.client.post(
            "/tareas",
            data={
                "due_date": "2026-06-20",
                "texto": "Revisar SOP interno",
                "assignee": "Nicky",
                "customer_email": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            task = CustomerReminder.query.filter_by(texto="Revisar SOP interno").one()
            self.assertEqual(task.customer_email, "")
            self.assertEqual(task.assignee, "Nicky")

        response = self.client.get("/bandeja")
        body = response.get_data(as_text=True)
        self.assertIn("Revisar SOP interno", body)
        self.assertIn("Sin cliente", body)

        response = self.client.post(
            "/tareas",
            data={
                "due_date": "2026-06-21",
                "texto": "Enviar propuesta",
                "assignee": "Frank",
                "customer_email": "cliente-z@example.test",
            },
        )

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            task = CustomerReminder.query.filter_by(texto="Enviar propuesta").one()
            self.assertEqual(task.customer_email, "cliente-z@example.test")
            self.assertEqual(task.assignee, "Frank")

    def test_bandeja_renderiza_edicion_plegada_para_tareas_activas(self):
        from db import db
        from db.models import CustomerReminder

        self.login()
        self.add_snapshot([self.customer_row(nombre="Cliente Editable")])
        with self.app.app_context():
            db.session.add(CustomerReminder(
                customer_email="cliente-z@example.test",
                due_date="2026-06-20",
                texto="Editar seguimiento",
                assignee="Luis",
            ))
            db.session.commit()
            task_id = CustomerReminder.query.filter_by(texto="Editar seguimiento").one().id

        response = self.client.get("/bandeja?date=2026-06-20")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Editar", body)
        self.assertIn(f'action="/recordatorios/{task_id}/editar"', body)
        self.assertIn(f'name="texto" value="Editar seguimiento"', body)
        self.assertIn('name="due_date" value="2026-06-20"', body)
        self.assertIn('name="assignee"', body)
        self.assertIn('name="customer_email"', body)
        self.assertIn("Sin cliente", body)

    def test_editar_tarea_manual_cambia_titulo_fecha_asignado_y_cliente(self):
        from db import db
        from db.models import CustomerReminder

        self.login()
        self.add_snapshot([
            self.customer_row(nombre="Cliente A", email="cliente-a@example.test"),
            self.customer_row(nombre="Cliente B", email="cliente-b@example.test"),
        ])
        with self.app.app_context():
            reminder = CustomerReminder(
                customer_email="cliente-a@example.test",
                due_date="2026-06-20",
                texto="Titulo anterior",
                assignee="Luis",
            )
            db.session.add(reminder)
            db.session.commit()
            reminder_id = reminder.id

        response = self.client.post(
            f"/recordatorios/{reminder_id}/editar",
            data={
                "texto": "Titulo actualizado",
                "due_date": "2026-06-25",
                "assignee": "Frank",
                "customer_email": "cliente-b@example.test",
            },
            headers={"Referer": "/bandeja?assignee=Luis&date=2026-06-20"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/bandeja?assignee=Luis&date=2026-06-20", response.location)
        with self.app.app_context():
            reminder = db.session.get(CustomerReminder, reminder_id)
            self.assertEqual(reminder.texto, "Titulo actualizado")
            self.assertEqual(reminder.due_date, "2026-06-25")
            self.assertEqual(reminder.assignee, "Frank")
            self.assertEqual(reminder.customer_email, "cliente-b@example.test")

    def test_editar_tarea_manual_permite_quitar_cliente(self):
        from db import db
        from db.models import CustomerReminder

        self.login()
        self.add_snapshot([self.customer_row(nombre="Cliente A", email="cliente-a@example.test")])
        with self.app.app_context():
            reminder = CustomerReminder(
                customer_email="cliente-a@example.test",
                due_date="2026-06-20",
                texto="Quitar cliente",
                assignee="Luis",
            )
            db.session.add(reminder)
            db.session.commit()
            reminder_id = reminder.id

        response = self.client.post(
            f"/recordatorios/{reminder_id}/editar",
            data={
                "texto": "Quitar cliente",
                "due_date": "2026-06-20",
                "assignee": "Luis",
                "customer_email": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            reminder = db.session.get(CustomerReminder, reminder_id)
            self.assertEqual(reminder.customer_email, "")

    def test_editar_tarea_manual_rechaza_asignado_invalido_sin_persistir(self):
        from db import db
        from db.models import CustomerReminder

        self.login()
        self.add_snapshot([self.customer_row(nombre="Cliente A", email="cliente-a@example.test")])
        with self.app.app_context():
            reminder = CustomerReminder(
                customer_email="cliente-a@example.test",
                due_date="2026-06-20",
                texto="Original",
                assignee="Luis",
            )
            db.session.add(reminder)
            db.session.commit()
            reminder_id = reminder.id

        response = self.client.post(
            f"/recordatorios/{reminder_id}/editar",
            data={
                "texto": "No debe guardar",
                "due_date": "2026-06-25",
                "assignee": "Persona Invalida",
                "customer_email": "cliente-a@example.test",
            },
        )

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            reminder = db.session.get(CustomerReminder, reminder_id)
            self.assertEqual(reminder.texto, "Original")
            self.assertEqual(reminder.due_date, "2026-06-20")
            self.assertEqual(reminder.assignee, "Luis")

    def test_editar_tarea_manual_rechaza_cliente_invalido_sin_persistir(self):
        from db import db
        from db.models import CustomerReminder

        self.login()
        self.add_snapshot([self.customer_row(nombre="Cliente A", email="cliente-a@example.test")])
        with self.app.app_context():
            reminder = CustomerReminder(
                customer_email="cliente-a@example.test",
                due_date="2026-06-20",
                texto="Original",
                assignee="Luis",
            )
            db.session.add(reminder)
            db.session.commit()
            reminder_id = reminder.id

        response = self.client.post(
            f"/recordatorios/{reminder_id}/editar",
            data={
                "texto": "No debe guardar",
                "due_date": "2026-06-25",
                "assignee": "Frank",
                "customer_email": "fantasma@example.test",
            },
        )

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            reminder = db.session.get(CustomerReminder, reminder_id)
            self.assertEqual(reminder.texto, "Original")
            self.assertEqual(reminder.due_date, "2026-06-20")
            self.assertEqual(reminder.assignee, "Luis")
            self.assertEqual(reminder.customer_email, "cliente-a@example.test")

    def test_editar_tarea_onboarding_solo_reasigna_responsable(self):
        from db import db
        from db.models import CustomerReminder

        self.login()
        self.add_snapshot([self.customer_row(nombre="Cliente Nuevo", email="nuevo@example.test")])
        self.client.get("/bandeja?date=2026-05-01")
        with self.app.app_context():
            reminder = CustomerReminder.query.filter_by(customer_email="nuevo@example.test", source="onboarding").one()
            reminder_id = reminder.id

        response = self.client.post(
            f"/recordatorios/{reminder_id}/editar",
            data={
                "texto": "No cambiar bienvenida",
                "due_date": "2026-06-25",
                "assignee": "Dalila",
                "customer_email": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            reminder = db.session.get(CustomerReminder, reminder_id)
            self.assertEqual(reminder.texto, "Bienvenida pendiente")
            self.assertEqual(reminder.due_date, "2026-05-01")
            self.assertEqual(reminder.customer_email, "nuevo@example.test")
            self.assertEqual(reminder.source, "onboarding")
            self.assertEqual(reminder.assignee, "Dalila")

    def test_editar_tarea_completada_no_persiste_cambios(self):
        import datetime as dt

        from db import db
        from db.models import CustomerReminder

        self.login()
        self.add_snapshot([self.customer_row(nombre="Cliente A", email="cliente-a@example.test")])
        with self.app.app_context():
            reminder = CustomerReminder(
                customer_email="cliente-a@example.test",
                due_date="2026-06-20",
                texto="Completada",
                assignee="Luis",
                completed_at=dt.datetime.now(dt.timezone.utc),
            )
            db.session.add(reminder)
            db.session.commit()
            reminder_id = reminder.id

        response = self.client.post(
            f"/recordatorios/{reminder_id}/editar",
            data={
                "texto": "No debe cambiar",
                "due_date": "2026-06-25",
                "assignee": "Frank",
                "customer_email": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            reminder = db.session.get(CustomerReminder, reminder_id)
            self.assertEqual(reminder.texto, "Completada")
            self.assertEqual(reminder.due_date, "2026-06-20")
            self.assertEqual(reminder.assignee, "Luis")
            self.assertEqual(reminder.customer_email, "cliente-a@example.test")

    def test_base_no_muestra_nav_tareas_separada(self):
        self.login()

        response = self.client.get("/bandeja")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('href="/bandeja">Bandeja', body)
        self.assertNotIn('href="/tareas">Tareas', body)

    def test_base_shell_autenticado_usa_logo_sin_topbar_ni_buscador_global(self):
        self.login()

        response = self.client.get("/bandeja")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('class="sidebar-brand"', body)
        self.assertIn('alt="Traqeer"', body)
        self.assertNotIn("<span>Customers Dashboard</span>", body)
        self.assertNotIn('class="topbar"', body)
        self.assertNotIn('class="global-search"', body)
        self.assertNotIn('placeholder="Buscar cliente, email, usuario o WhatsApp"', body)
        sidebar = body[body.index('class="sidebar"'):body.index('</aside>')]
        self.assertIn('action="/sync"', sidebar)
        self.assertIn("Actualizar datos", sidebar)
        self.assertIn('href="/logout"', sidebar)
        self.assertIn("Salir", sidebar)

    def test_base_shell_mobile_expone_header_hamburger_y_drawer_vertical(self):
        self.login()

        response = self.client.get("/bandeja")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('class="mobile-shell-header"', body)
        self.assertIn('aria-label="Abrir menu"', body)
        self.assertIn('class="mobile-menu-toggle"', body)
        self.assertIn('class="mobile-drawer-backdrop"', body)
        self.assertIn('id="mobile-menu"', body)
        self.assertIn('aria-label="Navegacion principal"', body)

        from pathlib import Path

        css = Path("static/style.css").read_text(encoding="utf-8")
        mobile_css = css[css.index("@media (max-width: 820px)"):]
        self.assertIn(".mobile-shell-header", mobile_css)
        self.assertIn("transform: translateX(-100%)", mobile_css)
        self.assertNotIn("overflow-x: auto", mobile_css)

    def test_dashboard_agrupa_variantes_de_instagram(self):
        from db import db
        from db.models import CustomerMeta, Snapshot

        self.login()
        clientes = [
            self.customer_row(nombre="IG EN", email="ig-en@example.test"),
            self.customer_row(nombre="IG ES", email="ig-es@example.test"),
            self.customer_row(nombre="Email", email="email@example.test"),
        ]
        with self.app.app_context():
            db.session.add(Snapshot(payload={
                "test_marker": "solicitudes_directas",
                "clientes": clientes,
                "eventos": {
                    "altas": [
                        {"email": "ig-en@example.test", "fecha": "2026-05-20T00:00:00+00:00"},
                        {"email": "ig-es@example.test", "fecha": "2026-05-21T00:00:00+00:00"},
                        {"email": "email@example.test", "fecha": "2026-05-22T00:00:00+00:00"},
                    ],
                    "bajas": [],
                },
                "resumen": {},
            }))
            db.session.add(CustomerMeta(email="ig-en@example.test", origen="ig_en"))
            db.session.add(CustomerMeta(email="ig-es@example.test", origen="ig_es"))
            db.session.add(CustomerMeta(email="email@example.test", origen="email"))
            db.session.commit()

        response = self.client.get("/?preset=todo&canal=instagram")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('<option value="instagram" selected>Instagram</option>', body)
        self.assertNotIn("Instagram inglés", body)
        self.assertNotIn("Instagram español", body)
        self.assertIn('"labels": ["Instagram"]', body)
        self.assertIn('"valores": [2]', body)

    def test_dashboard_canales_usa_base_actual_recurrentes_y_trials(self):
        from db import db
        from db.models import CustomerMeta, Snapshot

        self.login()
        clientes = [
            {**self.customer_row(nombre="Alta IG", email="alta-ig@example.test"), "estado": "activo"},
            {**self.customer_row(nombre="Trial IG", email="trial-ig@example.test"), "estado": "trial"},
            {**self.customer_row(nombre="Trial Email", email="trial-email@example.test"), "estado": "trial"},
            {**self.customer_row(nombre="One Time", email="one-time@example.test"), "estado": "activo"},
        ]
        with self.app.app_context():
            db.session.add(Snapshot(payload={
                "test_marker": "solicitudes_directas",
                "clientes": clientes,
                "eventos": {
                    "altas": [
                        {"email": "alta-ig@example.test", "fecha": "2026-05-20T00:00:00+00:00"},
                    ],
                    "bajas": [],
                },
                "resumen": {},
            }))
            db.session.add(CustomerMeta(email="alta-ig@example.test", origen="instagram"))
            db.session.add(CustomerMeta(email="trial-ig@example.test", origen="ig_es"))
            db.session.add(CustomerMeta(email="trial-email@example.test", origen="email"))
            db.session.add(CustomerMeta(email="one-time@example.test", origen="telegram", manual_plan="one_time"))
            db.session.commit()

        response = self.client.get("/?preset=todo")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Base actual por canal", body)
        self.assertIn('"labels": ["Email", "Instagram"]', body)
        self.assertIn('"valores": [1, 2]', body)
        self.assertIn("return `${label} · ${value} (${pct}%)`;", body)
        self.assertIn("text: `${label} · ${value} (${pct}%)`", body)
        self.assertIn("const totalCanal = canalData.valores.reduce((a, b) => a + b, 0);", body)
        self.assertIn("canalData.labels.map((label, index) =>", body)

    def test_dashboard_canales_respeta_periodo_custom(self):
        from db import db
        from db.models import CustomerMeta, Snapshot

        self.login()
        clientes = [
            {**self.customer_row(nombre="Alta Mayo", email="alta-mayo@example.test"), "fecha_alta_raw": "2026-05-15T00:00:00+00:00"},
            {**self.customer_row(nombre="Alta Abril", email="alta-abril@example.test"), "fecha_alta_raw": "2026-04-10T00:00:00+00:00"},
            {**self.customer_row(nombre="Trial Mayo", email="trial-mayo@example.test"), "estado": "trial", "fecha_alta_raw": "2026-05-20T00:00:00+00:00"},
            {**self.customer_row(nombre="Manual Mayo", email="manual-mayo@example.test"), "fecha_alta_raw": "2026-05-18T00:00:00+00:00"},
        ]
        with self.app.app_context():
            db.session.add(Snapshot(payload={
                "test_marker": "solicitudes_directas",
                "clientes": clientes,
                "eventos": {
                    "altas": [
                        {"email": "alta-mayo@example.test", "fecha": "2026-05-15T00:00:00+00:00"},
                        {"email": "alta-abril@example.test", "fecha": "2026-04-10T00:00:00+00:00"},
                    ],
                    "bajas": [],
                },
                "resumen": {},
            }))
            db.session.add(CustomerMeta(email="alta-mayo@example.test", origen="instagram"))
            db.session.add(CustomerMeta(email="alta-abril@example.test", origen="telegram"))
            db.session.add(CustomerMeta(email="trial-mayo@example.test", origen="email"))
            db.session.add(CustomerMeta(email="manual-mayo@example.test", origen="telegram"))
            db.session.commit()

        response = self.client.get("/?desde=2026-05-01&hasta=2026-05-31")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Altas y trials por canal", body)
        self.assertIn('"labels": ["Email", "Instagram"]', body)
        self.assertIn('"valores": [1, 1]', body)
        self.assertNotIn('"Telegram"', body)

    def test_dashboard_canales_periodo_ignora_eventos_sin_cliente_actual(self):
        from db import db
        from db.models import CustomerMeta, Snapshot

        self.login()
        clientes = [
            {**self.customer_row(nombre="Alta Actual", email="alta-actual@example.test"), "fecha_alta_raw": "2026-05-15T00:00:00+00:00"},
            {**self.customer_row(nombre="Trial Actual", email="trial-actual@example.test"), "estado": "trial", "fecha_alta_raw": "2026-05-20T00:00:00+00:00"},
        ]
        with self.app.app_context():
            db.session.add(Snapshot(payload={
                "test_marker": "solicitudes_directas",
                "clientes": clientes,
                "eventos": {
                    "altas": [
                        {"email": "alta-actual@example.test", "fecha": "2026-05-15T00:00:00+00:00"},
                        {"email": "viejo-sin-meta@example.test", "fecha": "2026-05-16T00:00:00+00:00"},
                    ],
                    "bajas": [],
                },
                "resumen": {},
            }))
            db.session.add(CustomerMeta(email="alta-actual@example.test", origen="instagram"))
            db.session.add(CustomerMeta(email="trial-actual@example.test", origen="email"))
            db.session.commit()

        response = self.client.get("/?desde=2026-05-01&hasta=2026-05-31")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('"labels": ["Email", "Instagram"]', body)
        self.assertIn('"valores": [1, 1]', body)
        self.assertNotIn('"Sin asignar"', body)

    def test_dashboard_canales_periodo_cuenta_eventos_con_canal_fuera_base_actual(self):
        from db import db
        from db.models import CustomerMeta, Snapshot

        self.login()
        clientes = [
            {**self.customer_row(nombre="Trial Actual", email="trial-actual@example.test"), "estado": "trial", "fecha_alta_raw": "2026-05-21T00:00:00+00:00"},
        ]
        with self.app.app_context():
            db.session.add(Snapshot(payload={
                "test_marker": "solicitudes_directas",
                "clientes": clientes,
                "eventos": {
                    "altas": [
                        {"email": "alta-actual@example.test", "fecha": "2026-05-21T00:00:00+00:00"},
                        {"email": "alta-fuera-base@example.test", "fecha": "2026-05-22T00:00:00+00:00"},
                        {"email": "alta-sin-canal@example.test", "fecha": "2026-05-23T00:00:00+00:00"},
                    ],
                    "bajas": [],
                },
                "resumen": {},
            }))
            db.session.add(CustomerMeta(email="alta-actual@example.test", origen="instagram"))
            db.session.add(CustomerMeta(email="alta-fuera-base@example.test", origen="telegram"))
            db.session.add(CustomerMeta(email="trial-actual@example.test", origen="directo"))
            db.session.commit()

        response = self.client.get("/?desde=2026-05-20&hasta=2026-05-29")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('"labels": ["Instagram", "Telegram", "No se sabe (directo)"]', body)
        self.assertIn('"valores": [1, 1, 1]', body)
        self.assertNotIn('"Sin asignar"', body)

    def test_dashboard_todo_completa_altas_con_recurrentes_actuales(self):
        from db import db
        from db.models import CustomerMeta, Snapshot

        self.login()
        clientes = [
            {**self.customer_row(nombre="Con evento", email="con-evento@example.test"), "fecha_alta_raw": "2026-05-15T00:00:00+00:00"},
            {**self.customer_row(nombre="Sin evento", email="sin-evento@example.test"), "fecha_alta_raw": "2026-05-20T00:00:00+00:00"},
        ]
        with self.app.app_context():
            db.session.add(Snapshot(payload={
                "test_marker": "solicitudes_directas",
                "clientes": clientes,
                "eventos": {
                    "altas": [
                        {"email": "con-evento@example.test", "fecha": "2026-05-15T00:00:00+00:00"},
                    ],
                    "bajas": [
                        {"email": "baja-sin-alta@example.test", "fecha": "2026-05-25T00:00:00+00:00"},
                    ],
                },
                "resumen": {},
            }))
            db.session.add(CustomerMeta(email="con-evento@example.test", origen="instagram"))
            db.session.add(CustomerMeta(email="sin-evento@example.test", origen="email"))
            db.session.commit()

        response = self.client.get("/?preset=todo")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        altas_block = body[body.index('<span class="kpi-label">Altas</span>'):]
        altas_block = altas_block[:altas_block.index("</a>")]
        self.assertIn('<span class="kpi-val">3</span>', altas_block)
        bajas_block = body[body.index('<span class="kpi-label">Bajas</span>'):]
        bajas_block = bajas_block[:bajas_block.index("</a>")]
        self.assertIn('<span class="kpi-val">1</span>', bajas_block)
        neto_block = body[body.index('<span class="kpi-label">Neto</span>'):]
        neto_block = neto_block[:neto_block.index("</div>")]
        self.assertIn('<span class="kpi-val">2</span>', neto_block)
        self.assertIn('"labels": ["Email", "Instagram"]', body)
        self.assertIn('"valores": [1, 1]', body)

        response = self.client.get("/?desde=2026-05-01&hasta=2026-05-31")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        altas_block = body[body.index('<span class="kpi-label">Altas</span>'):]
        altas_block = altas_block[:altas_block.index("</a>")]
        self.assertIn('<span class="kpi-val">1</span>', altas_block)

    def test_dashboard_altas_excluye_trials_en_periodo(self):
        from db import db
        from db.models import CustomerMeta, Snapshot

        self.login()
        pagos = [
            {**self.customer_row(nombre=f"Pago {i}", email=f"pago-{i}@example.test"), "fecha_alta_raw": f"2026-05-2{i}T00:00:00+00:00"}
            for i in range(1, 4)
        ]
        trials = [
            {**self.customer_row(nombre=f"Trial {i}", email=f"trial-{i}@example.test"), "estado": "trial", "fecha_alta_raw": f"2026-05-2{i}T00:00:00+00:00"}
            for i in range(1, 7)
        ]
        with self.app.app_context():
            db.session.add(Snapshot(payload={
                "test_marker": "solicitudes_directas",
                "clientes": pagos + trials,
                "eventos": {
                    "altas": [
                        {"email": f"pago-{i}@example.test", "fecha": f"2026-05-2{i}T00:00:00+00:00"}
                        for i in range(1, 4)
                    ] + [
                        {"email": f"trial-{i}@example.test", "fecha": f"2026-05-2{i}T00:00:00+00:00"}
                        for i in range(1, 4)
                    ],
                    "bajas": [],
                },
                "resumen": {},
            }))
            for i in range(1, 4):
                db.session.add(CustomerMeta(email=f"pago-{i}@example.test", origen="instagram"))
            for i in range(1, 7):
                db.session.add(CustomerMeta(email=f"trial-{i}@example.test", origen="email"))
            db.session.commit()

        response = self.client.get("/?desde=2026-05-20&hasta=2026-05-29")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        altas_block = body[body.index('<span class="kpi-label">Altas</span>'):]
        altas_block = altas_block[:altas_block.index("</a>")]
        self.assertIn('<span class="kpi-val">3</span>', altas_block)
        self.assertIn('"altas": [0, 1, 1, 1, 0, 0, 0, 0, 0, 0]', body)
        self.assertIn('"trials": [0, 1, 1, 1, 1, 1, 1, 0, 0, 0]', body)

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
        self.assertIn("Crear solicitud", body)
        self.assertIn('class="request-board panel v5-board-panel"', body)
        self.assertIn('class="request-create-inline v5-form-panel"', body)
        self.assertNotIn('class="request-create-panel panel v5-form-panel"', body)
        self.assertIn('class="btn-primary request-header-action"', body)
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

    def test_solicitudes_con_customer_preselecciona_cliente(self):
        self.login()
        self.add_snapshot([
            {"nombre": "Zeta", "email": "zeta@example.test", "email_key": "zeta@example.test"},
            {"nombre": "Ana", "email": "ana@example.test", "email_key": "ana@example.test"},
        ])

        response = self.client.get("/solicitudes?customer=ana@example.test")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        option = '<option value="ana@example.test" selected>Ana'
        self.assertIn(option, body)

    def test_bandeja_con_customer_preselecciona_cliente_en_nueva_tarea(self):
        self.login()
        self.add_snapshot([
            {"nombre": "Zeta", "email": "zeta@example.test", "email_key": "zeta@example.test"},
            {"nombre": "Ana", "email": "ana@example.test", "email_key": "ana@example.test"},
        ])

        response = self.client.get("/bandeja?customer=ana@example.test")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        option = '<option value="ana@example.test" selected>Ana'
        self.assertIn(option, body)

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
        self.assertIn('class="request-list open-request-list"', body)
        self.assertIn('class="request-create-inline v5-form-panel"', body)
        self.assertNotIn('class="requests-table open-requests-table"', body)
        ticket_row = body[body.index(f"Ticket #{ticket_id}"):]
        ticket_row = ticket_row[:ticket_row.index("</article>")]
        self.assertIn("OPERACIONES", ticket_row)
        self.assertIn("Eliminar", ticket_row)
        self.assertEqual(ticket_row.count("Actualizar"), 1)
        self.assertIn('class="request-actions-menu"', ticket_row)
        self.assertIn("Gestionar", ticket_row)
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
        self.assertIn('class="request-list open-request-list"', body)
        self.assertIn(f"Ticket #{ticket_id}", body)
        self.assertIn("8 dias", body)
        self.assertIn("age-warn", body)
        self.assertIn("Alta", body)
        self.assertIn("0 comentarios", body)
        self.assertIn(f'/solicitudes/{ticket_id}', body)

        response = self.client.get(f"/solicitudes/{ticket_id}")
        body = response.get_data(as_text=True)
        self.assertIn("ticket-thread", body)
        self.assertIn('class="ticket-sidebar ticket-sidebar-compact"', body)
        self.assertIn('class="ticket-side-panel panel"', body)
        self.assertIn('class="ticket-comment-form"', body)
        self.assertIn('name="agente"', body)
        for agente in ("Luis", "Dalila", "Nicky", "Frank"):
            self.assertIn(f'value="{agente}"', body)

        response = self.client.post(
            f"/solicitudes/{ticket_id}/comentarios",
            data={"agente": "Dalila", "texto": "Ops confirma que lo toma hoy."},
        )
        self.assertEqual(response.status_code, 302)

        response = self.client.get("/solicitudes")
        body = response.get_data(as_text=True)
        self.assertIn("1 comentario", body)

        response = self.client.get(f"/solicitudes/{ticket_id}")
        body = response.get_data(as_text=True)
        self.assertIn(f"Ticket #{ticket_id}", body)
        self.assertIn("Ops confirma que lo toma hoy.", body)
        self.assertIn("Dalila", body)
        self.assertIn('class="comment-bubble"', body)
        self.assertIn("En gestion", body)
        self.assertIn("status-en_gestion", body)

        with self.app.app_context():
            comment = TicketComment.query.filter_by(interaccion_id=ticket_id).one()
            self.assertEqual(comment.agente, "Dalila")

    def test_ticket_detalle_separa_texto_y_enlaces_con_copiar(self):
        import datetime as dt

        from db import db
        from db.models import Interaccion

        self.login()
        self.add_snapshot([self.customer_row()])
        first_url = "https://lovingsiren.com/2026/04/02/leotiska-video-de-zorrita-desnuda-masturbandose-xxx/"
        second_url = "https://example.com/reporte?ticket=11"
        with self.app.app_context():
            ticket = Interaccion(
                customer_email="cliente-z@example.test",
                tipo="solicitud",
                texto=f"Revisar este enlace {first_url} y tambien este {second_url} para pedir baja.",
                categoria="envia_links",
                estado_gestion="abierta",
                created_at=dt.datetime.now(dt.timezone.utc),
            )
            db.session.add(ticket)
            db.session.commit()
            ticket_id = ticket.id

        response = self.client.get(f"/solicitudes/{ticket_id}")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Revisar este enlace", body)
        self.assertIn("y tambien este", body)
        self.assertIn("para pedir baja.", body)
        self.assertIn('class="ticket-link-list"', body)
        self.assertEqual(body.count('class="ticket-link-card"'), 2)
        self.assertIn(f'href="{first_url}" target="_blank" rel="noopener noreferrer"', body)
        self.assertIn(f'data-copy-url="{first_url}"', body)
        self.assertIn(f'href="{second_url}" target="_blank" rel="noopener noreferrer"', body)
        self.assertIn(f'data-copy-url="{second_url}"', body)
        initial_message = body[body.index("Detalle inicial"):]
        initial_message = initial_message[:initial_message.index("</article>")]
        self.assertEqual(initial_message.count(first_url), 3)
        self.assertEqual(initial_message.count(second_url), 3)

    def test_ticket_comentario_renderiza_enlaces_accionables(self):
        import datetime as dt

        from db import db
        from db.models import Interaccion, TicketComment

        self.login()
        self.add_snapshot([self.customer_row()])
        comment_url = "https://example.com/cliente/avance"
        with self.app.app_context():
            ticket = Interaccion(
                customer_email="cliente-z@example.test",
                tipo="solicitud",
                texto="Revisar comentario con link",
                estado_gestion="abierta",
                created_at=dt.datetime.now(dt.timezone.utc),
            )
            db.session.add(ticket)
            db.session.flush()
            db.session.add(TicketComment(
                interaccion_id=ticket.id,
                agente="Luis",
                texto=f"Enviar update usando {comment_url} hoy.",
                created_at=dt.datetime.now(dt.timezone.utc),
            ))
            db.session.commit()
            ticket_id = ticket.id

        response = self.client.get(f"/solicitudes/{ticket_id}")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        comment_message = body[body.index("Luis"):]
        comment_message = comment_message[:comment_message.index("</article>")]
        self.assertIn("Enviar update usando", comment_message)
        self.assertIn("hoy.", comment_message)
        self.assertIn('class="ticket-link-card"', comment_message)
        self.assertIn(f'href="{comment_url}" target="_blank" rel="noopener noreferrer"', comment_message)
        self.assertIn(f'data-copy-url="{comment_url}"', comment_message)

    def test_ticket_link_render_no_ejecuta_html(self):
        import datetime as dt

        from db import db
        from db.models import Interaccion

        self.login()
        self.add_snapshot([self.customer_row()])
        safe_url = "https://example.com/safe"
        with self.app.app_context():
            ticket = Interaccion(
                customer_email="cliente-z@example.test",
                tipo="solicitud",
                texto=f'<script>alert("x")</script> mirar {safe_url}',
                estado_gestion="abierta",
                created_at=dt.datetime.now(dt.timezone.utc),
            )
            db.session.add(ticket)
            db.session.commit()
            ticket_id = ticket.id

        response = self.client.get(f"/solicitudes/{ticket_id}")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("&lt;script&gt;alert(&#34;x&#34;)&lt;/script&gt; mirar", body)
        self.assertNotIn('<script>alert("x")</script>', body)
        self.assertIn(f'href="{safe_url}" target="_blank" rel="noopener noreferrer"', body)

    def test_ticket_comentario_requiere_autor_valido(self):
        import datetime as dt

        from db import db
        from db.models import Interaccion, TicketComment

        self.login()
        self.add_snapshot([self.customer_row()])
        with self.app.app_context():
            ticket = Interaccion(
                customer_email="cliente-z@example.test",
                tipo="solicitud",
                texto="Validar autor",
                estado_gestion="abierta",
                created_at=dt.datetime.now(dt.timezone.utc),
            )
            db.session.add(ticket)
            db.session.commit()
            ticket_id = ticket.id

        response = self.client.post(
            f"/solicitudes/{ticket_id}/comentarios",
            data={"agente": "Otro", "texto": "No deberia guardarse."},
        )
        self.assertEqual(response.status_code, 302)

        with self.app.app_context():
            self.assertEqual(TicketComment.query.filter_by(interaccion_id=ticket_id).count(), 0)

    def test_ticket_abierto_renderiza_form_para_crear_tarea(self):
        import datetime as dt

        from app import MADRID_TZ
        from db import db
        from db.models import Interaccion

        self.login()
        self.add_snapshot([self.customer_row()])
        with self.app.app_context():
            ticket = Interaccion(
                customer_email="cliente-z@example.test",
                tipo="solicitud",
                texto="Dar seguimiento desde ticket",
                estado_gestion="abierta",
                created_at=dt.datetime.now(dt.timezone.utc),
            )
            resolved = Interaccion(
                customer_email="cliente-z@example.test",
                tipo="solicitud",
                texto="Ticket cerrado",
                estado_gestion="resuelta",
                resuelta=True,
                resolved_at=dt.datetime.now(dt.timezone.utc),
                created_at=dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=1),
            )
            db.session.add(ticket)
            db.session.add(resolved)
            db.session.commit()
            ticket_id = ticket.id
            resolved_id = resolved.id

        response = self.client.get(f"/solicitudes/{ticket_id}")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        today = dt.datetime.now(MADRID_TZ).date().isoformat()
        self.assertIn("Crear tarea", body)
        self.assertIn(f'action="/solicitudes/{ticket_id}/tareas"', body)
        self.assertIn('name="texto"', body)
        self.assertIn(f'name="due_date" value="{today}"', body)
        self.assertIn('name="assignee"', body)
        for assignee in ("Luis", "Dalila", "Nicky", "Frank"):
            self.assertIn(f'value="{assignee}"', body)

        resolved_response = self.client.get(f"/solicitudes/{resolved_id}")
        resolved_body = resolved_response.get_data(as_text=True)
        self.assertNotIn(f'action="/solicitudes/{resolved_id}/tareas"', resolved_body)

    def test_crear_tarea_desde_ticket_abierto_persiste_trazabilidad(self):
        import datetime as dt

        from db import db
        from db.models import CustomerReminder, Interaccion

        self.login()
        self.add_snapshot([self.customer_row()])
        with self.app.app_context():
            ticket = Interaccion(
                customer_email="cliente-z@example.test",
                tipo="queja",
                texto="Cliente pide respuesta",
                estado_gestion="abierta",
                created_at=dt.datetime.now(dt.timezone.utc),
            )
            db.session.add(ticket)
            db.session.commit()
            ticket_id = ticket.id

        response = self.client.post(
            f"/solicitudes/{ticket_id}/tareas",
            data={"texto": "Responder con estado", "due_date": "2026-06-12", "assignee": "Frank"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(f"/solicitudes/{ticket_id}", response.location)
        with self.app.app_context():
            task = CustomerReminder.query.filter_by(customer_email="cliente-z@example.test", source="ticket").one()
            self.assertEqual(task.texto, f"Ticket #{ticket_id} · Responder con estado")
            self.assertEqual(task.due_date, "2026-06-12")
            self.assertEqual(task.assignee, "Frank")

    def test_ticket_resuelto_no_crea_tarea(self):
        import datetime as dt

        from db import db
        from db.models import CustomerReminder, Interaccion

        self.login()
        self.add_snapshot([self.customer_row()])
        with self.app.app_context():
            ticket = Interaccion(
                customer_email="cliente-z@example.test",
                tipo="solicitud",
                texto="Ya resuelto",
                estado_gestion="resuelta",
                resuelta=True,
                resolved_at=dt.datetime.now(dt.timezone.utc),
                created_at=dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=1),
            )
            db.session.add(ticket)
            db.session.commit()
            ticket_id = ticket.id

        response = self.client.post(
            f"/solicitudes/{ticket_id}/tareas",
            data={"texto": "No crear", "due_date": "2026-06-12", "assignee": "Luis"},
        )

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            self.assertEqual(CustomerReminder.query.filter_by(customer_email="cliente-z@example.test", source="ticket").count(), 0)

    def test_tarea_desde_ticket_rechaza_asignado_texto_o_fecha_invalidos(self):
        import datetime as dt

        from db import db
        from db.models import CustomerReminder, Interaccion

        self.login()
        self.add_snapshot([self.customer_row()])
        with self.app.app_context():
            ticket = Interaccion(
                customer_email="cliente-z@example.test",
                tipo="solicitud",
                texto="Validar formulario",
                estado_gestion="abierta",
                created_at=dt.datetime.now(dt.timezone.utc),
            )
            db.session.add(ticket)
            db.session.commit()
            ticket_id = ticket.id

        invalid_payloads = [
            {"texto": "Asignado invalido", "due_date": "2026-06-12", "assignee": "Persona Invalida"},
            {"texto": "", "due_date": "2026-06-12", "assignee": "Luis"},
            {"texto": "Sin fecha", "due_date": "", "assignee": "Luis"},
        ]
        for payload in invalid_payloads:
            response = self.client.post(f"/solicitudes/{ticket_id}/tareas", data=payload)
            self.assertEqual(response.status_code, 302)

        with self.app.app_context():
            self.assertEqual(CustomerReminder.query.filter_by(customer_email="cliente-z@example.test", source="ticket").count(), 0)

    def test_tarea_desde_ticket_inexistente_o_no_solicitud_devuelve_404(self):
        import datetime as dt

        from db import db
        from db.models import Interaccion

        self.login()
        self.add_snapshot([self.customer_row()])
        response = self.client.post(
            "/solicitudes/999999/tareas",
            data={"texto": "No existe", "due_date": "2026-06-12", "assignee": "Luis"},
        )
        self.assertEqual(response.status_code, 404)

        with self.app.app_context():
            note = Interaccion(
                customer_email="cliente-z@example.test",
                tipo="nota",
                texto="No es solicitud",
                created_at=dt.datetime.now(dt.timezone.utc),
            )
            db.session.add(note)
            db.session.commit()
            note_id = note.id

        response = self.client.post(
            f"/solicitudes/{note_id}/tareas",
            data={"texto": "No crear", "due_date": "2026-06-12", "assignee": "Luis"},
        )
        self.assertEqual(response.status_code, 404)

    def test_tarea_creada_desde_ticket_aparece_en_bandeja(self):
        import datetime as dt

        from db import db
        from db.models import Interaccion

        self.login()
        self.add_snapshot([self.customer_row()])
        with self.app.app_context():
            ticket = Interaccion(
                customer_email="cliente-z@example.test",
                tipo="solicitud",
                texto="Seguir en bandeja",
                estado_gestion="abierta",
                created_at=dt.datetime.now(dt.timezone.utc),
            )
            db.session.add(ticket)
            db.session.commit()
            ticket_id = ticket.id

        self.client.post(
            f"/solicitudes/{ticket_id}/tareas",
            data={"texto": "Enviar update", "due_date": "2026-06-12", "assignee": "Dalila"},
        )

        response = self.client.get("/bandeja?date=2026-06-12")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn(f"Ticket #{ticket_id} · Enviar update", body)
        self.assertIn("Cliente Z", body)
        self.assertIn("Dalila", body)

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
        self.assertIn('class="request-list resolved-request-list"', body)
        self.assertIn(f"Ticket #{ticket_id}", body)
        ticket_row = body[body.index(f"Ticket #{ticket_id}"):]
        ticket_row = ticket_row[:ticket_row.index("</article>")]
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
