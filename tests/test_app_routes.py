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
        self.assertIn('class="collabs-page page"', body)
        self.assertIn('class="page-head collabs-head"', body)
        self.assertIn('class="collabs-kpi-strip mini-kpis"', body)
        self.assertIn('class="collab-form-panel panel"', body)
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
        self.assertIn('class="churn-page page"', body)
        self.assertIn('class="page-head churn-head"', body)
        self.assertIn('class="churn-toolbar periodo-bar"', body)
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
        self.assertIn('class="messages-page page"', body)
        self.assertIn('class="page-head messages-head"', body)
        self.assertIn('class="message-toolbar panel"', body)
        self.assertIn('action="/mensajes/categorias"', body)
        self.assertIn('class="message-form-panel panel"', body)
        self.assertIn('action="/mensajes"', body)
        self.assertIn('class="message-list redesigned-message-list"', body)
        self.assertIn("Test UI Mensaje", body)
        self.assertIn("copy-message", body)

    def test_ficha_permita_guardar_contacto_whatsapp_y_usuario(self):
        self.login()
        self.add_snapshot([self.customer_row()])

        response = self.client.get("/cliente/cliente-z@example.test")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('name="whatsapp"', body)
        self.assertIn('name="usuario"', body)
        self.assertIn("customer-profile-grid", body)
        self.assertIn("profile-overview-grid", body)
        self.assertIn("profile-secondary-grid", body)
        self.assertIn("client-action-form", body)

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
        self.assertIn('action="/clientes"', body)
        self.assertIn('name="q"', body)
        self.assertIn('placeholder="Buscar cliente"', body)
        self.assertIn("Ana", body)
        self.assertNotIn("Mia", body)

        response = self.client.get("/clientes?q=5555")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Ana", body)
        self.assertNotIn("Mia", body)

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
        self.assertIn('class="clientes-mobile-list"', body)

        response = self.client.get("/clientes?sort=cliente&dir=asc")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertLess(body.index("Ana"), body.index("Beta"))

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
        self.assertIn('class="dashboard-page page"', body)
        self.assertIn('class="page-head dashboard-head"', body)
        self.assertIn('class="dashboard-kpi-strip"', body)
        self.assertIn('class="dashboard-main-grid"', body)
        self.assertIn('class="dashboard-action-panel panel"', body)
        self.assertIn("Requiere accion", body)
        self.assertIn('href="/bandeja"', body)
        self.assertIn('href="/clientes?estado=impago"', body)
        self.assertIn('href="/clientes?estado=trial"', body)
        self.assertIn('class="base-state-grid"', body)

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
        self.assertIn('class="inbox-page page"', body)
        self.assertIn('class="page-head inbox-head"', body)
        self.assertIn('class="inbox-buckets"', body)
        self.assertIn('class="inbox-panel panel tone-danger"', body)
        self.assertIn('class="inbox-row"', body)
        self.assertIn("Bandeja operativa", body)
        self.assertIn("Cliente Impago", body)
        self.assertIn("Cliente Trial", body)
        self.assertIn("Completar", body)

    def test_ficha_crea_recordatorio_con_fecha_y_texto(self):
        from db.models import CustomerReminder

        self.login()
        self.add_snapshot([self.customer_row()])

        response = self.client.get("/cliente/cliente-z@example.test")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Recordatorios", body)
        self.assertIn('name="due_date"', body)

        response = self.client.post(
            "/cliente/cliente-z@example.test/recordatorios",
            data={"due_date": "2026-06-15", "texto": "Escribirle para revisar avance"},
        )

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            reminder = CustomerReminder.query.filter_by(customer_email="cliente-z@example.test").one()
            self.assertEqual(reminder.due_date, "2026-06-15")
            self.assertEqual(reminder.texto, "Escribirle para revisar avance")
            self.assertIsNone(reminder.completed_at)

    def test_ficha_usa_layout_core_en_columnas(self):
        self.login()
        self.add_snapshot([self.customer_row()])

        response = self.client.get("/cliente/cliente-z@example.test")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('class="customer-page page"', body)
        self.assertIn('class="page-head customer-head"', body)
        self.assertIn('class="customer-health-strip"', body)
        self.assertIn('class="customer-command-grid"', body)
        self.assertIn('class="customer-main-column"', body)
        self.assertIn('class="customer-side-column"', body)
        self.assertIn('action="/cliente/cliente-z@example.test/suscripcion"', body)
        self.assertIn('action="/cliente/cliente-z@example.test/contacto"', body)
        self.assertIn('action="/cliente/cliente-z@example.test/interaccion"', body)
        self.assertIn('action="/cliente/cliente-z@example.test/recordatorios"', body)

    def test_bandeja_muestra_recordatorios_activos_y_permite_completarlos(self):
        from db import db
        from db.models import CustomerReminder

        self.login()
        self.add_snapshot([self.customer_row(nombre="Cliente Recordado")])
        with self.app.app_context():
            reminder = CustomerReminder(
                customer_email="cliente-z@example.test",
                due_date="2026-06-15",
                texto="Mandar seguimiento de WhatsApp",
            )
            db.session.add(reminder)
            db.session.commit()
            reminder_id = reminder.id

        response = self.client.get("/bandeja")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Recordatorios (1)", body)
        self.assertIn("Cliente Recordado", body)
        self.assertIn("Mandar seguimiento de WhatsApp", body)
        self.assertIn("15/06/2026", body)
        self.assertIn("Completar", body)

        response = self.client.post(f"/recordatorios/{reminder_id}/completar")

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            reminder = db.session.get(CustomerReminder, reminder_id)
            self.assertIsNotNone(reminder.completed_at)

        response = self.client.get("/bandeja")
        body = response.get_data(as_text=True)
        self.assertIn("Recordatorios (0)", body)
        self.assertNotIn("Mandar seguimiento de WhatsApp", body)

    def test_recordatorio_requiere_fecha_y_texto(self):
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
        self.assertIn('class="requests-table open-requests-table"', body)
        self.assertIn('class="request-form-panel panel"', body)
        self.assertIn('class="requests-mobile-list"', body)
        ticket_row = body[body.index(f"Ticket #{ticket_id}"):]
        ticket_row = ticket_row[:ticket_row.index("</tr>")]
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
        self.assertIn('class="requests-table open-requests-table"', body)
        self.assertIn(f"Ticket #{ticket_id}", body)
        self.assertIn("8 dias", body)
        self.assertIn("age-warn", body)
        self.assertIn("Alta", body)
        self.assertIn("0 comentarios", body)
        self.assertIn(f'/solicitudes/{ticket_id}', body)

        response = self.client.get(f"/solicitudes/{ticket_id}")
        body = response.get_data(as_text=True)
        self.assertIn("ticket-thread", body)
        self.assertIn('class="ticket-sidebar"', body)
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
        self.assertIn('class="requests-table resolved-requests-table"', body)
        self.assertIn(f"Ticket #{ticket_id}", body)
        ticket_row = body[body.index(f"Ticket #{ticket_id}"):]
        ticket_row = ticket_row[:ticket_row.index("</tr>")]
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
