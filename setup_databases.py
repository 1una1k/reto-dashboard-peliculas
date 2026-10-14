"""Inicializa los datos reales. Ejecutar una vez antes del despliegue."""
import argparse
import hashlib
import json
from pathlib import Path
import tomllib
from google.api_core.exceptions import AlreadyExists
from catalog import validate_movie
from database import create_firestore_client, connect_postgres, read_movies

ROOT = Path(__file__).resolve().parent


def seed_movies(settings):
    client = create_firestore_client(settings)
    data = json.loads((ROOT / "data/movies.json").read_text(encoding="utf-8"))
    inserted = 0
    for row in data:
        movie = validate_movie(**row)
        # ID estable + create: reejecutar no duplica ni sobrescribe documentos.
        key = hashlib.sha256(f"{movie['name']}|{movie['director']}".encode()).hexdigest()
        try:
            client.collection("movies").document(key).create(movie, timeout=15, retry=None)
            inserted += 1
        except AlreadyExists:
            pass
    total = len(read_movies(client))
    print(f"Firestore: {inserted} documentos nuevos; {total} películas en movies.")
    if total < 20:
        raise RuntimeError("La colección debe contener al menos 20 documentos.")


def setup_postgres(settings):
    # La base guests debe existir; se crea en Aiven o con sql/create_database.sql.
    if settings["postgres"]["dbname"] != "guests":
        raise ValueError("Usa dbname = 'guests' para cumplir el reto.")
    with connect_postgres(settings) as conn:
        conn.execute((ROOT / "sql/schema.sql").read_text(encoding="utf-8"))
        count = conn.execute("SELECT COUNT(*) AS total FROM people").fetchone()["total"]
    print(f"PostgreSQL: tabla guests.public.people lista; {count} comentarios.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--secrets", type=Path, default=ROOT / ".streamlit/secrets.toml")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--firestore-only", action="store_true")
    group.add_argument("--postgres-only", action="store_true")
    args = parser.parse_args()
    try:
        settings = tomllib.loads(args.secrets.read_text(encoding="utf-8"))
        if not args.postgres_only:
            seed_movies(settings)
        if not args.firestore_only:
            setup_postgres(settings)
    except Exception as exc:
        # No imprimir objetos de conexión ni credenciales en los mensajes.
        raise SystemExit(f"No se completó la inicialización ({type(exc).__name__}). "
                         "Revisa secrets.toml, permisos, conexión y la base guests; después reintenta.") from None


if __name__ == "__main__":
    main()
