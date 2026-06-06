# Estado Traqeer AM Dashboard Codex

Fecha: 2026-06-06.

Carpeta de trabajo aislada:

```text
C:\Users\Franco Salemme\OneDrive\Escritorio\traqeer-am-dashboard-codex
```

No tocar como fuente de verdad de Claude:

```text
C:\Users\Franco Salemme\OneDrive\Escritorio\traqeer-am-dashboard
```

## Iteracion 2026-06-06 - Ticket enlaces accionables

Implementado en rama `codex/ticket-link-boxes`:

- La ficha de ticket separa automaticamente texto y URLs en el detalle inicial y comentarios.
- Los enlaces detectados se muestran en cajas accionables con URL visible, hipervinculo `Abrir enlace` y boton `Copiar`.
- `Crear tarea` queda plegado por defecto en el lateral del ticket y el layout da mas ancho relativo a la conversacion.
- No se cambio schema, persistencia, rutas ni endpoints; el parseo se calcula al renderizar.

Archivos tocados:

- `app.py`
- `templates/ticket.html`
- `static/style.css`
- `tests/test_app_routes.py`
- `status.md`

Verificacion:

```powershell
python -m unittest discover -s tests -p test_app_routes.py -k "ticket_detalle_separa" -v
python -m unittest discover -s tests -p test_app_routes.py -k "ticket_detalle_separa" -k "ticket_comentario_renderiza" -k "ticket_link_render" -v
python -m unittest discover -s tests -p test_app_routes.py -v
python -m unittest discover -s tests -v
git diff --check
```

Resultado:

- Test RED focal fallo inicialmente porque no existia `ticket-link-list`.
- Focales OK.
- `test_app_routes.py`: 74 tests OK.
- Suite completa: 115 tests OK.
- `git diff --check` con codigo 0; solo avisos esperados de normalizacion CRLF en Windows.
- Smoke local con Flask test client y ticket temporal:
  - `/solicitudes/<ticket_id>` autenticado -> 200.
  - Contiene `ticket-link-list`, `ticket-copy-button`, `href` seguro del enlace y `Crear tarea` cerrado por defecto.

Riesgos / fuera de alcance:

- Browser visual QA no ejecutada: el plugin Browser esta instalado, pero no expuso `node_repl/js` utilizable en esta sesion.

PR/deploy:

- PR #96 mergeado a `main` con commit `6b54f1e`.
- Deploy manual ejecutado con `railway up --detach -m "Deploy ticket actionable links"`.
- Deployment Railway `d7820e62-c482-441a-9fa6-6ee2c2864497` -> SUCCESS.
- Produccion publica verificada:
  - `https://customers-production-8190.up.railway.app/healthz` -> 200 `{"status":"ok"}`.
  - `/login` -> 200, contiene `Customers Dashboard`.
- QA autenticada de produccion no ejecutada: no se uso ni pidio clave en esta iteracion.

## Iteracion 2026-06-05 - Solicitudes acciones compactas

Implementado en rama `codex/solicitudes-actions-compact`:

- `Crear solicitud` deja de vivir en una barra/panel separado y queda integrado dentro del panel `Abiertas`.
- Cada ticket abierto reduce ruido visual: las acciones de estado, importancia, resolver y eliminar quedan plegadas bajo `Gestionar`.
- El listado conserva los tags operativos visibles, pero deja los controles accionables fuera de la primera lectura.

Archivos tocados:

- `templates/quejas.html`
- `static/style.css`
- `tests/test_app_routes.py`
- `status.md`

Verificacion:

```powershell
python -m unittest discover -s tests -p test_app_routes.py -k "solicitudes_muestra_formulario" -k "solicitudes_abiertas" -v
python -m unittest discover -s tests -p test_app_routes.py -v
python -m unittest discover -s tests -v
git diff --check
```

Resultado:

- Tests RED focales fallaron inicialmente contra el panel separado y acciones siempre visibles.
- Focales OK.
- `test_app_routes.py`: 71 tests OK.
- Suite completa: 112 tests OK.
- `git diff --check` con codigo 0; solo avisos esperados de normalizacion CRLF en Windows.
- Smoke local con Flask test client:
  - `/solicitudes` autenticado -> 200.
  - Contiene `request-create-inline`, no contiene `request-create-panel`, y contiene `request-actions-menu` o estado vacio.

Riesgos / fuera de alcance:

- No se cambiaron rutas, modelos, endpoints ni reglas de negocio.

PR/deploy:

- PR #94 mergeado a `main` con commit `17d455a`.
- Deploy manual ejecutado con `railway up --detach -m "Deploy solicitudes compact actions"`.
- Deployment Railway `3a44ea4f-86d8-480d-8e06-ec4726b10c87` -> SUCCESS.
- Produccion publica verificada:
  - `https://customers-production-8190.up.railway.app/healthz` -> 200 `{"status":"ok"}`.
  - `/login` -> 200, contiene `Customers Dashboard`.
  - `/solicitudes` sin sesion -> 302 a login.
- QA autenticada de produccion no ejecutada: no se uso ni pidio clave en esta iteracion.

## Iteracion 2026-06-05 - Solicitudes UI minimalista

Implementado en rama `codex/solicitudes-minimal-ui`:

- `/solicitudes` mueve la carga manual a un panel desplegable `Crear solicitud`, alineado con el patron de `Nueva tarea` en Bandeja.
- El listado de solicitudes abiertas y resueltas deja la tabla ancha y pasa a filas compactas con cliente, resumen, tags operativos y acciones inline.
- `/solicitudes/<id>` mantiene conversacion, gestion y creacion de tareas, pero compacta la columna lateral en una sola superficie con secciones internas.
- KPIs y grafico de solicitudes bajan peso visual para priorizar la mesa operativa.

Archivos tocados:

- `templates/quejas.html`
- `templates/ticket.html`
- `static/style.css`
- `tests/test_app_routes.py`
- `status.md`

Verificacion:

```powershell
python -m unittest discover -s tests -p test_app_routes.py -k "solicitudes_muestra_formulario" -k "solicitudes_abiertas" -k "ticket_muestra_numero" -v
python -m unittest discover -s tests -p test_app_routes.py -v
python -m unittest discover -s tests -v
git diff --check
```

Resultado:

- Tests RED focales fallaron inicialmente contra el layout anterior.
- Focales OK.
- `test_app_routes.py`: 71 tests OK.
- Suite completa: 112 tests OK.
- `git diff --check` con codigo 0; solo avisos esperados de normalizacion CRLF en Windows.
- Smoke local con Flask test client:
  - `/solicitudes` autenticado -> 200.
  - Contiene `request-create-panel` y lista/estado vacio de solicitudes.

Riesgos / fuera de alcance:

- No se cambiaron rutas, modelos, endpoints ni reglas de negocio.
- QA visual con navegador integrado no ejecutada: la herramienta Browser no expuso `node_repl/js` utilizable en esta sesion; se verifico por HTML/CSS, tests y smoke local.

PR/deploy:

- PR #92 mergeado a `main` con commit `a2cb1cc`.
- Deploy manual ejecutado con `railway up --detach -m "Deploy solicitudes minimal UI"`.
- Deployment Railway `4aa1598c-9891-41c9-adb9-41e829ff842b` -> SUCCESS.
- Produccion publica verificada:
  - `https://customers-production-8190.up.railway.app/healthz` -> 200 `{"status":"ok"}`.
  - `/login` -> 200, contiene `Customers Dashboard`.
  - `/solicitudes` sin sesion -> 302 a login.
- QA autenticada de produccion no ejecutada: no se uso ni pidio clave en esta iteracion.

## Iteracion 2026-06-05 - Churn incluye canceladas con periodo futuro

Implementado en rama `codex/churn-canceled-period-end`:

- Causa raiz: `build_snapshot()` solo agregaba a `clientes` las suscripciones Stripe `active`, `trialing`, `past_due` y `unpaid`.
- Las suscripciones `status="canceled"` se usaban solo para eventos de `bajas`; si Stripe ya las habia marcado como `canceled` pero conservaban `current_period_end` futuro, no entraban al snapshot de clientes y por eso `/bandeja` no podia mostrarlas en `Riesgo de churn`.
- Fix: al recorrer `status="canceled"`, si `_scheduled_cancellation_info()` detecta fecha futura y hubo pago real, el cliente se mantiene como `activo` con `cancelacion_programada=True` y no se registra todavia como baja efectiva.

Archivos tocados:

- `sync/snapshot.py`
- `tests/test_jobs.py`
- `status.md`

Verificacion:

```powershell
python -m unittest discover -s tests -p test_jobs.py -k "future_period_end" -v
python -m unittest discover -s tests -p test_jobs.py -v
python -m unittest discover -s tests -p test_customer_rules.py -k "churn" -v
python -m unittest discover -s tests -p test_app_routes.py -k "bandeja_muestra_cancelaciones" -v
python -m unittest discover -s tests -v
git diff --check
```

Resultado:

- Test RED nuevo fallo inicialmente porque el cliente cancelado con periodo futuro no aparecia en `payload["clientes"]`.
- Tests focales OK.
- Suite completa: 112 tests OK.
- `git diff --check` con codigo 0; solo avisos esperados de normalizacion CRLF en Windows.

Riesgos / fuera de alcance:

- Para que produccion muestre esos clientes, hace falta regenerar snapshot con el boton autenticado `Actualizar datos` o esperar el cron.
- No se verificaron nombres reales localmente: el clon local no tiene snapshot real cargado (`clientes=0`).
- Refresh remoto manual no ejecutado: `railway run python -m sync.refresh_job` corre local con variables Railway y falla porque `postgres.railway.internal` no resuelve fuera de Railway; `railway ssh --service customers --environment production -- python --version` y `railway ssh --service customers --environment production python -m sync.refresh_job` quedaron colgados hasta timeout.

PR/deploy:

- PR #90 mergeado a `main` con commit `8eef0b6`.
- Deploy manual ejecutado con `railway up --detach -m "Deploy churn future-period cancellations"`.
- Deployment Railway `2d5ead92-890d-4240-bc36-60e1b117fe8b` -> Online.
- Produccion publica verificada:
  - `https://customers-production-8190.up.railway.app/healthz` -> 200 `{"status":"ok"}`.
  - `/login` -> 200, contiene `Customers Dashboard`.
  - `/bandeja` sin sesion -> 302 a `/login?next=/bandeja`.
  - `/bandeja?customer=test@example.com` sin sesion -> 302 a `/login?next=/bandeja`.

## Iteracion 2026-06-05 - Bandeja acciones y colores por bucket

Implementado en rama `codex/bandeja-actions-colors`:

- `/bandeja` deja el panel superior solo para filtros `Fecha`, `Asignado`, `Estado` y `Filtrar`.
- `Nueva tarea` se mueve al header del bucket `Tareas`; al abrir el bucket aparece el formulario de creacion dentro de `Tareas`.
- `/bandeja?customer=<email>` abre por defecto el bucket `Tareas` y preselecciona el cliente en `Nueva tarea`.
- Colores por bucket:
  - `Tareas`: `tone-tasks` / `tag-tasks`.
  - `Riesgo de churn`: `tone-churn` / `tag-churn`.
  - `Impagos`: `tone-danger` / `tag-danger`.
  - `Onboarding pendiente`: `tone-onboarding` / `tag-onboarding`.
  - `En trial`: `tone-warning` / `tag-warning`.
- `Filtrar` queda alineado junto a los filtros con ancho natural en desktop y ancho completo en mobile.

Archivos tocados:

- `templates/bandeja.html`
- `static/style.css`
- `tests/test_app_routes.py`
- `status.md`

Verificacion:

```powershell
python -m unittest discover -s tests -p test_app_routes.py -k "bandeja_usa_layout_operativo" -k "bandeja_premium" -k "bandeja_con_customer_abre" -v
python -m unittest discover -s tests -v
git diff --check
```

Resultado:

- Tests RED focales fallaron inicialmente contra el layout anterior.
- Tests focales OK.
- Suite completa: 111 tests OK.
- `git diff --check` con codigo 0; solo avisos esperados de normalizacion CRLF en Windows.
- Smoke local con Flask test client:
  - `/bandeja` -> 200, contiene `tone-tasks`, `tone-onboarding`, `tag-tasks`, `tag-danger` y `tag-warning`.
  - `/bandeja?customer=smoke-bandeja@example.test` -> 200, abre `Tareas` y preselecciona el cliente.

Riesgos / fuera de alcance:

- No se cambiaron rutas, modelos ni endpoints.
- Browser visual QA no ejecutada: el plugin Browser esta instalado, pero no expuso `node_repl/js` en esta sesion; se verifico por HTML/CSS, tests y smoke local.
- QA autenticada de produccion no ejecutada: no se uso ni pidio clave en esta iteracion.

