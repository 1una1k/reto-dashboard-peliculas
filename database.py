"""Acceso real a Firestore y PostgreSQL; las credenciales se reciben aparte."""
import psycopg
from psycopg.rows import dict_row
from google.cloud import firestore
from google.oauth2 import service_account


def create_firestore_client(settings):
    info = dict(settings["firebase"])
    info["private_key"] = info["private_key"].replace("\\n", "\n")
    credentials = service_account.Credentials.from_service_account_info(info)
    return firestore.Client(project=info["project_id"], credentials=credentials)


def read_movies(client):
    return [doc.to_dict() for doc in client.collection("movies").stream(timeout=15, retry=None)]


def insert_movie(client, movie):
    # ID automático: dos filmes con el mismo nombre no se sobrescriben.
    client.collection("movies").document().create(movie, timeout=15, retry=None)


def connect_postgres(settings):
    config = dict(settings["postgres"])
    sslmode = config.get("sslmode", "require")
    if sslmode not in {"require", "verify-ca", "verify-full"}:
        raise ValueError("PostgreSQL requiere una conexión TLS.")
    kwargs = {k: config[k] for k in ("host", "port", "dbname", "user", "password")}
    kwargs.update(sslmode=sslmode, connect_timeout=10,
                  options="-c statement_timeout=15000", row_factory=dict_row)
    if config.get("sslrootcert"):
        kwargs["sslrootcert"] = config["sslrootcert"]
    return psycopg.connect(**kwargs)


def insert_guest(settings, guest):
    # Parámetros separados del SQL: admite apóstrofos y evita inyección SQL.
    with connect_postgres(settings) as conn:
        conn.execute("INSERT INTO people (email, comment) VALUES (%s, %s)",
                     (guest["email"], guest["comment"]))
    # El context manager confirma la transacción o hace rollback si falla.


def read_guests(settings):
    with connect_postgres(settings) as conn:
        return conn.execute("SELECT email, comment FROM people ORDER BY email, comment").fetchall()
