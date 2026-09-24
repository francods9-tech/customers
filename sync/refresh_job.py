import logging

from app import app, refresh_and_record_counts
from db import db


def main():
    with app.app_context():
        try:
            payload = refresh_and_record_counts()
        except Exception:
            # Non-zero exit makes the Railway cron run show as failed.
            logging.exception("refresh failed")
            return 1
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