PR/deploy:

- PR #88 mergeado a `main` con commit `aa0ff7d`.
- Deploy manual ejecutado con `railway up --detach -m "Deploy bandeja actions colors"`.
- Deployment Railway `0bf61e04-3838-42cc-8416-8764ccd74449` -> Online.
- Produccion publica verificada:
  - `https://customers-production-8190.up.railway.app/healthz` -> 200 `{"status":"ok"}`.
  - `/login` -> 200, contiene `Customers Dashboard`.
  - `/bandeja` sin sesion -> 302 a `/login?next=/bandeja`.
  - `/bandeja?customer=test@example.com` sin sesion -> 302 a `/login?next=/bandeja`.

## Iteracion 2026-06-05 - Bandeja colapsable y churn violeta

Implementado en rama `codex/bandeja-collapsible-polish`:

- `/bandeja` compacta la operacion en buckets colapsables por defecto:
  - `Tareas`, `Riesgo de churn`, `Impagos`, `Onboarding pendiente` y `En trial`.
  - `Onboarding pendiente` vuelve como bucket propio con accion masiva, manteniendo tambien las tareas automaticas de bienvenida.
- El header suma chip `churn` en violeta junto a impagos, trials y tareas.
- `Riesgo de churn` usa `tone-churn` y tags `tag-churn` para no confundirse con amarillo de trials/onboarding.
- `Nueva tarea` queda dentro de un panel operativo junto a filtros.
- `/bandeja?customer=<email>` abre `Nueva tarea` por defecto y conserva cliente preseleccionado.
- El boton `Filtrar` vuelve a ancho natural en desktop; en mobile conserva ancho completo.

Archivos tocados:

- `templates/bandeja.html`
- `static/style.css`
- `tests/test_app_routes.py`
- `status.md`

Verificacion:

```powershell
python -m unittest discover -s tests -p "test_app_routes.py" -k "bandeja_usa_layout_operativo" -k "bandeja_premium" -k "bandeja_con_customer_abre" -v
python -m unittest discover -s tests -v
git diff --check
```

Resultado:

- Tests RED focales fallaron inicialmente contra la Bandeja anterior.
- Tests focales OK.
- Suite completa: 111 tests OK.
- `git diff --check` con codigo 0; solo avisos esperados de normalizacion CRLF en Windows.
- Smoke local con Flask test client:
  - `/bandeja?customer=smoke-bandeja2@example.test` -> 200.
  - Contiene chip `1 churn`, `tag-churn` y `Nueva tarea` abierta con cliente preseleccionado.

Riesgos / fuera de alcance:

- No se cambiaron modelos, endpoints ni reglas de negocio.
- La accion masiva de onboarding queda dentro del bucket colapsable; las tareas automaticas de bienvenida siguen apareciendo en `Tareas`.
- QA visual con navegador integrado no ejecutada: la herramienta de navegador no quedo expuesta; se verifico por HTML/CSS y tests.

PR/deploy:

- PR #86 mergeado a `main` con commit `64b7f4b`.
- Deploy manual ejecutado con `railway up --detach -m "Deploy bandeja collapsible polish"`.
- Deployment Railway `87fed923-bcbd-42a1-a2e8-d75a33050f7f` -> SUCCESS.
- Produccion publica verificada:
  - `https://customers-production-8190.up.railway.app/healthz` -> 200 `{"status":"ok"}`.
  - `/login` -> 200, contiene `Customers Dashboard`.
  - `/bandeja` sin sesion -> 302 a login.
  - `/bandeja?customer=test@example.com` sin sesion -> 302 a login.
- QA autenticada de produccion no ejecutada: no se uso ni pidio clave en esta iteracion.

## Iteracion 2026-06-05 - Ficha cliente botones y UI polish

Implementado en rama `codex/ficha-ui-polish-buttons`:

- La botonera superior de `/cliente/<email>` ahora renderiza `Crear solicitud` y `Crear tarea` como botones primarios reales, no links sueltos.
- `Volver a clientes` conserva estilo secundario y queda alineado con las acciones principales.
- Se ajusto el header de ficha con clase `customer-head-copy`, gap consistente, alto minimo de acciones, espaciado de tags y responsive mobile para que los botones ocupen ancho completo.
- Se agrego cobertura preventiva en `test_ficha_usa_layout_core_en_columnas` para asegurar clases de acciones y estilos `.btn-primary`.

Archivos tocados:

- `templates/ficha.html`
- `static/style.css`
- `tests/test_app_routes.py`
- `status.md`

Verificacion:

```powershell
python -m unittest discover -s tests -p "test_app_routes.py" -k "ficha_usa_layout_core" -k "ficha_operativa" -v
python -m unittest discover -s tests -v
git diff --check
```

Resultado:

- Tests focales OK.
- Suite completa: 110 tests OK.
- `git diff --check` con codigo 0; solo avisos esperados de normalizacion CRLF en Windows.
- Smoke local con Flask test client:
  - `/cliente/smoke-buttons@example.test` -> 200.
  - Contiene `customer-head-copy`, `customer-head-actions`, links primarios a `/solicitudes?customer=...` y `/bandeja?customer=...`, secundario a `/clientes` y leyenda `Antes: Francisco Pardo`.

Riesgos / fuera de alcance:

- No se cambio backend, datos ni rutas.
- QA visual con navegador integrado no ejecutada: la herramienta de navegador no quedo expuesta en esta sesion; se verifico por HTML/CSS y tests.

PR/deploy:

- PR #84 mergeado a `main` con commit `e325876`.
- Deploy manual ejecutado con `railway up --detach -m "Deploy ficha UI polish buttons"`.
- Deployment Railway `e292ac40-3d42-444c-939d-1b4157f8a779` -> SUCCESS.
- Produccion publica verificada:
  - `https://customers-production-8190.up.railway.app/healthz` -> 200 `{"status":"ok"}`.
  - `/login` -> 200, contiene `Customers Dashboard`.
  - `/cliente/test@example.com` sin sesion -> 302 a login.
  - `/solicitudes?customer=test@example.com` sin sesion -> 302 a login.
  - `/bandeja?customer=test@example.com` sin sesion -> 302 a login.

## Iteracion 2026-06-05 - Ficha cliente polish minimal

Implementado en rama `codex/ficha-cliente-polish`:

- `/cliente/<email>` queda mas limpia y orientada a lectura operativa:
  - Header con acciones principales `Crear solicitud`, `Crear tarea` y `Volver a clientes`; se quita el boton visible `Marcar inactivo`.
  - El estado operativo se integra al header como tags compactos: impago, solicitudes abiertas, churn, trial, bienvenida pendiente, tareas activas o `Sin pendientes`.
  - Se elimina el panel lateral duplicado `Acciones`.
  - Se elimina el panel lateral separado `Tareas activas`; las tareas activas viven en el resumen operativo y en el historial.
- `Contacto e identificacion` cambia el foco:
  - Se oculta el selector `Estado WhatsApp` de la UI porque no representaba el caso real de nombre agendado.
  - Se usa `CustomerMeta.manual_nombre` como `Nombre operativo` editable desde la ficha.
  - Si el nombre operativo reemplaza al nombre del snapshot, el header muestra `Antes: <nombre snapshot>`.
  - El backend conserva `whatsapp_status` si llega desde clientes existentes o rutas legacy; ya no se resetea al guardar contacto desde la ficha.
- `Links reportados por el cliente` y `Actividad reciente` se unifican en `Historial operativo`:
  - Muestra resumen de links reportados sin URLs.
  - Muestra tareas activas compactas con accion `Completar`.
  - Mantiene notas, solicitudes, quejas, churn y upsell de `Interaccion`.

Archivos tocados:

- `app.py`
- `templates/ficha.html`
- `static/style.css`
- `tests/test_app_routes.py`
- `status.md`

Verificacion:

```powershell
python -m unittest discover -s tests -p "test_app_routes.py" -k "ficha_permita_guardar_contacto" -k "ficha_operativa" -k "ficha_permita_marcar_cliente" -k "ficha_usa_layout_core" -v
python -m unittest discover -s tests -p "test_app_routes.py" -v
python -m unittest discover -s tests -v
git diff --check
```

Resultado:

- Tests RED focales fallaron inicialmente contra la UI anterior.
- Tests focales OK.
- `test_app_routes.py`: 70 tests OK.
- Suite completa: 110 tests OK.
- `git diff --check` con codigo 0; solo avisos esperados de normalizacion CRLF en Windows.
- Smoke local con Flask test client:
  - `/cliente/smoke-polish@example.test` -> 200.
  - Contiene `Patri Castillo`, `Antes: Francisco Pardo`, acciones principales, `Historial operativo`, tarea y ticket de prueba.
  - No contiene `Marcar inactivo`, panel `Acciones`, `Estado WhatsApp`, `Links reportados por el cliente` ni `Tareas activas`.

Riesgos / fuera de alcance:

- El endpoint legacy `POST /cliente/<email>/inactivar` sigue existiendo y testeado; solo se retiro el boton visible de la ficha.
- `whatsapp_status` sigue en modelo/backend por compatibilidad, pero no se edita desde esta UI.
- QA visual con navegador integrado no ejecutada en esta iteracion; la verificacion visual fue smoke HTML por Flask test client.

PR/deploy:

- PR #82 mergeado a `main` con commit `a5cf61c`.
- Deploy manual ejecutado con `railway up --detach -m "Deploy ficha cliente polish minimal"`.
- Deployment Railway `ce4d54fa-ef9a-4083-acb0-81b5b7615cb4` -> SUCCESS.
- Produccion publica verificada:
  - `https://customers-production-8190.up.railway.app/healthz` -> 200 `{"status":"ok"}`.
  - `/login` -> 200, contiene `Customers Dashboard`.
  - `/cliente/test@example.com` sin sesion -> 302 a login.
  - `/solicitudes?customer=test@example.com` sin sesion -> 302 a login.
  - `/bandeja?customer=test@example.com` sin sesion -> 302 a login.
- QA autenticada de produccion no ejecutada: no se uso ni pidio clave en esta iteracion.

## Iteracion 2026-06-05 - Ficha cliente operativa

Implementado en rama `codex/ficha-cliente-operativa`:

- `/cliente/<email>` se reorganiza como ficha de lectura operativa:
  - Header con acciones `Crear solicitud` y `Crear tarea`.
  - Bloque unificado `Suscripcion y salud` con plan, estado, tipo, alta/trial, activo recurrente, pirateria, suplantaciones y health checks.
  - Bloque `Contacto e identificacion` con WhatsApp, usuario, manager y estado de WhatsApp.
  - Bloque `Links reportados por el cliente` como resumen sin exponer URLs.
  - `Historial` renombrado a `Actividad reciente`.
  - Tareas activas quedan como lectura compacta; se quitaron formularios inline de nueva solicitud/tarea.
- `CustomerMeta` agrega `manager` y `whatsapp_status` con migracion local compatible con Postgres.
- `sync.health.salud_de_cuentas()` agrega `impersonations_gestionadas` y resumen `manual_reports`.
- `/solicitudes?customer=<email>` preselecciona cliente en `Nueva solicitud`.
- `/bandeja?customer=<email>` preselecciona cliente en `Nueva tarea`.

Archivos tocados:

- `app.py`
- `db/models.py`
- `sync/health.py`
- `templates/ficha.html`
- `templates/quejas.html`
- `templates/bandeja.html`
- `tests/test_app_routes.py`
- `tests/test_health.py`
- `status.md`

Verificacion:

```powershell
python -m unittest discover -s tests -p "test_app_routes.py" -k "customer_meta_acepta" -k "ficha_permita_guardar_contacto" -k "ficha_operativa" -k "solicitudes_con_customer" -k "bandeja_con_customer" -v
python -m unittest discover -s tests -p "test_health.py" -v
python -m unittest discover -s tests -p "test_app_routes.py" -v
python -m unittest discover -s tests -v
git diff --check
```

Resultado:

- Tests RED focales fallaron inicialmente por campos/modelo, preseleccion y salud faltantes.
- Tests focales OK.
- `test_app_routes.py`: 70 tests OK.
- Suite completa: 110 tests OK.
- `git diff --check` con codigo 0; solo avisos esperados de normalizacion CRLF en Windows.
- Smoke local con Flask test client:
  - `/cliente/smoke-ficha@example.test` -> 200, contiene bloques nuevos y links con `customer`.
  - `/solicitudes?customer=smoke-ficha@example.test` -> 200, cliente preseleccionado.
  - `/bandeja?customer=smoke-ficha@example.test` -> 200, cliente preseleccionado.

Riesgos / fuera de alcance:

