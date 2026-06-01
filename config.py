import os
import pathlib
from dotenv import load_dotenv

# Carga el .env de este proyecto sin depender del directorio actual.
# override=False: si las vars ya vienen del entorno (ej. Railway), ganan esas.
load_dotenv(pathlib.Path(__file__).resolve().parent / ".env", override=False)


def _normalize_db_url(url: str) -> str:
    """Railway entrega 'postgresql://'. SQLAlchemy + psycopg3 quiere
    'postgresql+psycopg://'. Si no hay URL, caemos a SQLite local."""
    if not url:
        # Ruta absoluta y determinística (no depende del directorio de ejecución).
        local_db = pathlib.Path(__file__).resolve().parent / "am_local.db"
        return f"sqlite:///{local_db.as_posix()}"
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-inseguro-cambiar")
    APP_PASSWORD = os.environ.get("APP_PASSWORD", "")

    SQLALCHEMY_DATABASE_URI = _normalize_db_url(os.environ.get("DATABASE_URL", ""))
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MONGO_URI = os.environ.get("MONGO_URI", "")
    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
    FINANCE_DATA_DIR = os.environ.get(
        "FINANCE_DATA_DIR",
        str(pathlib.Path(__file__).resolve().parent / "data"),
    )
