from app import app
from db import db
from sync import refrescar_snapshot


def main():
    with app.app_context():
        try:
            payload = refrescar_snapshot()
        finally:
            db.session.remove()
            db.engine.dispose()
    resumen = payload.get("resumen") or {}
    print(
        "refresh ok "
        f"clientes={len(payload.get('clientes', []))} "
        f"activos={resumen.get('activos', 0)} "
        f"trial={resumen.get('trial', 0)} "
        f"impago={resumen.get('impago', 0)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