- No se elimino el backend legacy `POST /cliente/<email>/interaccion` ni `POST /cliente/<email>/recordatorios`; solo se quitaron los formularios inline de la ficha.
- El resumen de links manuales depende de metadata en Mongo (`reportedByRole`, `reportedAt`/`reported_at`, `repeated`/`duplicate`) y no expone URLs.
- No se ejecuto QA visual con navegador real en esta iteracion; la verificacion fue HTML/smoke por test client.

Deploy Railway posterior:

- PR #80 mergeado a `main` con commit `d162648`.
- Deploy manual ejecutado con `railway up --detach -m "Deploy ficha cliente operativa"`.
- Deployment Railway `28f1e58c-9acf-433a-9902-ceea218cbe72` -> SUCCESS.
- Produccion publica verificada:
  - `https://customers-production-8190.up.railway.app/healthz` -> 200 `{"status":"ok"}`.
  - `/login` -> 200, contiene `Customers Dashboard`.
  - `/clientes` sin sesion -> 302 a `/login?next=/clientes`.
  - `/cliente/test@example.com` sin sesion -> 302 a login.
  - `/solicitudes?customer=test@example.com` sin sesion -> 302 a login.
  - `/bandeja?customer=test@example.com` sin sesion -> 302 a login.
- QA autenticada de produccion no ejecutada: no se uso ni pidio clave en esta iteracion.

## Hecho

- Riesgo de churn:
  - El snapshot guarda cancelaciones programadas de Stripe en clientes activos con `cancelacion_programada`, `cancelacion_fecha_raw`, `cancelacion_fecha` y `cancelacion_dias`.
  - Los clientes con cancelacion programada siguen contando como activos recurrentes hasta la fecha efectiva.
  - Bandeja tiene seccion `Riesgo de churn`, combinando cancelaciones programadas y marcas manuales tipo `churn` creadas desde la ficha.
  - La ficha muestra una tarjeta de atencion cuando existe cancelacion programada o riesgo de churn manual.
- Refresh automatico:
  - Se agrego `python -m sync.refresh_job` para ejecutar `refrescar_snapshot()` con app context y cerrar conexiones al terminar.
  - `RAILWAY.md` documenta crear un segundo servicio Railway con cron `0 4 * * *` UTC para 06:00 Madrid durante CEST.
- Diagnostico de activos recurrentes:
  - Se agrego `python -m scripts.active_recurrent_diff` para comparar los dos ultimos snapshots reales, ignorando snapshots de tests.
  - Diff local de los ultimos snapshots reales: activos recurrentes `77 -> 76`; salio `Estefania sol giuliano <estefaniasolgiuliano@gmail.com>` por pasar de `activo` a `impago`.
- Impagos con factura rechazada:
  - `refrescar_snapshot()` ahora construye el snapshot completo y despues cruza `collect_unpaid_from_stripe()`/`merge_unpaid_details()`.
  - Esto cubre clientes cuya suscripcion sigue `active` pero cuya ultima factura Stripe quedo `open`/rechazada con saldo pendiente.
  - El resumen persistido se recalcula despues del merge para que `activos` baje e `impago` suba en el mismo snapshot.
- Clientes ahora tiene buscador por nombre/email.
- Origen incluye `XBIZ`, `Instagram`, `WhatsApp`, `Sky` y `Reactivacion` como canales seleccionables y filtrables.
- Clientes tiene filtros por activos recurrentes, activos, trial, impagos, inactivos, one time y free colab.
- La ficha permite ajustar manualmente plan, estado y tipo de cliente.
- `One time payment` y `Free por colab` no suman como activos recurrentes.
- Dashboard separa activos recurrentes, one time y free colab.
- Se agregaron pruebas unitarias para reglas de negocio.
- Bandeja muestra impagos con dias de atraso, monto pendiente y link de ultima factura cuando el snapshot lo trae.
- La lista de Clientes/Impagos tambien muestra la columna Atencion con dias de impago y factura.
- El snapshot nuevo guarda `ultima_factura_fecha_raw`, `ultima_factura_url`, `impago_monto_pendiente`, `impago_dias` y estado de factura para impagos Stripe.
- Se agrego refresh parcial solo Stripe para enriquecer impagos sin necesitar Mongo.
- Impagos ahora soporta multiples facturas pendientes por cliente:
  - El snapshot guarda `facturas_pendientes` con fecha, link, monto pendiente y estado por factura.
  - Clientes, Bandeja y Ficha muestran cantidad de facturas, monto total pendiente, factura mas vieja y links de factura.
  - `estado=impago` agrupa todos los estados operativos de deuda.
- Aging operativo de impagos agregado sin contaminar churn:
  - 0-29 dias: `impago`.
  - 30-89 dias: `pausado_impago`.
  - 90+ dias: `inactivo_impago`.
  - Estos estados no cuentan como activos recurrentes y no se agregan a Bajas/Churn salvo cancelacion real en Stripe.
  - Si el plan detectado contiene `free`, la UI muestra `acceso free por impago` como senal operativa separada del billing.
- Bandeja ahora ordena impagos por mas dias de atraso y quejas abiertas por mas antiguedad.
- Ficha de cliente redisenada con cabecera de perfil, badges, bloque de atencion, ajuste manual, origen/bienvenida, salud y contacto/historial.
- Quejas tiene dashboard propio con abiertas, resueltas, dias maximos abiertas y total registrado.
- Las quejas se pueden categorizar como `Encuentra links`, `Envia links`, `Tiempos de gestion` u otras categorias creadas desde la plataforma.
- Las categorias de quejas son editables desde `/quejas`: agregar, renombrar y ocultar.
- Desde la ficha de cliente, al registrar una queja se puede elegir la categoria.
- Modelo de colabs agregado:
  - `Free por colab` queda independiente y no suma como activo recurrente.
  - `Colab con descuento` se puede seleccionar como tipo de cliente y si esta activo sigue sumando como activo recurrente.
  - La ficha permite registrar descuento, acuerdo, fecha de inicio y proxima revision.
  - Clientes y Dashboard tienen filtro/KPI de `Colab descuento`.
  - Bandeja muestra `Colabs a revisar` cuando la fecha de revision esta vencida.
- Wiki editable de mensajes agregada en `/mensajes`:
  - Categorias iniciales: Bienvenida, Pagos, Soporte y Quejas.
  - Permite crear categorias nuevas.
  - Permite crear mensajes con titulo, categoria, tags y cuerpo.
  - Permite buscar por titulo, texto o tag y filtrar por categoria.
  - Permite editar, archivar y copiar el texto del mensaje.
  - Se agrego pack inicial de plantillas basado en `C:\Users\Franco Salemme\traqeer-wa-analysis\output\PLAYBOOK.md`.
  - Plantillas incluidas: baja de enlace, link activo, queja/demora, consulta general, soporte tecnico, alta/suscripcion, venta y cierre/checkpoint.
- Trials por vencer:
  - Se calcula fecha de fin usando `trial_fin_raw` si existe; si no, `fecha_alta_raw + 7 dias`.
  - Clientes, Ficha y Bandeja muestran la fecha exacta de fin de trial y dias restantes/vencidos.
  - Bandeja ordena trials por vencimiento mas proximo.
- Reactivaciones:
  - Si un cliente tuvo baja historica pero hoy esta activo, la ficha/lista lo marcan como reactivado.
  - Las bajas de clientes reactivados se excluyen de KPIs, serie temporal y vista de bajas.
- Preparacion Railway:
  - `/healthz` publico agregado.
  - `RAILWAY.md` agregado con comando, healthcheck y variables.
  - `.env.*` agregado al `.gitignore`.
  - Se elimino `.env.stripe.tmp` temporal.
- Pulido visual aplicado:
  - Topbar mas compacta y consistente.
  - Layout principal ampliado.
  - Paneles, cards, badges y tags con estilos mas uniformes.
  - Tabla de Clientes envuelta en scroll responsive.
  - Formularios, Bandeja, Ficha, Quejas y Mensajes con mejor espaciado y lectura.
  - Mobile mejorado para filtros, listas, tablas y ficha.
- Solicitudes de clientes:
  - Quejas y solicitudes viven en una hoja operativa aparte (`/solicitudes`, tambien compatible con `/quejas`).
  - La navegacion tiene acceso directo a `Solicitudes`.
  - Desde la ficha del cliente se puede cargar `Queja` o `Solicitud`.
  - Cada solicitud puede asignarse a Customer Success u Operaciones.
  - Cada solicitud tiene estado de gestion: abierta, en proceso, esperando cliente o resuelta.
  - La ficha del cliente da mas preponderancia a solicitudes abiertas y enlaza a la hoja de gestion.
- Tema visual claro Traqeer:
  - Fondo blanco/gris claro, acento celeste y bordes suaves estilo Google/minimal.
  - Header usa logo SVG en `static/traqeer-logo.svg` basado en la referencia compartida.
  - Si aparece el archivo original del logo, se puede reemplazar ese SVG sin tocar templates.
  - Logo web agregado en `static/traqeer-logo.png` y usado en header/login.
  - Entrada renombrada a `Customers Dashboard`.
- Colabs ahora tiene pantalla propia `/colabs`:
  - Bandeja ya no muestra Solicitudes ni Colabs.
  - Colabs muestra total, free colab, colab con descuento y revisiones pendientes.
  - Tambien funciona como pipeline editable de creadores/prospectos para colabs.
  - Permite cargar nombre, contacto, red, estado, tipo, idea, detalles, duracion, fechas, proxima accion y responsable.
  - Permite editar y archivar creadores.
- Bajas ahora tiene pantalla propia `/bajas`:
  - Muestra cancelaciones reales por periodo, excluyendo clientes reactivados.
  - Permite cargar motivo de baja y detalle interno por cliente/fecha.
  - Motivos iniciales: precio, no uso, no vio resultado, soporte, competencia, pausa temporal y otro.
- Dashboard ahora incluye preset `Todo` y la linea temporal toma el primer evento real de altas/bajas como inicio.
- El KPI de Bajas del dashboard abre la pantalla de bajas con motivos.
- Inicio muestra la northstar `Activos recurrentes` como primer KPI superior, comparada contra el periodo anterior seleccionado y con link a Clientes filtrado por recurrentes.
- Los estados de impago (`impago`, `pausado_impago`, `inactivo_impago`) cuentan dentro de `Activos recurrentes` si el cliente es de tipo recurrente. Siguen excluidos `One time payment` y `Free por colab`.
- Inicio ya no muestra KPI de Solicitudes; esa lectura vive en `/solicitudes`.
- El grafico principal de Inicio es de barras y combina Altas, Bajas y Trials por dia/semana segun el periodo.
- Inicio agrupa `Instagram`, `Instagram ingles`, `Instagram español` e `Instagram portugues` como un solo canal `Instagram` para filtro y grafico de base actual por canal.
- Inicio muestra el grafico lateral `Base actual por canal`, calculado sobre clientes activos recurrentes + trials actuales por canal de adquisicion.
- El grafico lateral de canales muestra cantidad y porcentaje por canal en la leyenda y tooltip.
- El grafico lateral de canales respeta el periodo seleccionado: para rangos filtrados cuenta eventos de altas + trials del periodo; en `Todo` muestra toda la base actual.
- Solicitudes ahora tiene dashboard por periodo:
  - Presets de tiempo, incluyendo `Todo`.
  - KPIs de registradas, abiertas actuales, Customer Success, Operaciones y resueltas.
  - Grafico temporal de solicitudes por dia o semana.
- Solicitudes permite alta directa desde `/solicitudes`:
  - Formulario superior `Nueva solicitud` con buscador de cliente por nombre/email/WhatsApp, tipo, motivo/categoria, importancia y detalle obligatorio.
  - Nueva ruta POST `/solicitudes/nueva`.
  - Todas las solicitudes nuevas se crean como `abierta`; luego se gestionan desde la lista/ficha.
  - El equipo no se selecciona al crear: se deriva del estado (`abierta`/`en_gestion` => Ops; `comunicar` => CS).
  - Si no hay clientes en snapshot, el formulario queda deshabilitado con mensaje operativo.
- Se removio el scope financiero/CEO del dashboard de Customer Success:
  - No hay bloque MRR/cash/conciliacion en Inicio.
  - No hay pantalla `/gastos` ni APIs financieras.
  - Queda un test preventivo para evitar reintroducir `Gastos`, `MRR`, `Stripe` o `Mercury` en Inicio.
