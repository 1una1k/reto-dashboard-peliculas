"""Transformaciones y validaciones independientes de la interfaz."""
import re
import pandas as pd

MOVIE_COLUMNS = ["name", "genre", "director", "company"]


def movie_dataframe(records):
    """Normaliza incluso una colección vacía o documentos con campos ausentes."""
    df = pd.DataFrame(records, columns=MOVIE_COLUMNS).fillna("").astype(str)
    return df.sort_values("name", key=lambda s: s.str.casefold()).reset_index(drop=True)


def search_title(df, text):
    """Coincidencia literal 'contiene', sin distinguir mayúsculas/minúsculas."""
    needle = text.strip().casefold()
    mask = df["name"].str.casefold().str.contains(needle, regex=False, na=False)
    return df.loc[mask].reset_index(drop=True)


def filter_by_director(df, director):
    """Filtra el dataset cargado al inicio usando el director seleccionado."""
    return df.loc[df["director"].eq(director)].reset_index(drop=True)


def validate_movie(name, genre, director, company):
    values = [value.strip() for value in (name, genre, director, company)]
    if not all(values):
        raise ValueError("Completa título, género, director y compañía.")
    if any(len(v) > limit for v, limit in zip(values, (200, 100, 200, 200))):
        raise ValueError("Uno de los campos supera la longitud permitida.")
    return dict(zip(MOVIE_COLUMNS, values))


def validate_guest(email, comment):
    email, comment = email.strip(), comment.strip()
    if len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise ValueError("Escribe un correo electrónico válido.")
    if not 1 <= len(comment) <= 2000:
        raise ValueError("Escribe un comentario de 1 a 2000 caracteres.")
    return {"email": email, "comment": comment}
