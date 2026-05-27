# Deploy en Railway

## Servicio

Railway puede detectar este proyecto con Nixpacks.

Comando de arranque:

```text
gunicorn app:app
```

Healthcheck recomendado:

```text
/healthz
```

## Variables

Configurar en Railway:

```text
APP_PASSWORD=clave-para-el-equipo
SECRET_KEY=valor-largo-random
DATABASE_URL=lo provee Railway Postgres
MONGO_URI=mongodb+srv://...
STRIPE_SECRET_KEY=sk_live_...
```

`DATABASE_URL` debe venir de un plugin Postgres de Railway. En local, si no existe, la app usa SQLite.

## Primer uso

1. Crear proyecto Railway.
2. Agregar servicio desde repo o carpeta.
3. Agregar Postgres.
4. Cargar variables.
5. Deploy.
6. Entrar con `APP_PASSWORD`.
7. Presionar `Actualizar datos` para generar el primer snapshot.