- Ficha de cliente:
  - `Ajuste manual` queda reorganizado en grilla compacta.
  - Se agrego campo WhatsApp editable por cliente en `CustomerMeta.whatsapp`.
  - Se agrego campo `usuario` editable por cliente en `CustomerMeta.usuario`, usado junto a WhatsApp para busqueda rapida.
  - La ficha usa una grilla de perfil mas armonica: resumen/atencion arriba, suscripcion/ajuste manual como bloque principal, contacto/origen/salud como bloque secundario.
  - Los campos avanzados de colab dentro de `Ajuste manual` quedan plegados salvo que ya existan datos de colab.
  - `Nuevo contacto o solicitud` usa formulario en dos lineas para evitar campos comprimidos.
  - En `Origen y bienvenida`, Instagram se elige como canal base y abre un selector de idioma (`Sin idioma`, `Ingles`, `Español`, `Portugues`) guardando la variante en `CustomerMeta.origen`.
- Clientes:
  - La busqueda usa nombre, email, usuario y WhatsApp; la leyenda del input queda como `Buscar cliente`.
  - La tabla permite ordenar por Cliente, Tipo, Plan, Estado, Atencion, Origen y Alta con links en los encabezados.
  - El orden vive en URL (`sort`/`dir`) y preserva filtros/busqueda.
- Solicitudes/tickets:
  - Cada solicitud se muestra como `Ticket #ID`.
  - La creacion ya no pide responsable.
  - Se agrega importancia (`Baja`, `Media`, `Alta`).
  - Estados operativos simplificados: `abierta`, `en_gestion`, `comunicar`; `resuelta` queda como accion separada.
  - El equipo se deriva del estado: abierta/comunicar => CS, en_gestion => Ops.
  - Se agrega ficha de ticket `/solicitudes/<id>` con comentarios internos.
  - Se muestra aging en dias; amarillo si supera 7 dias, rojo si supera 14.
  - Los tickets resueltos muestran los dias que estuvieron abiertos y ya no muestran equipo CS/Ops.
  - Los tickets resueltos pueden reabrirse; vuelven a `abierta` con equipo CS.
  - Las filas de Solicitudes muestran contador de comentarios por ticket.
  - Los comentarios internos permiten elegir autor entre Luis, Dalila, Nicky y Frank, y validan que el autor sea uno de esos valores.
  - Los estados tienen chips de color para diferenciar abierta, en gestion, comunicar y resuelta.
  - Las abiertas pueden eliminarse desde la lista.
  - En abiertas solo se actualizan estado e importancia; la categoria queda fija luego de crear el ticket.
  - La administracion visual de categorias se oculto de `/solicitudes`; las categorias se manejan internamente.
- Recordatorios por cliente:
  - La ficha permite crear recordatorios con fecha limite y texto libre.
  - Bandeja muestra todos los recordatorios activos al final, ordenados por fecha, con boton `Completar`.
  - Los recordatorios completados salen de Bandeja y quedan visibles como completados recientes en la ficha.
- Handoff de diseno:
  - Se agrego `design-handoff.md` con contexto de producto, rutas, restricciones, prompt para Claude/tool de diseno y criterios para traer el diseno de vuelta a Codex.
  - Se generaron screenshots locales en `design-screenshots/` para adjuntar manualmente al pedido de diseno. No se versionan porque pueden contener nombres/emails reales de clientes.
- Redisenio UI/UX V1:
  - Se adopto el shell base con sidebar desktop, topbar con busqueda global hacia `/clientes` y navegacion responsive simple en mobile.
  - `/clientes` queda como pantalla piloto del nuevo sistema visual: filtros compactos, tabla densa con headers sticky y cards mobile.
  - El prototipo React de diseno se uso como referencia, sin incorporarlo al runtime Flask ni agregar dependencias frontend.
- Redisenio UI/UX V2:
  - `/solicitudes` adopta una vista operativa tipo tabla/lista, manteniendo abiertas y resueltas separadas.
  - La carga de `Nueva solicitud` queda como panel compacto visible, sin cambiar rutas ni schema.
  - Las solicitudes abiertas y resueltas tienen tablas desktop y cards mobile; las acciones rapidas siguen disponibles en la lista.
  - La ficha `/solicitudes/<id>` se reorganiza como conversacion interna + sidebar de propiedades/gestion.
  - No se incorporo runtime React/Tailwind ni dependencias frontend del prototipo; se porto como Jinja/CSS.
- Redisenio UI/UX V3 core:
  - `/` adopta el sistema visual nuevo: page head, KPIs densos, grafico principal, panel `Requiere accion`, grafico de canales y grilla de estado actual.
  - `/bandeja` adopta buckets operativos densos para churn, impagos, onboarding, trials y recordatorios, preservando acciones POST existentes.
  - `/cliente/<email>` adopta ficha en columnas: cabecera, strip de atencion, columna principal de suscripcion/contacto/salud/historial y columna lateral de ajustes/contactos/recordatorios.
  - Se mantiene Flask/Jinja/CSS sin React/Tailwind ni cambios de schema/rutas.
- Redisenio UI/UX V4 admin:
  - `/colabs` adopta cabecera operativa, KPIs, panel de alta de creador, pipeline de creadores y tabla de clientes colab con scroll controlado.
  - `/bajas` adopta cabecera, filtros de periodo/canal, KPIs y tabla de motivos con formulario inline preservando POST `/bajas/motivo`.
  - `/mensajes` adopta toolbar de busqueda/categoria, panel compacto de alta y lista de mensajes redisenada con copiar/editar/archivar.
  - Se mantiene Flask/Jinja/CSS sin React/Tailwind ni cambios de schema/rutas.
- Redisenio UI/UX V5 polish profundo:
  - Todas las pantallas principales adoptan marcador `polish-v5` y una capa visual balanceada para headers, toolbars, KPIs, paneles, tablas y cards mobile.
  - Pantallas incluidas: `/`, `/clientes`, `/cliente/<email>`, `/bandeja`, `/solicitudes`, `/solicitudes/<id>`, `/colabs`, `/bajas` y `/mensajes`.
  - Clientes, Solicitudes y Ticket incorporan wrappers dedicados para ordenar mejor la lectura operativa sin cambiar rutas, forms ni schema.
  - Se mantiene Flask/Jinja/CSS sin React/Tailwind ni dependencias frontend nuevas.

## Verificacion

Ultima verificacion luego de aplicar Polish V5 profundo:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_app_routes.AppRoutesTest.test_polish_v5_renderiza_todas_las_pantallas_principales -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -c "from app import app; print('imports ok', len(list(app.url_map.iter_rules())))"
git diff --check
```

Resultado: test focal V5 OK; 76 tests OK; import Flask OK con 40 rutas; `git diff --check` sin errores reales, solo avisos CRLF de Windows. Verificacion visual local con Playwright en 1440px y 390px para `/`, `/clientes`, `/cliente/<email>`, `/bandeja`, `/solicitudes`, `/solicitudes/<id>`, `/colabs`, `/bajas?preset=todo` y `/mensajes`: todas con `polish-v5` y sin overflow horizontal; capturas guardadas en `design-screenshots/polish-v5/`.
PR #60 mergeado a `main`.
Deploy Railway posterior: `b267b2da-e00d-4889-8198-327a5c2b657f` SUCCESS; produccion verificada con `/healthz` 200, `/login` 200 y `/`, `/clientes`, `/bandeja`, `/solicitudes`, `/colabs`, `/bajas`, `/mensajes` redirigiendo a login.

Ultima verificacion luego de redisenar Colabs, Bajas y Mensajes:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_app_routes.AppRoutesTest.test_colabs_usa_layout_admin_redisenado tests.test_app_routes.AppRoutesTest.test_bajas_usa_layout_admin_redisenado tests.test_app_routes.AppRoutesTest.test_mensajes_usa_layout_admin_redisenado -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -c "from app import app; print('imports ok', len(list(app.url_map.iter_rules())))"
git diff --check
```

Resultado: tests focales OK; 75 tests OK; import Flask OK con 40 rutas; `git diff --check` sin errores reales, solo avisos CRLF de Windows. Verificacion visual local con Playwright en 1440px y 390px para `/colabs`, `/bajas?preset=todo` y `/mensajes`: sin overflow horizontal; capturas guardadas en `design-screenshots/admin-ui-redesign/`.
PR #58 mergeado a `main`.
Deploy Railway posterior: `47b9d041-5dc8-42c4-810b-96d4603f95c8` SUCCESS; produccion verificada con `/healthz` 200, `/login` 200 y `/colabs`, `/bajas`, `/mensajes` redirigiendo a login.

Ultima verificacion luego de redisenar Inicio, Bandeja y Ficha de cliente:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_app_routes.AppRoutesTest.test_dashboard_usa_layout_core_redisenado tests.test_app_routes.AppRoutesTest.test_bandeja_usa_layout_operativo_redisenado tests.test_app_routes.AppRoutesTest.test_ficha_usa_layout_core_en_columnas -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -c "from app import app; print('imports ok', len(list(app.url_map.iter_rules())))"
git diff --check
```

Resultado: tests focales OK; 72 tests OK; import Flask OK con 40 rutas; `git diff --check` sin errores reales, solo avisos CRLF de Windows. Verificacion visual local con Playwright en 1440px y 390px para `/`, `/bandeja` y `/cliente/<email>`: sin overflow horizontal; las tres pantallas renderizan con las clases core nuevas.
PR #56 mergeado a `main`.
Deploy Railway posterior: `58f9767e-698a-4f2e-979e-e1a71ccd2253` SUCCESS; produccion verificada con `/healthz` 200, `/login` 200, `/` redirigiendo a login y `/bandeja` redirigiendo a login.

Ultima verificacion luego de redisenar Solicitudes y ficha de Ticket:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_app_routes.AppRoutesTest.test_solicitudes_abiertas_actualizan_estado_importancia_y_se_pueden_eliminar tests.test_app_routes.AppRoutesTest.test_ticket_muestra_numero_aging_y_comentarios tests.test_app_routes.AppRoutesTest.test_ticket_resuelto_muestra_dias_abierto_y_permite_reabrir -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -c "from app import app; print('imports ok', len(list(app.url_map.iter_rules())))"
git diff --check
```

Resultado: tests focales OK; 69 tests OK; import Flask OK con 40 rutas; `git diff --check` sin errores reales, solo avisos CRLF de Windows. Verificacion visual local con Playwright en 1440px y 390px para `/solicitudes` y `/solicitudes/2`: sin overflow horizontal; tabla/lista desktop OK, cards mobile de abiertas/resueltas OK y ficha de ticket OK.
Deploy Railway posterior: `4d8a48dc-4681-43cc-b687-42435da1571e` SUCCESS; produccion verificada con `/healthz` 200, `/login` 200 y `/solicitudes` redirigiendo a login.

Ultima verificacion luego de aplicar redisenio V1 shell + Clientes:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_app_routes.AppRoutesTest.test_clientes_busca_por_usuario_y_whatsapp_con_placeholder_simple tests.test_app_routes.AppRoutesTest.test_clientes_ordena_por_columnas_y_preserva_filtros -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -c "from app import app; print('imports ok', len(list(app.url_map.iter_rules())))"
git diff --check
```

Resultado: tests focales OK; 69 tests OK; import Flask OK con 40 rutas; `git diff --check` sin errores reales, solo avisos CRLF de Windows. Verificacion visual local con Playwright en 1440px y 390px para `/`, `/clientes`, `/cliente/<email>` y `/solicitudes`: sin overflow horizontal; Clientes desktop/mobile y Solicitudes desktop revisadas visualmente.
Deploy Railway posterior: `088748e4-a7a9-4699-b1ac-7932dac5edd3` SUCCESS; produccion verificada con `/healthz` 200, `/login` 200 y `/clientes` redirigiendo a login.

Ultima verificacion luego de preparar handoff de diseno:

```powershell
.\.venv\Scripts\python.exe -c "from app import app; print('imports ok', len(list(app.url_map.iter_rules())))"
```

Resultado: import Flask OK con 40 rutas. Capturas locales generadas con Playwright contra `http://127.0.0.1:5001`: 9 desktop y 3 mobile en `design-screenshots/`; revision visual manual OK en Clientes desktop y Solicitudes mobile.

