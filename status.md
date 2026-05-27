# Estado Traqeer AM Dashboard Codex

Fecha: 2026-05-27.

Carpeta de trabajo aislada:

```text
C:\Users\Franco Salemme\OneDrive\Escritorio\traqeer-am-dashboard-codex
```

No tocar como fuente de verdad de Claude:

```text
C:\Users\Franco Salemme\OneDrive\Escritorio\traqeer-am-dashboard
```

## Hecho

- Clientes ahora tiene buscador por nombre/email.
- Origen incluye `XBIZ` como canal seleccionable y filtrable.
- Clientes tiene filtros por activos recurrentes, activos, trial, impagos, inactivos, one time y free colab.
- La ficha permite ajustar manualmente plan, estado y tipo de cliente.
- `One time payment` y `Free por colab` no suman como activos recurrentes.
- Dashboard separa activos recurrentes, one time y free colab.
- Se agregaron pruebas unitarias para reglas de negocio.
- Bandeja muestra impagos con dias de atraso, monto pendiente y link de ultima factura cuando el snapshot lo trae.
- La lista de Clientes/Impagos tambien muestra la columna Atencion con dias de impago y factura.
- El snapshot nuevo guarda `ultima_factura_fecha_raw`, `ultima_factura_url`, `impago_monto_pendiente`, `impago_dias` y estado de factura para impagos Stripe.
- Se agrego refresh parcial solo Stripe para enriquecer impagos sin necesitar Mongo.
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
- Solicitudes ahora tiene dashboard por periodo:
  - Presets de tiempo, incluyendo `Todo`.
  - KPIs de registradas, abiertas actuales, Customer Success, Operaciones y resueltas.
  - Grafico temporal de solicitudes por dia o semana.

## Verificacion

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

Resultado: `imports ok 32`.

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
- `/?preset=todo` 200 con preset Todo
- `/mensajes` 200 con wiki editable de mensajes
- `/mensajes?q=checkpoint` 200 con plantillas del pack WhatsApp
- `/static/traqeer-logo.svg` 200
- `/healthz` 200 publico
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

Servidor activo:

```text
http://127.0.0.1:5002
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
- Variables pendientes para refresh real: `STRIPE_SECRET_KEY`, `MONGO_URI`.
- Deploy Railway exitoso.
- URL publica: `https://customers-production-8190.up.railway.app`
- Verificado `/healthz` 200.
- Verificado `/login` 200.
- Verificado login y dashboard 200 con la clave configurada.
- Verificado login publico con `Customers Dashboard`, logo PNG y dashboard 200.

## Pendiente Recomendado

- Cargar `STRIPE_SECRET_KEY` y `MONGO_URI` en Railway para poder usar `Actualizar datos`.
- Presionar `Actualizar datos` en produccion cuando esten las variables reales.
