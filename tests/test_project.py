"""Pruebas locales: lógica, contratos de persistencia e interfaz Streamlit."""
import json
import os
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch
from catalog import movie_dataframe, search_title, filter_by_director, validate_guest, validate_movie
from database import insert_guest, read_guests, insert_movie, read_movies

ROOT = Path(__file__).resolve().parents[1]


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.movies = json.loads((ROOT / "data/movies.json").read_text(encoding="utf-8"))
        self.df = movie_dataframe(self.movies)

    def test_seed_has_twenty_valid_unique_movies(self):
        self.assertEqual(len(self.movies), 20)
        self.assertEqual(len({(r['name'], r['director']) for r in self.movies}), 20)
        for row in self.movies:
            self.assertEqual(validate_movie(**row), row)

    def test_search_is_case_insensitive_and_substring(self):
        self.assertEqual(search_title(self.df, "  INTEr  ")["name"].tolist(), ["Interstellar"])

    def test_search_does_not_interpret_regular_expressions(self):
        self.assertTrue(search_title(self.df, ".*").empty)

    def test_director_returns_only_matching_movies(self):
        self.assertEqual(len(filter_by_director(self.df, "Christopher Nolan")), 4)
        self.assertTrue(filter_by_director(self.df, "No existe").empty)

    def test_empty_and_incomplete_collection(self):
        self.assertEqual(movie_dataframe([]).shape, (0, 4))
        self.assertEqual(movie_dataframe([{"name": "Solo título"}]).iloc[0]["genre"], "")

    def test_invalid_inputs_are_rejected(self):
        for email, comment in [("sin-arroba", "Hola"), ("a@example.com", " "), ("a@example.com", "x" * 2001)]:
            with self.assertRaises(ValueError):
                validate_guest(email, comment)
        with self.assertRaises(ValueError):
            validate_movie("Título", " ", "Director", "Compañía")

    @patch("database.connect_postgres")
    def test_sql_uses_parameters_and_transaction_context(self, connect):
        guest = {"email": "o'hara@example.com", "comment": "'); DROP TABLE people; --"}
        insert_guest({}, guest)
        conn = connect.return_value.__enter__.return_value
        conn.execute.assert_called_once_with(
            "INSERT INTO people (email, comment) VALUES (%s, %s)",
            (guest['email'], guest['comment']))
        connect.return_value.__exit__.assert_called_once_with(None, None, None)

    def test_firestore_read_and_insert_contracts(self):
        client = MagicMock()
        snapshot = MagicMock()
        snapshot.to_dict.return_value = self.movies[0]
        client.collection.return_value.stream.return_value = [snapshot]
        self.assertEqual(read_movies(client), [self.movies[0]])
        insert_movie(client, self.movies[0])
        client.collection.return_value.document.return_value.create.assert_called_once_with(
            self.movies[0], timeout=15, retry=None)

    @patch("database.connect_postgres")
    def test_postgres_reads_guestbook(self, connect):
        rows = [{"email": "a@example.com", "comment": "Excelente"}]
        connect.return_value.__enter__.return_value.execute.return_value.fetchall.return_value = rows
        self.assertEqual(read_guests({}), rows)


class InterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["MOVIES_DEMO"] = "1"
        import repository
        repository.DEMO = True

    def app(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20).run()
        self.assertEqual(len(app.exception), 0)
        return app

    def test_search_director_checkbox_and_no_results(self):
        app = self.app()
        self.assertEqual(app.metric[0].value, "20")
        app.checkbox(key="show_all").uncheck().run()
        self.assertEqual(len(app.dataframe), 0)
        app.text_input(key="title_query").set_value("inTER").run()
        app.button(key="search").click().run()
        self.assertEqual(app.dataframe[-1].value['name'].tolist(), ["Interstellar"])
        app.selectbox(key="director").select("Christopher Nolan").run()
        app.button(key="filter_director").click().run()
        self.assertEqual(len(app.dataframe[-1].value), 4)
        app.text_input(key="title_query").set_value("NO_EXISTE_123").run()
        app.button(key="search").click().run()
        self.assertTrue(any("Total de filmes encontrados: 0" in x.value for x in app.success))
        self.assertEqual(len(app.exception), 0)

    def test_movie_form_refreshes_catalog_and_directors(self):
        app = self.app()
        for key, value in [("new_name", "Mi película"), ("new_genre", "Drama"),
                           ("new_director", "Directora de prueba"), ("new_company", "Estudio de prueba")]:
            app.text_input(key=key).set_value(value)
        app.button(key="FormSubmitter:movie_form-Guardar película").click().run()
        self.assertEqual(app.metric[0].value, "21")
        self.assertIn("Directora de prueba", app.selectbox(key="director").options)
        self.assertEqual(len(app.exception), 0)

    def test_guestbook_empty_invalid_and_successful_submit(self):
        app = self.app()
        app.button(key="view_guests").click().run()
        self.assertTrue(any("Todavía no hay" in x.value for x in app.info))
        app.text_input(key="guest_email").set_value("incorrecto")
        app.text_area(key="guest_comment").set_value("Hola")
        app.button(key="FormSubmitter:guest_form-Registrar comentario").click().run()
        self.assertTrue(any("correo electrónico válido" in x.value for x in app.warning))
        app.text_input(key="guest_email").set_value("visitante@example.com")
        app.text_area(key="guest_comment").set_value("Me gustó el catálogo.")
        app.button(key="FormSubmitter:guest_form-Registrar comentario").click().run()
        self.assertEqual(app.dataframe[-1].value.iloc[0]['comment'], "Me gustó el catálogo.")
        self.assertEqual(len(app.exception), 0)

    def test_cloud_failure_is_visible_and_not_replaced_by_demo(self):
        import repository
        with patch.object(repository, "DEMO", False), patch.object(repository, "cloud_movies", side_effect=RuntimeError):
            app = self.app()
            self.assertEqual(app.metric[0].value, "0")
            self.assertTrue(any("No se pudo leer Firestore" in x.value for x in app.error))
            self.assertFalse(any("Modo demostración" in x.value for x in app.warning))
            self.assertEqual(len(app.exception), 0)


if __name__ == "__main__":
    unittest.main()