Ultima verificacion luego de agregar contador y autores de comentarios en tickets:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_app_routes.AppRoutesTest.test_ticket_muestra_numero_aging_y_comentarios tests.test_app_routes.AppRoutesTest.test_ticket_comentario_requiere_autor_valido -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -c "from app import app; print('imports ok', len(list(app.url_map.iter_rules())))"
git diff --check
```

Resultado: tests focales OK; 69 tests OK; import Flask OK con 40 rutas; `git diff --check` sin errores reales, solo avisos CRLF de Windows. Verificacion renderizada local autenticada de `/solicitudes` y `/solicitudes/<id>`: contador pasa de `0 comentarios` a `1 comentario`, selector muestra Luis/Dalila/Nicky/Frank y el comentario guardado se renderiza con autor.
Deploy Railway posterior: `e763a911-149e-41b2-9e49-4e499a872f7c` SUCCESS; produccion verificada con `/healthz` 200, `/login` 200 y `/solicitudes` redirigiendo a login.

Ultima verificacion luego de ordenar la tabla de clientes y ampliar busqueda:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_app_routes.AppRoutesTest.test_clientes_busca_por_usuario_y_whatsapp_con_placeholder_simple tests.test_app_routes.AppRoutesTest.test_clientes_ordena_por_columnas_y_preserva_filtros -v
.\.venv\Scripts\python.exe -c "from app import app; print('imports ok', len(list(app.url_map.iter_rules())))"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Resultado: tests focales OK; import Flask OK con 40 rutas; 68 tests OK. Verificacion HTTP local autenticada de `/clientes`: busqueda por usuario/telefono 200 y orden `sort=alta&dir=desc` 200.
Deploy Railway posterior: `cf7df728-eeee-4148-9466-e2ce2549ab35` SUCCESS; produccion verificada con `/healthz` 200 y `/login` 200.

Ultima verificacion luego de agregar recordatorios por cliente:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_app_routes.AppRoutesTest.test_ficha_crea_recordatorio_con_fecha_y_texto tests.test_app_routes.AppRoutesTest.test_bandeja_muestra_recordatorios_activos_y_permite_completarlos tests.test_app_routes.AppRoutesTest.test_recordatorio_requiere_fecha_y_texto -v
.\.venv\Scripts\python.exe -c "from app import app; print('imports ok', len(list(app.url_map.iter_rules())))"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Resultado: tests focales OK; import Flask OK con 40 rutas; 66 tests OK. Verificacion HTTP local autenticada de `/cliente/<email>` y `/bandeja`: 200 con Recordatorios, texto y boton Completar renderizados.
Deploy Railway posterior: `7edbd231-5f7d-4bb5-bdac-bd7685422853` SUCCESS; produccion verificada con `/healthz` 200 y `/login` 200.

Ultima verificacion luego de incluir impagos recurrentes en activos recurrentes:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_customer_rules.CustomerRulesTest.test_unpaid_recurrent_customer_counts_as_recurrent_active -v
.\.venv\Scripts\python.exe -c "from app import app; print('imports ok', len(list(app.url_map.iter_rules())))"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Resultado: test focal OK; import Flask OK con 38 rutas; 63 tests OK.
Deploy Railway posterior: `6594ae09-27da-402a-ac36-4f4ca59edea9` SUCCESS; produccion verificada con `/healthz` 200 y `/login` 200.

Ultima verificacion luego de conectar facturas rechazadas al refresh completo:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -c "from app import app; print('imports ok', len(list(app.url_map.iter_rules())))"
```

Resultado: 62 tests OK; import Flask OK con 38 rutas.

Ultima verificacion luego de agregar canales de adquisicion para bulk:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -c "from app import app; print('imports ok', len(list(app.url_map.iter_rules())))"
```

Resultado: 46 tests OK; import Flask OK con 38 rutas.

Bulk de canales de adquisicion aplicado en produccion desde `C:\Users\Franco Salemme\Downloads\Hoja de cálculo sin título (2).xlsx`:

- Excel: 102 emails unicos con canal normalizado.
- Snapshot actual: 46 clientes encontrados y actualizados.
- Fuera del snapshot actual: 56 emails sin tocar.
- Canales desconocidos: 0.
- Duplicados/conflictos: 7; se aplico la ultima aparicion del Excel.
- Verificacion posterior: 46 matched, 0 mismatches.
- Conteo final aplicado: `instagram=20`, `referido=16`, `whatsapp=3`, `telegram=2`, `email=2`, `directo=2`, `sky=1`.
- Deploy Railway previo al bulk: `cfb784fe-9338-4ca7-94b7-9fa7a8654711` SUCCESS; `/healthz` 200 y `/login` 200.

Ultima verificacion luego de pulir layout de ficha de cliente:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -c "from app import app; print('imports ok', len(list(app.url_map.iter_rules())))"
```

Resultado: 46 tests OK; import Flask OK con 38 rutas.

Verificacion visual local:

- Servidor local: `http://127.0.0.1:5010`.
- Ficha desktop 1240px: sin overflow horizontal.
- Ficha mobile 390px: sin overflow horizontal.
- Se corrigio `_ensure_local_schema` para agregar `interacciones.resuelta` en SQLite local antiguo.
- Deploy Railway posterior: `0babac60-f3fe-4549-a9f2-beff071bb35b` SUCCESS; `/healthz` 200 y `/login` 200.

Ultima verificacion luego de agrupar variantes de Instagram:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -c "from app import app; print('imports ok', len(list(app.url_map.iter_rules())))"
```

Resultado: 49 tests OK; import Flask OK con 38 rutas.
- Deploy Railway posterior: `31e92431-3357-4745-844a-6602fa0c6ee2` SUCCESS; `/healthz` 200 y `/login` 200.

Ultima verificacion luego de sumar trials al grafico por canal:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -c "from app import app; print('imports ok', len(list(app.url_map.iter_rules())))"
```

Resultado: 50 tests OK; import Flask OK con 38 rutas.
- Deploy Railway posterior: `0993a175-ee0d-46c0-a14b-d223d6754858` SUCCESS; `/healthz` 200 y `/login` 200.

Ultima verificacion luego de agregar porcentajes al grafico por canal:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -c "from app import app; print('imports ok', len(list(app.url_map.iter_rules())))"
```

Resultado: 50 tests OK; import Flask OK con 38 rutas.
- Deploy Railway posterior: `bf568317-14aa-4e06-b67a-970be1d8abce` SUCCESS; `/healthz` 200 y `/login` 200.

Correccion posterior:

- La leyenda del grafico por canal usa el indice de `canalData.labels` como fuente del label para evitar `undefined` en Chart.js.
- Verificacion: 50 tests OK; import Flask OK con 38 rutas.
- El grafico por canal ahora usa la base actual de activos recurrentes + trials actuales, no eventos historicos de altas/trials, para que `Sin asignar` no incluya clientes viejos fuera del snapshot vigente.
- Verificacion: 50 tests OK; import Flask OK con 38 rutas.
- Deploy Railway posterior: `ab1dfc74-c31f-40af-ab3d-b620a49dbdb9` SUCCESS; `/healthz` 200 y `/login` 200.
- Correccion posterior: el grafico por canal respeta filtros de fecha y la leyenda se genera con una entrada por segmento del grafico.
- Verificacion: 51 tests OK; import Flask OK con 38 rutas.
- Deploy Railway posterior: `512965df-974b-4e5f-b706-5dd88a0750ac` SUCCESS; `/healthz` 200 y `/login` 200.
- Correccion posterior: en periodos filtrados el grafico por canal usa altas + trials del periodo para que el total coincida con los KPIs/serie; `Todo` conserva la lectura de base actual.
- Verificacion: 51 tests OK; import Flask OK con 38 rutas.
- Deploy Railway posterior: `4b80021c-1b43-49d0-b4c6-386fa90fdbc3` SUCCESS; `/healthz` 200 y `/login` 200.
- Correccion posterior: en periodos filtrados el grafico por canal descarta eventos de emails fuera de la base actual recurrente/trial para no reintroducir `Sin asignar` historico.
- Verificacion: 52 tests OK; import Flask OK con 38 rutas.
- Deploy Railway posterior: `3f56b3fe-cea0-49ac-9e19-8dac27ec4c35` SUCCESS; `/healthz` 200 y `/login` 200.
- Correccion posterior: en preset `Todo`, el KPI Altas completa eventos faltantes con clientes recurrentes actuales que no tienen alta historica registrada, para evitar que Altas quede por debajo de Activos recurrentes.
- Verificacion: 53 tests OK; import Flask OK con 38 rutas.
- Deploy Railway posterior: `838040de-2ed2-49df-9784-ad25770889f4` SUCCESS; `/healthz` 200 y `/login` 200.
- Correccion posterior: en preset `Todo`, Altas tambien completa bajas historicas sin alta registrada, para que `Altas - Bajas` cierre contra la base activa recurrente cuando el historial de altas esta incompleto.
- Verificacion: 53 tests OK; import Flask OK con 38 rutas.
- Deploy Railway posterior: `1b6c0e0a-c10d-4649-839b-3ce7cb0addd0` SUCCESS; `/healthz` 200 y `/login` 200.
- Correccion posterior: las altas excluyen emails que hoy estan en trial, para que en periodos como 7 dias `Altas` no duplique trials; los trials quedan solo en su serie propia.
- Verificacion: 54 tests OK; import Flask OK con 38 rutas.
- Deploy Railway posterior: `69013efe-1c0c-45a2-b18d-5c93b65db112` SUCCESS; `/healthz` 200 y `/login` 200.
- Correccion posterior: en periodos filtrados, la torta por canal cuenta todos los eventos de altas + trials con canal definido, aunque el email no este en la base actual; solo descarta `Sin asignar`.
- Verificacion: 55 tests OK; import Flask OK con 38 rutas.
- Deploy Railway posterior: `a04a9ab2-ea07-45a9-aed7-31c7ff76f347` SUCCESS; `/healthz` 200 y `/login` 200.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Resultado: 24 tests OK.

Ultima verificacion luego de Bajas/Todo/Solicitudes:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Resultado: 26 tests OK.

Ultima verificacion luego de pack WhatsApp y pipeline Colabs:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Resultado: 28 tests OK.

Ultima verificacion luego de agregar origen `XBIZ`:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Resultado: 29 tests OK.

Ultima verificacion luego de mover northstar a Inicio:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Resultado: 30 tests OK.

Ultima verificacion luego de multiples facturas y aging de impagos:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Resultado: 33 tests OK.

Ultima verificacion luego de ajustar Inicio con northstar por periodo y barras de trials:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Resultado: 34 tests OK.

Verificacion focal luego de alta directa de solicitudes:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_app_routes -v
```

Resultado: 9 tests OK.

Verificacion completa luego de alta directa de solicitudes:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Resultado historico intermedio: 47 tests OK antes de remover el scope financiero.

Verificacion focal luego de remover finanzas del dashboard CS:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_app_routes.AppRoutesTest.test_dashboard_no_muestra_finanzas_ni_gastos -v
```

Resultado: 1 test OK.

Verificacion completa final:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Resultado: 40 tests OK.

Verificacion luego de ficha WhatsApp y tickets:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Resultado: 43 tests OK.

Verificacion luego de pulir tickets resueltos/reapertura:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -c "from app import app; print('imports ok', len(list(app.url_map.iter_rules())))"
```

Resultado: 44 tests OK; `imports ok 37`.

Verificacion HTTP local autenticada luego de pulir tickets:

- `/solicitudes` 200 con formulario visible, sin `name="agente"` y con chips de estado.
- PR #6 mergeado a `main`.
- Railway deploy `4ea78907-f526-4952-8e1e-7d5bc44916b1` exitoso.
- Produccion verificada: `/healthz` 200, `/login` 200, `/solicitudes` sin login redirige a login.

Verificacion luego de simplificar acciones de abiertas y buscador de cliente:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -c "from app import app; print('imports ok', len(list(app.url_map.iter_rules())))"
```

Resultado: 45 tests OK; `imports ok 38`.

Verificacion HTTP local autenticada:

- `/solicitudes` 200.
- Formulario con buscador por cliente/email/WhatsApp.
- Alta sin campo `pelota`.
- Ticket abierto con boton `Eliminar`, sin edicion de categoria en la fila.
- Estado `abierta` mostrado como Operaciones derivado del estado.
- PR #8 mergeado a `main`.
- Railway deploy `5ab5fe76-ffd2-45b3-9db4-886dc5820e81` exitoso.
- Produccion verificada: `/healthz` 200, `/login` 200, `/solicitudes` sin login redirige a login.

Verificacion luego de alta siempre abierta:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -c "from app import app; print('imports ok', len(list(app.url_map.iter_rules())))"
```

Resultado: 45 tests OK; `imports ok 38`.

Verificacion HTTP local autenticada:

- `/solicitudes` 200.
- Formulario de alta con buscador e importancia.
- Formulario de alta sin `estado_gestion`; el backend ignora cualquier estado enviado y crea `abierta`.
- PR #10 mergeado a `main`.
- Railway deploy `27dd475e-d994-4981-8bef-e425ba3c7c7f` exitoso.
- Produccion verificada: `/healthz` 200, `/login` 200, `/solicitudes` sin login redirige a login.

