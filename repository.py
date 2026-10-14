"""Orquestación, caché de lectura y modo local explícito para demostraciones."""
import json
import os
from pathlib import Path
import pandas as pd
import streamlit as st
from catalog import movie_dataframe
from database import create_firestore_client, read_movies, insert_movie, read_guests, insert_guest

DEMO = os.environ.get("MOVIES_DEMO") == "1"
ROOT = Path(__file__).resolve().parent


@st.cache_resource
def firestore_client():
    return create_firestore_client(st.secrets)


@st.cache_data(ttl=60, show_spinner="Cargando catálogo…")
def cloud_movies():
    return movie_dataframe(read_movies(firestore_client()))


def load_movies():
    """Lee toda la colección movies en un dataframe al arrancar la aplicación."""
    if DEMO:
        if "demo_movies" not in st.session_state:
            st.session_state.demo_movies = json.loads((ROOT / "data/movies.json").read_text(encoding="utf-8"))
        return movie_dataframe(st.session_state.demo_movies)
    return cloud_movies()


def refresh_movies():
    cloud_movies.clear()


def add_movie(movie):
    if DEMO:
        st.session_state.demo_movies.append(movie)
    else:
        insert_movie(firestore_client(), movie)


def add_guest(guest):
    if DEMO:
        st.session_state.setdefault("demo_guests", []).append(guest)
    else:
        insert_guest(st.secrets, guest)


def load_guests():
    rows = st.session_state.get("demo_guests", []) if DEMO else read_guests(st.secrets)
    return pd.DataFrame(rows, columns=["email", "comment"])
