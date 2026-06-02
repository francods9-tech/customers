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

## Refresh diario

El boton `Actualizar datos` queda como fallback manual. Para automatizar el refresh:

1. Crear un segundo servicio Railway desde el mismo repo.
2. Configurar su start command como:

```text
python -m sync.refresh_job
```

3. Configurar `Cron Schedule` en Settings:

```text
0 4 * * *
```

Railway evalua cron en UTC. `0 4 * * *` equivale a 06:00 Europe/Madrid durante CEST; revisar a `0 5 * * *` durante CET si se quiere mantener 06:00 Madrid todo el ano.

El job debe terminar al finalizar. Si una ejecucion sigue activa cuando toca la siguiente, Railway salta esa ejecucion.

## Diagnostico de activos recurrentes

Para explicar una diferencia entre los dos ultimos snapshots:

```powershell
python -m scripts.active_recurrent_diff
```

En produccion, ejecutarlo dentro del servicio Railway o con una URL `DATABASE_URL` accesible desde el entorno donde corre el comando.