Verificacion luego de usuario de cliente y categorias internas:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -c "from app import app; print('imports ok', len(list(app.url_map.iter_rules())))"
```

Resultado: 45 tests OK; `imports ok 38`.

Verificacion HTTP local autenticada:

- `/solicitudes` 200 sin bloque visual de `Categorias` ni endpoint `/quejas/categorias` renderizado.
- `/cliente/<email>` 200 con campo `usuario` y grilla `customer-profile-grid`.
- PR #12 mergeado a `main`.
- Railway deploy `3538b7b3-830d-4fe4-9d6a-b3d4a2e10191` exitoso.
- Produccion verificada: `/healthz` 200, `/login` 200, `/solicitudes` sin login redirige a login.

Verificacion HTTP local luego de ficha WhatsApp y tickets:

- `/solicitudes` 200 con tickets numerados, selector de importancia y sin campo responsable en alta.
- `/solicitudes/<id>` 200 con ficha de ticket, estado, importancia y comentarios.
- PR #5 mergeado a `main`.
- Railway deploy `7d1c9d69-c28d-4368-981a-f8d0b18cdc71` exitoso.
- Produccion verificada: `/healthz` 200, `/login` 200, `/solicitudes` sin login redirige a login.

Verificacion de import:

```powershell
.\.venv\Scripts\python.exe -c "from app import app; print('imports ok', len(list(app.url_map.iter_rules())))"
```

Resultado: `imports ok 28`.

Ultima verificacion de import:

```powershell
.\.venv\Scripts\python.exe -c "from app import app; print('imports ok', len(list(app.url_map.iter_rules())))"
```

Resultado: `imports ok 30`.

Ultima verificacion de import:

```powershell
.\.venv\Scripts\python.exe -c "from app import app; print('imports ok', len(list(app.url_map.iter_rules())))"
```

Resultado: `imports ok 36`.

Ultima verificacion de import:

```powershell
.\.venv\Scripts\python.exe -c "from app import app; print('imports ok', len(list(app.url_map.iter_rules())))"
```

Resultado: `imports ok 37`.

Verificacion HTTP local:

- `/` 200
- `/clientes` 200
- `/clientes?recurrente=1` 200
- `/clientes?tipo=one_time` 200
- `/clientes?estado=inactivo` 200
- `/bandeja` 200
- `/clientes?estado=impago` 200
- `/cliente/<email>` 200 con nueva ficha visual
- `/quejas` 200 con dashboard de quejas y categorias editables
- `/solicitudes` 200 con hoja operativa CS/Ops
- `/colabs` 200 con gestion separada de colabs
- `/colabs` 200 con pipeline de creadores y formulario de alta
- `/bajas?preset=todo` 200 con motivos de baja editables
- `/solicitudes?preset=todo` 200 con dashboard y grafico temporal
- `/solicitudes` 200 autenticado con formulario `Nueva solicitud` y accion `/solicitudes/nueva`.
- `/` 200 autenticado sin bloque financiero/CEO.
- Produccion Railway redeployada luego de remover finanzas: `/healthz` 200, `/gastos` 404.
- `/?preset=todo` 200 con preset Todo
- `/mensajes` 200 con wiki editable de mensajes
- `/mensajes?q=checkpoint` 200 con plantillas del pack WhatsApp
- `/static/traqeer-logo.svg` 200
- `/healthz` 200 publico
- `/` 200 autenticado con grafico de barras Altas/Bajas/Trials, sin KPI de Solicitudes y sin texto `vs 7d ant.`
- `/clientes?estado=impago` 200 con facturas multiples y chips de aging
- `/clientes?estado=pausado_impago` 200
- `/clientes?estado=inactivo_impago` 200
- `/bandeja` 200 con detalle de facturas pendientes
- `/clientes?estado=trial` 200 con informacion de trial
- `/clientes` 200 con tabla responsive
- Flujo verificado: crear queja desde ficha, verla en `/quejas`, agregar categoria, renombrar categoria, categorizar queja, ocultar categoria y resolver queja.
- Flujo de colab verificado: marcar cliente como `Colab con descuento`, guardar descuento/acuerdo/inicio/revision, verlo en ficha, filtrarlo en Clientes, verlo en Dashboard y verlo en Bandeja como revision pendiente. Luego se restauro el cliente usado para prueba.
- Flujo de creador colab verificado: crear creador temporal, archivarlo y limpiar el dato temporal.
- Flujo de wiki verificado: crear categoria, crear mensaje, buscar por tag/texto, editar mensaje y archivar. Luego se limpiaron los datos temporales.
- Pack WhatsApp verificado en wiki: busqueda por `checkpoint` devuelve plantillas de queja y cierre.
- Flujo de solicitudes verificado: crear solicitud desde ficha, verla en hoja, cambiar equipo/estado, resolverla y limpiar dato temporal.
- Bandeja verificada sin bloques de Solicitudes ni Colabs.
- Flujo de baja verificado: guardar motivo por POST en `/bajas/motivo`, confirmar persistencia y restaurar el dato temporal.

Refresh parcial Stripe ejecutado:

- Impagos detectados en Stripe: 7
- Cruzados con clientes actuales: 7
- Con link de factura: 6

Servidor activo en la ultima verificacion local:

```text
http://127.0.0.1:5001
```

Clave usada en la verificacion local: `test123`.

GitHub:

- Repo remoto: `https://github.com/francods9-tech/customers`
- Rama publicada: `main`
- Commit inicial: `b50e6fb Initial Traqeer customers dashboard`

Railway:

- CLI instalado.
- Proyecto indicado por Franco: `prett freedom`.
- Proyecto linkeado: `pretty-freedom`.
- Servicio web: `customers`.
- Postgres agregado.
- Variables cargadas en servicio web: `APP_PASSWORD`, `SECRET_KEY`, `DATABASE_URL`.
- Clave de login Railway actualizada a la indicada por Franco el 2026-05-27.
- Variables cargadas para refresh real: `STRIPE_SECRET_KEY`, `MONGO_URI`.
- `MONGO_URI` y Stripe se recuperaron desde el `.env` cifrado de `Traqeer cs` usando `.env.keys`/dotenvx; no guardar secretos en el repo.
- Deploy Railway exitoso.
- URL publica: `https://customers-production-8190.up.railway.app`
- Verificado `/healthz` 200.
- Verificado `/login` 200.
- Verificado login y dashboard 200 con la clave configurada.
- Verificado login publico con `Customers Dashboard`, logo PNG y dashboard 200.
- Verificado `Actualizar datos` en produccion: completo en 101s, dashboard 200 con KPIs y datos cargados.
- Gunicorn configurado con `--timeout 240` porque el refresh inicial supera el timeout default de 30s.

## Pendiente Recomendado

- Si el refresh crece mucho, mover `Actualizar datos` a job/background task para evitar requests largos.

## Iteracion 2026-06-04 - Tareas asignables v1

Implementado en rama `codex/tareas-asignables`:

- Los recordatorios pasan a operar como tareas cliente-centricas con `assignee` opcional.
- Asignados validos v1: Luis, Dalila, Nicky y Frank; las tareas antiguas quedan como `Sin asignar`.
- Nueva vista `/tareas` con filtros por fecha, asignado y estado, agrupada en vencidas, para la fecha, proximas y completadas.
- Bandeja y Ficha muestran “Tareas”, responsable, estado relativo y accion `Completar`.
- Se mantienen las rutas compatibles `/cliente/<email>/recordatorios` y `/recordatorios/<id>/completar`.

Fuera de alcance por ahora:

- Tareas internas sin cliente.
- Usuarios configurables.
- Creacion automatica o desde boton dentro de tickets.

Verificacion:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
git diff --check
```

Resultado:

- 77 tests OK.
- `git diff --check` sin errores; solo avisos esperados de normalizacion CRLF en Windows.
- HTTP local con server en `http://127.0.0.1:5001`: `/tareas`, `/tareas?assignee=Luis&date=2026-06-04` y `/bandeja` responden 200.

## Iteracion 2026-06-04 - Bandeja unificada con tareas genericas

Implementado en rama `codex/bandeja-tareas-unificada`:

- Bandeja absorbe la experiencia de Tareas: filtros por fecha/asignado/estado, grupos de vencidas/para la fecha/proximas y formulario `Nueva tarea`.
- Se elimina la pestaña lateral `Tareas`; `GET /tareas` redirige a `/bandeja` preservando query params.
- `POST /tareas` crea tareas rapidas con titulo, fecha, asignado y cliente opcional.
- Las tareas sin cliente se guardan con `customer_email=""` y se muestran como `Sin cliente`.
- Se elimina `templates/tareas.html` para no mantener una pantalla duplicada muerta.

Fuera de alcance por ahora:

- Usuarios configurables.
- Tareas desde tickets o automatizacion de solicitudes.
- Campo de detalle separado del titulo.

Verificacion:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
git diff --check
```

Resultado:

- 80 tests OK.
- `git diff --check` sin errores; solo avisos esperados de normalizacion CRLF en Windows.
- HTTP local por test client: `/bandeja` 200, `/bandeja?assignee=Luis&date=2026-06-04` 200 y `/tareas?assignee=Luis&date=2026-06-04` 302 hacia Bandeja.

## Iteracion 2026-06-04 - Bienvenidas como tareas automaticas

Implementado en rama `codex/onboarding-tasks`:

- Bandeja crea tareas automaticas `Bienvenida pendiente` para clientes activos/trial con onboarding pendiente.
- Responsable automatico: `Nicky`.
- Fecha limite: fecha de alta del cliente; si ya paso, la tarea aparece como vencida.
- Las tareas de bienvenida usan `customer_reminders.source = "onboarding"` para evitar duplicados.
- Completar una tarea de bienvenida marca `CustomerMeta.onboarding_hecho = True`.
- `Marcar a todos como bienvenidos` tambien completa tareas onboarding activas.

Verificacion:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
git diff --check
```

Resultado:

- 82 tests OK.
- `git diff --check` sin errores; solo avisos esperados de normalizacion CRLF en Windows.
- HTTP local por test client: `/bandeja` 200 y `/bandeja?assignee=Nicky&date=2026-06-04` 200.

## Iteracion 2026-06-04 - Pulido premium de Bandeja

Implementado en rama `codex/bandeja-premium-polish`:

- `Nueva tarea` queda como accion compacta colapsada; el form mantiene titulo, fecha, asignado y cliente opcional, y sigue posteando a `/tareas`.
- Tareas queda como primer bloque y se ordena visualmente en `Vencidas`, `Hoy` y `Proximas`; `Vencidas` tiene mayor peso de alerta.
- Las filas de tareas son mas compactas: cliente/titulo a la izquierda y estado/fecha/asignado/accion a la derecha.
- El bloque separado `Onboarding pendiente` ya no renderiza en Bandeja; las bienvenidas viven solo como tareas `Bienvenida pendiente` y se completan desde la tarea.
- Churn, Impagos y Trials quedan debajo como paneles secundarios; los estados vacios usan copy corto `Sin pendientes.`.
- Se agrego cobertura de ruta para el contrato de Bandeja premium y se ajusto el contrato visual existente de Impagos.

Fuera de alcance por ahora:

- Edicion/reasignacion inline de tareas.
- Crear tareas desde tickets.
- Cambios de modelo de datos.

Verificacion:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_app_routes.AppRoutesTest.test_bandeja_premium_colapsa_nueva_tarea_y_no_duplica_onboarding -v
.\.venv\Scripts\python.exe -m unittest tests.test_app_routes -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
git diff --check
```

Resultado:

- Test focal OK; rutas OK; suite completa 83 tests OK.
- `git diff --check` sin errores; solo avisos esperados de normalizacion CRLF en Windows.
- HTTP local autenticado en `http://127.0.0.1:5021/bandeja?date=2026-06-04` -> 200; contiene `Nueva tarea` y `Hoy`, no contiene `Onboarding pendiente`.
- Capturas Chrome headless desktop/mobile generadas en `design-screenshots/bandeja-premium/`; desktop sin solapes evidentes, mobile mejorado en cuerpo de Bandeja. La navegacion movil del shell conserva su scroll horizontal existente.

Deploy Railway posterior:

- PR #65 mergeado en `main` con commit `73fe3aa`.
- Deploy manual ejecutado con `railway deployment up -m "Deploy Bandeja premium polish"`.
- Deployment Railway `4dd2683a-34a3-4568-95a2-67ea147b6bb9` -> SUCCESS.
- Produccion publica verificada:
  - `https://customers-production-8190.up.railway.app/healthz` -> 200 `{"status":"ok"}`.
  - `/login` -> 200, contiene `Customers Dashboard`.
  - `/bandeja` sin sesion -> 302 a `/login?next=/bandeja`.
- QA autenticada de produccion no ejecutada por decision de alcance; se uso QA autenticada local.
- QA local autenticada en `http://127.0.0.1:5022/bandeja?date=2026-06-04`:
  - Sin fixture temporal: 200, contiene `Nueva tarea` y `Hoy`, no contiene `Onboarding pendiente`.
  - Con fixture temporal `deploy-qa-bienvenida@example.test`: 200, contiene `Bienvenida pendiente` y `Deploy QA Bienvenida`, no contiene `Onboarding pendiente`.
  - Fixture temporal limpiado despues del smoke.
