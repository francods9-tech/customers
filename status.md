# Estado Traqeer AM Dashboard Codex

Fecha: 2026-06-01.

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
  - Los comentarios internos no piden ni guardan autor.
  - Los estados tienen chips de color para diferenciar abierta, en gestion, comunicar y resuelta.
  - Las abiertas pueden eliminarse desde la lista.
  - En abiertas solo se actualizan estado e importancia; la categoria queda fija luego de crear el ticket.
  - La administracion visual de categorias se oculto de `/solicitudes`; las categorias se manejan internamente.

## Verificacion

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
