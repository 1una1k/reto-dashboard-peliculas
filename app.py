"""Dashboard del reto: catálogo en Firestore y visitas en PostgreSQL."""
import streamlit as st

from catalog import filter_by_director, search_title, validate_guest, validate_movie
from repository import (
    DEMO, add_guest, add_movie, load_guests, load_movies, refresh_movies,
)

st.set_page_config(page_title="CineScope | Catálogo de películas", page_icon="🎬", layout="wide")
st.markdown("""<style>
.block-container {padding-top: 2rem; max-width: 1380px;}
[data-testid="stMetric"] {background: #191d29; padding: 18px; border-radius: 12px;}
[data-testid="stSidebar"] {border-right: 1px solid #2a2e3b;}
</style>""", unsafe_allow_html=True)
st.caption("CINESCOPE / EXPLORA · DESCUBRE · COMPARTE")
st.title("Una mirada a tu próximo filme")
st.write("Explora el catálogo, encuentra películas por título o director y deja tu recomendación.")
if DEMO:
    st.warning("Modo demostración: datos temporales de esta sesión. No está conectado a Firestore ni PostgreSQL.")

if message := st.session_state.pop("flash", None):
    st.success(message)

# Se llama al iniciar cada ejecución. La caché evita lecturas innecesarias a Firestore.
movies_ready = True
try:
    df = load_movies()
except Exception as exc:
    from catalog import movie_dataframe
    df = movie_dataframe([])
    movies_ready = False
    st.error("No se pudo leer Firestore. Revisa las credenciales, los permisos y la base (default).")
    st.caption(f"Tipo de error: {type(exc).__name__}. Consulta la guía de configuración del proyecto.")

st.session_state.setdefault("filter_mode", "all")
st.session_state.setdefault("filter_value", "")
st.session_state.setdefault("show_guests", False)

with st.sidebar:
    st.title("🎬 CineScope")
    st.caption("TU CATÁLOGO DE CINE")
    show_all = st.checkbox("Visualizar todos los filmes", value=True, key="show_all")
    if st.button("Actualizar catálogo", key="refresh", width="stretch"):
        refresh_movies()
        st.rerun()

    st.divider()
    st.subheader("Buscar por título")
    title = st.text_input("El título contiene", placeholder="Ej. matrix", key="title_query")
    if st.button("Buscar título", key="search", width="stretch"):
        if title.strip():
            st.session_state.filter_mode = "title"
            st.session_state.filter_value = title.strip()
        else:
            st.warning("Escribe parte de un título.")

    st.subheader("Filtrar por director")
    directors = sorted(d for d in df["director"].unique() if d)
    director = st.selectbox("Director", directors, index=0 if directors else None, key="director")
    if st.button("Buscar director", key="filter_director", disabled=not directors, width="stretch"):
        st.session_state.filter_mode = "director"
        st.session_state.filter_value = director
    if st.button("Limpiar búsqueda", key="clear", width="stretch"):
        st.session_state.filter_mode = "all"
        st.session_state.filter_value = ""

    with st.expander("＋ Agregar una película"):
        with st.form("movie_form", clear_on_submit=True):
            name = st.text_input("Título", max_chars=200, key="new_name")
            genre = st.text_input("Género", max_chars=100, key="new_genre")
            new_director = st.text_input("Director del filme", max_chars=200, key="new_director")
            company = st.text_input("Compañía", max_chars=200, key="new_company")
            save_movie = st.form_submit_button("Guardar película", disabled=not movies_ready, width="stretch")
        if save_movie:
            try:
                movie = validate_movie(name, genre, new_director, company)
                add_movie(movie)
            except ValueError as exc:
                st.warning(str(exc))
            except Exception as exc:
                st.error(f"No se pudo guardar la película ({type(exc).__name__}).")
            else:
                refresh_movies()
                st.session_state.flash = f"Película guardada: {movie['name']}."
                st.rerun()

    st.divider()
    with st.expander("✎ Firmar el libro de visitas"):
        with st.form("guest_form", clear_on_submit=True):
            email = st.text_input("Correo electrónico", max_chars=254, key="guest_email")
            comment = st.text_area("Comentario", max_chars=2000, key="guest_comment")
            st.caption("Tu correo y comentario serán visibles en el libro de visitas.")
            save_guest = st.form_submit_button("Registrar comentario", width="stretch")
        if save_guest:
            try:
                guest = validate_guest(email, comment)
                add_guest(guest)
            except ValueError as exc:
                st.warning(str(exc))
            except Exception as exc:
                st.error(f"No se pudo registrar el comentario ({type(exc).__name__}). Revisa PostgreSQL.")
            else:
                st.session_state.show_guests = True
                st.session_state.flash = "Gracias. Tu comentario se guardó correctamente."
                st.rerun()
    if st.button("Ver comentarios", key="view_guests", width="stretch"):
        st.session_state.show_guests = True
    if st.session_state.show_guests and st.button("Ocultar comentarios", key="hide_guests", width="stretch"):
        st.session_state.show_guests = False

col1, col2, col3 = st.columns(3)
col1.metric("Películas en el catálogo", len(df))
col2.metric("Directores", df.loc[df.director.ne(""), "director"].nunique())
col3.metric("Géneros", df.loc[df.genre.ne(""), "genre"].nunique())
st.caption("Datos de demostración" if DEMO else "Catálogo: Firestore · Libro de visitas: PostgreSQL")

if not df.empty:
    left, right = st.columns([1, 1])
    with left:
        st.subheader("Películas por género")
        st.bar_chart(df.groupby("genre").size().rename("Películas"), color="#ff5964")
    with right:
        st.subheader("Directores en el catálogo")
        counts = df.groupby("director").size().sort_values(ascending=False).head(8)
        st.bar_chart(counts.rename("Películas"), horizontal=True, color="#8c9eff")

if show_all:
    st.header("Todos los filmes")
    st.caption(f"{len(df)} películas disponibles")
    st.dataframe(df, hide_index=True, width="stretch")

mode = st.session_state.filter_mode
value = st.session_state.filter_value
if mode != "all":
    st.header("Resultados de búsqueda")
    if mode == "title":
        result = search_title(df, value)
        st.write(f"El título contiene: **{value}**")
    else:
        result = filter_by_director(df, value)
        st.write(f"Director: **{value}**")
    st.success(f"Total de filmes encontrados: {len(result)}")
    if result.empty:
        st.info("No hay coincidencias. Prueba con otro título o director.")
    else:
        st.dataframe(result, hide_index=True, width="stretch")

if st.session_state.show_guests:
    st.header("Libro de visitas")
    try:
        guests = load_guests()
    except Exception as exc:
        st.error(f"No se pudieron consultar los comentarios ({type(exc).__name__}). Revisa PostgreSQL.")
    else:
        st.caption(f"{len(guests)} comentarios")
        if guests.empty:
            st.info("Todavía no hay comentarios. ¡Sé el primero!")
        else:
            st.dataframe(guests, hide_index=True, width="stretch")

st.divider()
st.caption("Proyecto académico · Desarrollo Web para un Portal de Inteligencia Analítica")