- Verificacion pre-deploy: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` -> 83 tests OK; `git diff --check` sin salida.

## Iteracion 2026-06-04 - Edicion inline de tareas en Bandeja

Implementado en rama `codex/bandeja-edicion-tareas-v2`:

- Nueva ruta autenticada `POST /recordatorios/<id>/editar`.
- Tareas manuales editables desde Bandeja: titulo, fecha limite, asignado y cliente opcional.
- Tareas manuales pueden quedar como `Sin cliente` guardando `customer_email=""`.
- Tareas automaticas de onboarding solo permiten reasignar responsable; conservan texto `Bienvenida pendiente`, fecha, cliente y `source="onboarding"`.
- Tareas completadas no se editan y redirigen con flash operativo.
- La UI de Bandeja agrega `Editar` plegado por tarea activa, manteniendo `Completar`.

Archivos tocados:

- `app.py`
- `templates/bandeja.html`
- `static/style.css`
- `tests/test_app_routes.py`
- `status.md`

Verificacion:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_app_routes.AppRoutesTest.test_bandeja_renderiza_edicion_plegada_para_tareas_activas tests.test_app_routes.AppRoutesTest.test_editar_tarea_manual_cambia_titulo_fecha_asignado_y_cliente tests.test_app_routes.AppRoutesTest.test_editar_tarea_manual_permite_quitar_cliente tests.test_app_routes.AppRoutesTest.test_editar_tarea_manual_rechaza_asignado_invalido_sin_persistir tests.test_app_routes.AppRoutesTest.test_editar_tarea_manual_rechaza_cliente_invalido_sin_persistir tests.test_app_routes.AppRoutesTest.test_editar_tarea_onboarding_solo_reasigna_responsable tests.test_app_routes.AppRoutesTest.test_editar_tarea_completada_no_persiste_cambios -v
.\.venv\Scripts\python.exe -m unittest tests.test_app_routes -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
git diff --check
```

Resultado:

- Tests focales OK.
- `tests.test_app_routes`: 51 tests OK.
- Suite completa: 90 tests OK.
- `git diff --check` con codigo 0; solo avisos esperados de normalizacion CRLF en Windows.
- Smoke local autenticado por test client:
  - `/bandeja?date=2026-06-04` -> 200 y contiene `Editar`.
  - Crear tarea manual -> 302.
  - Editar tarea manual -> 302 a referrer, persiste titulo, fecha, asignado y `customer_email=""`.
  - Reasignar onboarding -> 302.
  - Completar onboarding -> 302 y deja `CustomerMeta.onboarding_hecho=True`.
- Servidor local levantado en `http://127.0.0.1:5024` con `/healthz` 200.
- Verificacion Browser in-app no ejecutada: el conector no expuso herramienta Node REPL usable en esta sesion.

PR/deploy:

- PR #67 mergeado a `main` con commit `ab94c16`.
- Correccion de handoff PR #68 mergeada a `main` con commit `86691ee`.
- Deploy Railway posterior ejecutado desde `main` con `railway deployment up -m "Deploy Bandeja task editing"`.
- Deployment Railway `e04a1e03-2e7d-4cf9-8f7f-713f7e71976d` -> SUCCESS.
- Produccion publica verificada:
  - `https://customers-production-8190.up.railway.app/healthz` -> 200 `{"status":"ok"}`.
  - `/login` -> 200, contiene `Customers Dashboard`.
  - `/bandeja` sin sesion -> 302 a `/login?next=/bandeja`.
- QA autenticada de produccion no ejecutada: no se uso ni pidio clave en esta iteracion.

## Iteracion 2026-06-05 - Clientes cards como filtros

Implementado en rama `codex/clientes-kpi-filter-cards`:

- `/clientes` elimina la fila de chips `Todos / Activos recurrentes / Activos / Trial / Impagos / ...`.
- La toolbar conserva solo busqueda, origen, tipo, boton `Buscar` y boton `Crear cliente`.
- Las cards superiores ahora son links de filtro para activos recurrentes, agencias, one time, free colab y colab descuento.
- La card `Colabs a revisar` se reemplaza por `Bajas`, con total historico excluyendo clientes reactivados y link a `/bajas?preset=todo`.
- Los conteos de cards de clientes respetan busqueda y origen, pero no se distorsionan por el filtro de card activo.

Archivos tocados:

- `app.py`
- `templates/clientes.html`
- `static/style.css`
- `tests/test_app_routes.py`
- `status.md`

Verificacion:

```powershell
python -m unittest discover -s tests -p test_app_routes.py -k "test_clientes_usa_cards_como_filtros_y_no_muestra_chips_de_estado" -k "test_clientes_card_bajas_cuenta_historico_y_enlaza_a_bajas_todo" -v
python -m unittest discover -s tests -p test_app_routes.py -v
python -m unittest discover -s tests -v
git diff --check
```

Resultado:

- Tests focales OK.
- `test_app_routes.py`: 66 tests OK.
- Suite completa: 105 tests OK.
- `git diff --check` con codigo 0; solo avisos esperados de normalizacion CRLF en Windows.
- Smoke local autenticado con cliente Flask y snapshot temporal:
  - `/clientes?origen=instagram` renderiza 200.
  - `segmented-filter` ausente.
  - Card `Bajas` presente con link `/bajas?preset=todo`.
  - `Colabs a revisar` ausente.
  - Card `One time` conserva link de filtro con origen.

Riesgos / fuera de alcance:

- No se cambia schema, rutas backend ni datos reales.
- QA visual con Browser/Playwright no ejecutada: el navegador integrado no expuso el ejecutor necesario y Playwright no esta instalado en este clon.

PR/deploy:

- PR #78 mergeado a `main` con commit `af97afc`.
- Railway CLI fue reautenticado y actualizado de 4.44.0 a 5.1.0 porque 4.44.0 hacia timeout contra `backboard.railway.com/graphql/v2`.
- Proyecto Railway linkeado localmente: `pretty-freedom`, environment `production`, service `customers`.
- Deploy manual ejecutado con `railway up --detach -m "Deploy Clientes cards filters"`.
- Deployment Railway `b971cae6-2c31-4ec3-94ac-cff9987b8a43` -> Online.
- Produccion publica verificada:
  - `https://customers-production-8190.up.railway.app/healthz` -> 200 `{"status":"ok"}`.
  - `/login` -> 200, contiene `Customers Dashboard`.
  - `/clientes` sin sesion -> 302 a login.
- QA autenticada de produccion no ejecutada: no se uso ni pidio clave en esta iteracion.

## Iteracion 2026-06-04 - Tareas manuales desde tickets

Implementado en rama `codex/tareas-desde-tickets`:

- Nueva ruta autenticada `POST /solicitudes/<id>/tareas`.
- La ficha de ticket abierto muestra un panel compacto `Crear tarea` en la sidebar.
- La tarea creada queda asociada al cliente del ticket con `source="ticket"` y texto `Ticket #ID · <accion>`.
- Se validan texto, fecha limite y asignado obligatorio entre Luis, Dalila, Nicky y Frank.
- Tickets inexistentes o que no sean solicitud/queja devuelven 404.
- Tickets resueltos no crean tareas; requieren reabrirse antes.
- Bandeja muestra estas tareas como tareas activas normales, sin UI especial nueva.

Archivos tocados:

- `app.py`
- `templates/ticket.html`
- `tests/test_app_routes.py`
- `status.md`

Verificacion:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_app_routes.AppRoutesTest.test_ticket_abierto_renderiza_form_para_crear_tarea tests.test_app_routes.AppRoutesTest.test_crear_tarea_desde_ticket_abierto_persiste_trazabilidad tests.test_app_routes.AppRoutesTest.test_ticket_resuelto_no_crea_tarea tests.test_app_routes.AppRoutesTest.test_tarea_desde_ticket_rechaza_asignado_texto_o_fecha_invalidos tests.test_app_routes.AppRoutesTest.test_tarea_desde_ticket_inexistente_o_no_solicitud_devuelve_404 tests.test_app_routes.AppRoutesTest.test_tarea_creada_desde_ticket_aparece_en_bandeja -v
.\.venv\Scripts\python.exe -m unittest tests.test_app_routes -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
git diff --check
```

Resultado:

- Tests focales OK.
- `tests.test_app_routes`: 57 tests OK.
- Suite completa: 96 tests OK.
- `git diff --check` con codigo 0; solo avisos esperados de normalizacion CRLF en Windows.
- Smoke local por test client: crear tarea desde ticket abierto devuelve 302; `/bandeja?date=2026-06-12` devuelve 200 y contiene `Ticket #ID`, texto de tarea y asignado.

Riesgos / fuera de alcance:

- No se agrego `ticket_id` ni migracion; trazabilidad v1 vive en `source="ticket"` y el prefijo del texto.
- No se agregaron automatizaciones ni acciones rapidas en la lista `/solicitudes`.

Deploy Railway posterior:

- Ejecutado desde `main` limpio en commit `1c118e3`.
- Comando: `railway deployment up -m "Deploy ticket task creation"`.
- Deployment Railway `f60d5075-159b-4be0-ab6c-0d78deae95c1` -> SUCCESS.
- Verificacion pre-deploy:
  - `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` -> 96 tests OK.
  - `git diff --check` -> sin salida.
- Produccion publica verificada:
  - `https://customers-production-8190.up.railway.app/healthz` -> 200 `{"status":"ok"}`.
  - `/login` -> 200, contiene `Customers Dashboard`.
  - `/bandeja` sin sesion -> 302 a `/login?next=/bandeja`.
  - `/solicitudes` sin sesion -> 302 a `/login?next=/solicitudes`.
- QA autenticada de produccion:
  - Login OK.
  - `/bandeja` -> 200 con `Bandeja operativa`.
  - `/solicitudes` -> 200 con tickets.
  - `/solicitudes/7` -> 200; ticket abierto con panel `Crear tarea` y accion `/solicitudes/7/tareas`.
  - No se crearon tareas reales en produccion.

## Iteracion 2026-06-04 - Pulido Inicio V1

Implementado en rama `codex/inicio-polish-v1`:

- Inicio corrige la tira superior de KPIs para renderizar como grilla real en desktop.
- `Requiere accion` reemplaza el placeholder `CS` por contador real de tickets abiertos (`solicitud`/`queja` sin resolver).
- La accion se renombra a `Tickets abiertos` con copy operativo mas preciso.
- El filtro de periodo/canal usa clase compacta y mejora el layout responsive en mobile.
- El grafico lateral `Base actual por canal` queda acotado para no dominar la pantalla.

Archivos tocados:

- `app.py`
- `templates/dashboard.html`
- `static/style.css`
- `tests/test_app_routes.py`
- `status.md`

Verificacion:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_app_routes.AppRoutesTest.test_dashboard_inicio_pulido_muestra_kpis_en_grilla_y_tickets_reales tests.test_app_routes.AppRoutesTest.test_dashboard_usa_layout_core_redisenado tests.test_app_routes.AppRoutesTest.test_dashboard_no_muestra_finanzas_ni_gastos tests.test_app_routes.AppRoutesTest.test_polish_v5_renderiza_todas_las_pantallas_principales -v
.\.venv\Scripts\python.exe -m unittest tests.test_app_routes -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
git diff --check
```

Resultado:

- Tests focales OK.
- `tests.test_app_routes`: 58 tests OK.
- Suite completa: 97 tests OK.
- `git diff --check` con codigo 0; solo avisos esperados de normalizacion CRLF en Windows.
- Smoke local autenticado en `http://127.0.0.1:5026/?preset=todo` con Playwright:
  - Desktop 1280px sin overflow horizontal, 4 KPIs en fila, `Tickets abiertos ... 2`, grafico de canal acotado a 360px.
  - Mobile 390px sin overflow horizontal, filtros compactados, `Tickets abiertos ... 2`, grafico de canal acotado a 260px.
  - Capturas temporales: `%TEMP%\traqeer_inicio_polish_v1\inicio-desktop.png` y `inicio-mobile.png`.

Riesgos / fuera de alcance:

- No se cambia schema ni se agrega trazabilidad nueva.
- El contador de `Tickets abiertos` es global y no queda filtrado por periodo/canal en esta iteracion.
- La navegacion mobile conserva el scroll horizontal existente del shell.

PR/deploy:

- PR #72 mergeado a `main` con commit `35e8a6b`.
- Deploy manual ejecutado con `railway deployment up -m "Deploy Inicio polish v1"`.
- Deployment Railway `48828c5f-c04b-482d-9419-835c30392792` -> SUCCESS.
- Produccion publica verificada:
  - `https://customers-production-8190.up.railway.app/healthz` -> 200 `{"status":"ok"}`.
  - `/login` -> 200, contiene `Customers Dashboard`.
  - `/` sin sesion -> 302 a `/login?next=/`.
