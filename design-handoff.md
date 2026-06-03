# Design Handoff - Customers Dashboard

Fecha: 2026-06-03

## Objetivo

Redisenar la UI/UX de Customers Dashboard manteniendo la funcionalidad actual. La app es una herramienta interna diaria para Customer Success y Operaciones, no una landing page ni una pieza de marketing.

El objetivo principal es mejorar claridad, jerarquia visual, velocidad de lectura y ergonomia operativa sin reimplementar producto desde cero.

## Producto

Customers Dashboard centraliza la operacion de clientes de Traqeer:

- Estado de clientes y suscripciones.
- Activos recurrentes, trials, impagos, one time y free colab.
- Bandeja operativa con impagos, churn risk, trials, colabs a revisar y recordatorios.
- Solicitudes/tickets de clientes con estados, importancia, comentarios internos y autores.
- Ficha de cliente con salud, contacto, origen, ajustes manuales, solicitudes y recordatorios.
- Bajas con motivos.
- Colabs y creadores.
- Wiki editable de mensajes.

## Usuario Principal

Equipo interno de Customer Success y Operaciones.

Necesitan:

- Leer rapido que requiere accion.
- Encontrar clientes por nombre, email, usuario o WhatsApp.
- Priorizar tickets, impagos y recordatorios.
- Editar datos operativos con pocos clics.
- Ver contexto del cliente antes de contactar.
- Evitar una interfaz decorativa o tipo landing.

## Restricciones

- Mantener toda la funcionalidad actual.
- No agregar features grandes sin validacion.
- No convertir la app en landing page.
- No usar composicion de marketing con heroes grandes.
- Desktop es prioridad; mobile debe ser usable.
- Mantener densidad operativa, pero con mejor jerarquia y respiracion visual.
- Preferir un SaaS interno sobrio, claro y profesional.
- Tablas, formularios, badges y acciones deben ser faciles de escanear.
- Evitar paletas de un solo color dominante.
- Evitar tarjetas dentro de tarjetas.
- No ocultar informacion critica detras de patrones demasiado decorativos.

## Rutas Clave

Produccion:

```text
https://customers-production-8190.up.railway.app/
```

Rutas para revisar:

```text
/                       Inicio / dashboard
/clientes               Tabla de clientes
/cliente/<email>        Ficha de cliente
/bandeja                Bandeja operativa
/solicitudes            Solicitudes / tickets
/solicitudes/<id>       Ficha de ticket
/colabs                 Colabs
/bajas                  Bajas
/mensajes               Wiki de mensajes
```

## Pantallas A Redisenar Primero

Prioridad 1:

- `/clientes`
- `/cliente/<email>`
- `/solicitudes`
- `/solicitudes/<id>`

Prioridad 2:

- `/`
- `/bandeja`
- `/colabs`
- `/bajas`
- `/mensajes`

## Problemas UX/UI A Auditar

Revisar especialmente:

- Jerarquia de informacion en dashboards y fichas.
- Escaneabilidad de tablas y listas largas.
- Consistencia de botones, badges, chips y formularios.
- Separacion entre informacion, estado y acciones.
- Acciones primarias/secundarias/destructivas.
- Formularios densos en ficha de cliente y solicitudes.
- Lectura rapida de tickets: estado, importancia, aging, comentarios.
- Mobile: que no haya overflow, texto apretado ni controles dificiles.
- Navegacion: que cada pantalla deje claro donde estoy y que puedo hacer.

## Output Esperado Del Disenador

Pedir una entrega en este orden:

1. Auditoria UI/UX de las pantallas actuales.
2. Sistema visual propuesto:
   - colores,
   - tipografia,
   - espaciados,
   - botones,
   - inputs,
   - badges/chips,
   - tablas,
   - paneles,
   - estados.
3. Redisenos desktop de las pantallas de Prioridad 1.
4. Version mobile de `/clientes`, `/cliente/<email>` y `/solicitudes`.
5. Notas de comportamiento e interacciones.
6. Priorizacion de implementacion por impacto.

Ideal:

- Link de Figma editable, o
- mockups con especificacion visual suficiente para implementar.

## Prompt Para Claude / Tool De Diseno

```text
Te paso el estado actual de una app interna llamada Customers Dashboard. Quiero que audites y mejores la UI/UX sobre la base existente, no que inventes una app nueva.

Contexto:
Es una herramienta interna de Customer Success y Operaciones para gestionar clientes, impagos, recordatorios, solicitudes/tickets, colabs, bajas y mensajes.

No es una landing page. Es una herramienta de trabajo diario. La prioridad es claridad, velocidad de lectura, jerarquia visual y ergonomia operativa.

Objetivo:
Redisenar la interfaz manteniendo toda la funcionalidad actual. Quiero una UI mas clara, profesional y consistente, tipo SaaS interno sobrio.

Restricciones:
- Mantener funcionalidad.
- No agregar features grandes.
- No convertirlo en marketing/landing.
- Desktop es prioridad; mobile debe ser usable.
- Mantener densidad operativa.
- Mejorar tablas, listas, formularios, badges, acciones y navegacion.
- No usar heroes grandes ni decoracion innecesaria.

Pantallas clave:
- Inicio
- Clientes
- Ficha de cliente
- Bandeja
- Solicitudes
- Ficha de ticket
- Colabs
- Bajas
- Mensajes

Primero quiero que hagas:
1. Auditoria UI/UX de lo actual.
2. Sistema visual propuesto.
3. Redisenos desktop de Clientes, Ficha de cliente, Solicitudes y Ficha de ticket.
4. Version mobile de Clientes, Ficha de cliente y Solicitudes.
5. Priorizacion de implementacion por impacto.

No necesito codigo todavia. Necesito una propuesta visual y UX implementable sobre el producto actual.
```

## Screenshots A Adjuntar

Adjuntar la carpeta `design-screenshots` completa si esta disponible.

Capturas recomendadas:

```text
desktop-01-inicio.png
desktop-02-clientes.png
desktop-03-ficha-cliente.png
desktop-04-bandeja.png
desktop-05-solicitudes.png
desktop-06-ticket.png
desktop-07-colabs.png
desktop-08-bajas.png
desktop-09-mensajes.png
mobile-01-clientes.png
mobile-02-ficha-cliente.png
mobile-03-solicitudes.png
```

## Como Traerlo De Vuelta A Codex

Cuando exista propuesta de diseno:

- Pegar el resumen de auditoria.
- Adjuntar link de Figma o screenshots/mockups.
- Indicar que pantallas aprobaron.
- Implementar por tandas pequenas:
  1. sistema visual base,
  2. Clientes,
  3. Ficha de cliente,
  4. Solicitudes/Ticket,
  5. resto de pantallas.

Cada tanda debe cerrar con tests razonables, verificacion visual responsive y deploy.
