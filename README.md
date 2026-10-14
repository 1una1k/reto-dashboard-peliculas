# CineScope: dashboard de películas

Proyecto académico en Python y Streamlit. Consulta y registra películas en la colección `movies` de Firestore, y administra un libro de visitas en la tabla `people` de la base PostgreSQL `guests`.

**Estado del proyecto:** código publicado en https://github.com/1una1k/reto-dashboard-peliculas. Firestore contiene 20 películas y la tabla `guests.public.people` está creada en Aiven. El despliegue en Streamlit está iniciado, pendiente de verificar su arranque y las conexiones desde la aplicación. Las 13 pruebas locales pasan también en Python 3.14.8 con pandas 2.3.3. El modo de demostración no sustituye la conexión a las bases de datos ni acredita el despliegue.

## Inicio rápido en Visual Studio Code (Windows)

1. Extrae el ZIP y abre la carpeta `reto_dashboard` desde **Archivo > Abrir carpeta** en VS Code.
2. Usa Python **3.12** y abre **Terminal > Nueva terminal**. Ejecuta desde la carpeta que contiene `app.py`:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

3. Para probar la interfaz sin claves, ejecuta:

```powershell
$env:MOVIES_DEMO = "1"
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Abre la dirección local que aparece en la terminal. La demostración tiene 20 registros y conserva las altas solo dentro de la sesión. Detén el servidor con **Ctrl+C**. Antes de conectarte a las bases reales, desactiva la demostración:

```powershell
Remove-Item Env:MOVIES_DEMO -ErrorAction SilentlyContinue
```

En macOS/Linux: `python3.12 -m venv .venv`, `source .venv/bin/activate`, `python -m pip install -r requirements.txt` y `MOVIES_DEMO=1 python -m streamlit run app.py`. Para usar las bases reales, ejecuta sin el prefijo `MOVIES_DEMO=1`.

## 1. Firestore en Firebase

1. Abre [Firebase Console](https://console.firebase.google.com/) y crea o selecciona un proyecto dedicado al reto.
2. En Firestore crea una base **Standard / modo nativo**, identificador **`(default)`**. Elige una región y usa reglas de producción. El cliente de Python usa una cuenta de servicio y permisos IAM; no requiere abrir las reglas al público.
3. En **Configuración del proyecto > Cuentas de servicio** genera la clave privada de la cuenta que usará el proyecto. Necesita permiso de lectura y escritura en Firestore, por ejemplo el rol IAM `Cloud Datastore User`.
4. Conserva el JSON fuera del repositorio. Copia `.streamlit/secrets.example.toml` a `.streamlit/secrets.toml`.
5. Sustituye `project_id`, `client_email`, `private_key` y `token_uri` con los valores del JSON. Mantén los encabezados de la clave privada. Se admiten saltos reales de línea o las secuencias `\n` del JSON.

No es necesario insertar manualmente las 20 películas: `setup_databases.py` crea los documentos de `movies`. Cada uno tiene exactamente `name`, `genre`, `director` y `company`. La carga usa identificadores estables y no duplica ni sobrescribe registros al repetirla.

## 2. PostgreSQL en Aiven

Firestore se crea en Firebase; **Aiven se usa para PostgreSQL**.

1. Entra a [Aiven](https://console.aiven.io/) y crea un servicio PostgreSQL. Revisa el plan y sus condiciones antes de activar cualquier servicio de pago.
2. Espera a que el servicio esté disponible. En **Connect > Databases > Create database**, crea la base **`guests`**. Como alternativa, ejecuta `sql/create_database.sql` conectado a `defaultdb`, fuera de una transacción y solo una vez.
3. Copia el host, el puerto exacto, el usuario y la contraseña del servicio a la sección `[postgres]` de `.streamlit/secrets.toml`. Usa `dbname = "guests"`, no `defaultdb`.
4. Conserva `sslmode = "require"` para cifrar la conexión según la configuración de Aiven. Si quieres verificar también el certificado, descarga el CA público, guárdalo en `certs/ca.pem` y usa `verify-full` con `sslrootcert = "certs/ca.pem"`.

La tabla `people` contiene `email` y `comment`, ambos obligatorios. La aplicación valida los campos e inserta con parámetros SQL; las transacciones se confirman al terminar correctamente.

## 3. Inicializar y ejecutar con datos reales

Con `.streamlit/secrets.toml` configurado y la base `guests` ya creada:

```powershell
.\.venv\Scripts\python.exe setup_databases.py
.\.venv\Scripts\python.exe -m streamlit run app.py
```

El primer comando debe informar al menos **20 películas** en Firestore y que la tabla de PostgreSQL está lista. Si configuras los servicios por separado, puedes usar `--firestore-only` o `--postgres-only`.

La aplicación lee Firestore al arrancar mediante una función que devuelve un dataframe. Conserva la lectura durante 60 segundos; **Actualizar catálogo** fuerza una lectura nueva, y registrar una película invalida la caché inmediatamente. Las listas de directores y los filtros usan ese mismo dataframe. El libro de visitas se consulta de nuevo al visualizarlo.

## 4. Publicar el código en GitHub

Crea un repositorio **público** llamado, por ejemplo, `reto-dashboard-peliculas`. Desde la terminal de VS Code, con Git instalado:

```powershell
git init
git add .
git status
git commit -m "Dashboard de peliculas con Streamlit, Firestore y PostgreSQL"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/reto-dashboard-peliculas.git
git push -u origin main
```

Sustituye `TU_USUARIO` por tu usuario real. Antes del commit, verifica que `.streamlit/secrets.toml` y el JSON de Firebase no aparezcan en `git status`. `.gitignore` ya excluye los nombres habituales; guarda de todos modos la clave JSON fuera de la carpeta. No incluyas el entorno `.venv`.

## 5. Desplegar en Streamlit Community Cloud

1. Entra a [share.streamlit.io](https://share.streamlit.io/) e inicia sesión. Autoriza el acceso al repositorio si se solicita.
2. Selecciona **Create app**, tu repositorio y la rama `main`. El archivo principal es **`app.py`**.
3. En **Advanced settings**, selecciona **Python 3.12** y pega el contenido completo de tu `.streamlit/secrets.toml` ya configurado en **Secrets**. No configures `MOVIES_DEMO`.
4. Publica y espera a que termine la instalación. Comprueba el catálogo y guarda un comentario de prueba para confirmar las dos conexiones.
5. Copia la URL real del repositorio y la URL pública generada por Streamlit en `ENTREGA.txt`.

Aunque el portal de despliegue es `share.streamlit.io`, la dirección pública de la aplicación tendrá un subdominio **`streamlit.app`**. Es la URL de la aplicación que debes entregar.

## Comprobar el reto antes de entregarlo

| Criterio | Puntos | Dónde está implementado | Evidencia que debes verificar en producción |
|---|---:|---|---|
| Lectura completa a dataframe mediante función | 10 | `repository.load_movies`, `database.read_movies` | Catálogo con al menos 20 filas de Firestore |
| Checkbox en sidebar, header y todos los filmes | 10 | `app.py` | Activar y desactivar “Visualizar todos los filmes” |
| Buscar título por “contiene”, sin distinguir mayúsculas | 15 | `catalog.search_title` y botón de búsqueda | Buscar `INTER`, `inter` e `Inter`; encontrar Interstellar |
| Selectbox y función de filtro por director, con total | 15 | `catalog.filter_by_director` | Christopher Nolan devuelve 4 películas del conjunto inicial |
| Formulario para insertar un filme | 20 | `database.insert_movie` | Insertar un filme y confirmarlo también en Firebase |
| Registrar comentarios en PostgreSQL | 10 | `database.insert_guest` | Guardar un correo y comentario; confirmar la fila en Aiven |
| Botón para visualizar comentarios | 10 | `database.read_guests` | Ver el comentario desde otra sesión del navegador |
| Despliegue funcional con ambas bases | 10 | `requirements.txt`, configuración y guía | Abrir la URL pública y repetir las operaciones |
| **Total posible** | **100** | | **La puntuación depende de la evaluación y de la verificación real.** |

No entregues únicamente el ZIP: el formato solicitado exige **las dos URL**. La implementación local no acredita por sí sola la configuración remota ni la persistencia en producción.

## Pruebas locales

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Las pruebas verifican datos iniciales, filtros, entradas inválidas, parámetros SQL, contratos de Firestore y la interfaz con `AppTest`. Las pruebas de interfaz usan datos temporales y las de acceso remoto utilizan dobles de prueba. No verifican credenciales ni conectividad con servicios reales.

## Archivos

```text
app.py                       Interfaz Streamlit
catalog.py                   Dataframe, búsquedas y validaciones
database.py                  Conexiones y operaciones reales
repository.py                Caché, lectura inicial y modo de demostración
setup_databases.py           Carga inicial y creación de people
requirements.txt             Dependencias fijadas
.streamlit/config.toml        Tema y configuración
.streamlit/secrets.example.toml  Plantilla de credenciales, sin claves reales
data/movies.json              20 películas para la práctica
sql/schema.sql               Tabla people
sql/create_database.sql      Creación opcional de guests
tests/test_project.py        Pruebas locales
ENTREGA.txt                  Plantilla para las dos URL
```

## Si algo falla

| Mensaje o síntoma | Qué revisar |
|---|---|
| No se pudo leer Firestore | Clave privada, project_id, permisos de la cuenta y base `(default)` creada |
| Catálogo vacío | Ejecutar `setup_databases.py --firestore-only` con el mismo proyecto |
| Error al registrar o leer comentarios | Host, puerto de Aiven, contraseña, TLS, base `guests` y tabla `people` |
| La tabla people no existe | Ejecutar `setup_databases.py --postgres-only` |
| La clave privada no se interpreta | Mantener BEGIN/END PRIVATE KEY y los saltos de línea |
| Sigue apareciendo modo demostración | Desactivar `MOVIES_DEMO` y reiniciar el servidor |
| El cambio no aparece | Pulsar Actualizar catálogo; para claves nuevas, reiniciar la app |

## Datos y referencias

Los registros de `movies.json` son ejemplos preparados para practicar. `company` representa una compañía asociada al filme (productora o distribuidora). No es una descarga de la base oficial de Netflix ni afirma disponibilidad actual en esa plataforma.

Documentación consultada el 14 de octubre de 2026:

- [Inicio de Firestore](https://firebase.google.com/docs/firestore/quickstart).
- [Crear bases PostgreSQL en Aiven](https://aiven.io/docs/products/postgresql/howto/create-database).
- [Conexiones TLS de Aiven](https://aiven.io/docs/products/postgresql/howto/list-code-samples).
- [Despliegue de Streamlit](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).
- [Secrets en Streamlit Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management).

La correspondencia de criterios se tomó de la rúbrica adjunta `DS25_DWPIA_C5_SC3.pdf`.