- QA autenticada de produccion:
  - Login OK.
  - `/?preset=todo` desktop 1280px -> 4 KPIs alineados en una fila, sin overflow horizontal, `Tickets abiertos ... 4`, grafico de canal 360px.
  - `/?preset=todo` mobile 390px -> sin overflow horizontal, `Tickets abiertos ... 4`, grafico de canal 260px.
  - No se crearon ni modificaron datos reales.

## Iteracion 2026-06-04 - Inicio layout acciones V2

Implementado en rama `codex/inicio-layout-actions`:

- Inicio reordena el contenido para separar lectura y operacion:
  - Arriba: dos graficos en paralelo (`Altas, bajas y trials` + `Base actual por canal`).
  - Abajo: `Requiere accion` junto a `Estado actual de la base`.
- `Requiere accion` agrega `Tareas pendientes`, enlazando a `/bandeja`.
- El contador de tareas usa `CustomerReminder` activas (`completed_at is None`) sin crear tareas ni modificar datos.
- La leyenda del grafico de canal pasa abajo para evitar cortes cuando el grafico comparte fila con el grafico principal.

Archivos tocados:

- `app.py`
- `templates/dashboard.html`
- `static/style.css`
- `tests/test_app_routes.py`
- `status.md`

Verificacion:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_app_routes.AppRoutesTest.test_dashboard_inicio_pulido_muestra_kpis_en_grilla_y_tickets_reales tests.test_app_routes.AppRoutesTest.test_dashboard_usa_layout_core_redisenado tests.test_app_routes.AppRoutesTest.test_dashboard_no_muestra_finanzas_ni_gastos tests.test_app_routes.AppRoutesTest.test_polish_v5_renderiza_todas_las_pantallas_principales -v
.\.venv\Scripts\python.exe -m unittest tests.test_app_routes -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
git diff --check
```

Resultado:

- Tests focales OK.
- `tests.test_app_routes`: 58 tests OK.
- Suite completa: 97 tests OK.
- `git diff --check` con codigo 0; solo avisos esperados de normalizacion CRLF en Windows.
- Smoke local autenticado en `http://127.0.0.1:5027/?preset=todo` con Playwright:
  - Desktop 1280px sin overflow horizontal; graficos arriba en paralelo; accion y estado abajo; `Tareas pendientes ... 2`.
  - Mobile 390px sin overflow horizontal; graficos y bloques operativos apilados en orden.
  - Capturas temporales: `%TEMP%\traqeer_inicio_layout_actions\inicio-desktop.png` y `inicio-mobile.png`.

Riesgos / fuera de alcance:

- No se cambia schema ni se crean tareas desde Inicio.
- El contador de tareas es global de activas y no queda filtrado por fecha/asignado.
- La navegacion mobile conserva el scroll horizontal existente del shell.

PR/deploy:

- PR #73 mergeado a `main` con commit `53428d8`.
- Deploy manual ejecutado con `railway deployment up -m "Deploy Inicio layout actions"`.
- Deployment Railway `b6d8f125-9c33-4546-978f-cdfb60a2f44c` -> SUCCESS.
- Produccion publica verificada:
  - `https://customers-production-8190.up.railway.app/healthz` -> 200 `{"status":"ok"}`.
  - `/login` -> 200, contiene `Customers Dashboard`.
  - `/` sin sesion -> 302 a `/login?next=/`.
- QA autenticada de produccion:
  - Login OK.
  - `/?preset=todo` desktop 1280px -> sin overflow horizontal; `chartSerie` y `chartCanal` alineados arriba; `Requiere accion` y `Estado actual de la base` abajo; `Tareas pendientes ... 7`.
  - `/?preset=todo` mobile 390px -> sin overflow horizontal; graficos apilados antes de operacion; `Tareas pendientes ... 7`.
  - No se crearon ni modificaron datos reales.

## Iteracion 2026-06-04 - Inicio balance paneles accion

Implementado en rama `codex/inicio-action-panel-balance`:

- Se quita el boton `Ver bandeja` del header de `Requiere accion`.
- La fila `Tareas pendientes` conserva el link a `/bandeja`.
- `Requiere accion` y `Estado actual de la base` ahora se estiran a la misma altura en desktop usando `dashboard-state-panel` y `align-items: stretch`.

Archivos tocados:

- `templates/dashboard.html`
- `static/style.css`
- `tests/test_app_routes.py`
- `status.md`

Verificacion:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_app_routes.AppRoutesTest.test_dashboard_inicio_pulido_muestra_kpis_en_grilla_y_tickets_reales tests.test_app_routes.AppRoutesTest.test_dashboard_usa_layout_core_redisenado -v
.\.venv\Scripts\python.exe -m unittest tests.test_app_routes -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
git diff --check
```

Resultado:

- Tests focales OK.
- `tests.test_app_routes`: 58 tests OK.
- Suite completa: 97 tests OK.
- `git diff --check` con codigo 0; solo avisos esperados de normalizacion CRLF en Windows.
- Smoke local autenticado en `http://127.0.0.1:5028/?preset=todo` con Playwright:
  - Desktop 1280px sin overflow horizontal; `Requiere accion` y `Estado actual de la base` con la misma altura `374.4px`; sin texto `Ver bandeja`; `Tareas pendientes` sigue linkeando a `/bandeja`.
  - Mobile 390px sin overflow horizontal; bloques apilados; sin texto `Ver bandeja`.

Riesgos / fuera de alcance:

- No se cambia schema, rutas ni conteos.
- La igualacion de altura aplica a los paneles de la fila operativa; en mobile se mantienen apilados.

PR/deploy:

- PR #74 mergeado a `main` con commit `f380ac7`.
- Deploy manual ejecutado con `railway deployment up -m "Deploy Inicio action panel balance"`.
- Deployment Railway `ceebff87-a8c8-4d7b-848c-71686f9e6b62` -> SUCCESS.
- Produccion publica verificada:
  - `https://customers-production-8190.up.railway.app/healthz` -> 200 `{"status":"ok"}`.
  - `/login` -> 200, contiene `Customers Dashboard`.
  - `/` sin sesion -> 302 a `/login?next=/`.
- QA autenticada de produccion:
  - Login OK.
  - `/?preset=todo` desktop 1280px -> sin overflow horizontal; sin `Ver bandeja`; `Tareas pendientes` conserva href `/bandeja`; `Requiere accion` y `Estado actual de la base` con altura igual `374.4px`.
  - `/?preset=todo` mobile 390px -> sin overflow horizontal; sin `Ver bandeja`; `Tareas pendientes` conserva href `/bandeja`.
  - No se crearon ni modificaron datos reales.

## Iteracion 2026-06-04 - Clientes V1 manuales e inactivos

Implementado en rama `codex/clientes-manuales-v1`:

- `CustomerMeta` agrega alta operativa manual: `manual_customer`, `manual_nombre` y `manual_fecha_alta`.
- `/clientes` agrega formulario compacto `Cliente manual` y `POST /clientes/manual`.
- Los clientes manuales se inyectan en el listado enriquecido; si el email ya existe en snapshot real, no se duplica y se usa la fila real con overrides manuales.
- `/cliente/<email>` abre fichas de clientes manuales aunque no existan en Stripe/Mongo.
- El orden default de `/clientes` pasa a `sort=alta&dir=desc`.
- Clientes con `manual_estado="inactivo"` quedan ocultos de `/clientes` default, Inicio, Colabs y Estadisticas; aparecen en `/clientes?estado=inactivo`.
- La ficha agrega accion `Marcar inactivo`, que marca `manual_estado="inactivo"` y vuelve a Clientes.

Archivos tocados:

- `app.py`
- `db/models.py`
- `templates/clientes.html`
- `templates/ficha.html`
- `tests/test_app_routes.py`
- `status.md`

Verificacion:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_app_routes.AppRoutesTest.test_clientes_default_ordena_por_alta_desc_y_oculta_inactivos tests.test_app_routes.AppRoutesTest.test_crear_cliente_manual_persiste_aparece_y_abre_ficha tests.test_app_routes.AppRoutesTest.test_cliente_manual_no_duplica_si_email_existe_en_snapshot_real tests.test_app_routes.AppRoutesTest.test_ficha_permita_marcar_cliente_como_inactivo -v
.\.venv\Scripts\python.exe -m unittest tests.test_app_routes -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
git diff --check
```

Resultado:

- Tests focales OK.
- `tests.test_app_routes`: 62 tests OK.
- Suite completa: 101 tests OK.
- `git diff --check` con codigo 0; solo avisos esperados de normalizacion CRLF en Windows.
- Smoke local Playwright con DB SQLite temporal en `http://127.0.0.1:5030/clientes`:
  - Desktop 1280px y mobile 390px sin overflow horizontal.
  - Default muestra formulario manual, ordena por alta desc y oculta inactivos.
  - `/clientes?estado=inactivo` muestra el cliente oculto.
  - Capturas generadas en `design-screenshots/clientes-v1-smoke/` y no versionadas.

Riesgos / fuera de alcance:

- No se sincronizan clientes manuales a Stripe/Mongo.
- No se elimina informacion real; ocultar equivale a marcar inactivo.
- La auditoria/pulido de ficha queda para la siguiente iteracion.

Hotfix deploy Railway:

- Primer deploy `e064b866-ddf9-4e79-b1bd-ec793a7c83fa` crasheo porque Postgres rechazo `ALTER TABLE customer_meta ADD COLUMN manual_customer BOOLEAN NOT NULL DEFAULT 0`.
- Se corrigio la migracion local a `DEFAULT FALSE`, compatible con Postgres, y se agrego test preventivo.
- Verificacion hotfix:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_app_routes.AppRoutesTest.test_migracion_manual_customer_usa_default_boolean_postgres -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
git diff --check
```

Resultado: test focal OK; suite completa 102 tests OK; `git diff --check` sin errores reales, solo avisos CRLF de Windows.

## Iteracion 2026-06-04 - Clientes V2 crear desde toolbar

Implementado en rama `codex/clientes-v2-toolbar`:

- `/clientes` elimina el panel permanente `Cliente manual`.
- La toolbar de clientes agrega boton `Crear cliente` junto al buscador/filtros.
- El alta manual se mueve a un modal compacto con nombre, email, fecha de alta, tipo, estado y origen.
- El modal conserva `POST /clientes/manual`; al crear redirige a `/cliente/<email>`.
- Los labels del modal quedan asociados con `for/id` para accesibilidad y smoke Playwright.
- La validacion minima de nombre/email mantiene redirect a `/clientes` sin persistir datos incompletos.

Archivos tocados:

- `templates/clientes.html`
- `static/style.css`
- `tests/test_app_routes.py`
- `status.md`

Verificacion:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_app_routes.AppRoutesTest.test_clientes_busca_por_usuario_y_whatsapp_con_placeholder_simple tests.test_app_routes.AppRoutesTest.test_crear_cliente_manual_rechaza_datos_minimos_incompletos tests.test_app_routes.AppRoutesTest.test_crear_cliente_manual_persiste_aparece_y_abre_ficha tests.test_app_routes.AppRoutesTest.test_clientes_default_ordena_por_alta_desc_y_oculta_inactivos -v
.\.venv\Scripts\python.exe -m unittest tests.test_app_routes -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
git diff --check
```

Resultado:

- Tests focales OK.
- `tests.test_app_routes`: 64 tests OK.
- Suite completa: 103 tests OK.
- `git diff --check` con codigo 0; solo avisos esperados de normalizacion CRLF en Windows.
- Smoke local Playwright autenticado en `http://127.0.0.1:5001/clientes`:
  - Desktop 1280px y mobile 390px sin overflow horizontal.
  - Boton `Crear cliente` visible.
  - Modal abre/cierra y muestra campos minimos por label.
  - Capturas generadas en `design-screenshots/clientes-v2-toolbar/`.

Riesgos / fuera de alcance:

- No se cambia schema ni rutas backend.
- No se sincronizan clientes manuales a Stripe/Mongo.

Deploy Railway posterior:

- PR #76 mergeado a `main` con commit `ed45f31`.
- Deploy manual ejecutado desde `main` con `railway deployment up -m "Deploy Clientes V2 toolbar create"`.
- Deployment Railway `bb56de65-1c0b-4385-9ee7-1b6fb28ce26a` -> SUCCESS.
- Produccion publica verificada:
  - `https://customers-production-8190.up.railway.app/healthz` -> 200 `{"status":"ok"}`.
  - `/login` -> 200, contiene `Customers Dashboard`.
  - `/clientes` sin sesion -> 302 a `/login?next=/clientes`.
- QA autenticada de produccion no ejecutada: no se uso ni pidio clave en esta iteracion.
