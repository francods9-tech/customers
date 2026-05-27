"""Regenera el snapshot con credenciales reales y lo guarda en la base local.
Uso (desde el workspace, con credenciales): dotenvx run -f .env.ceo -- <venv python> seed_snapshot.py"""
from app import app
from sync import refrescar_snapshot

with app.app_context():
    s = refrescar_snapshot()
    print("resumen:", s["resumen"])
    print("altas:", len(s["eventos"]["altas"]), "bajas:", len(s["eventos"]["bajas"]))
