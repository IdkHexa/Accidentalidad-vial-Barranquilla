# Documentación Técnica: Controladores y Lógica de Negocio
**Proyecto:** Análisis de Accidentalidad Vial en Barranquilla
**Responsable:** Juan David Medina
**Módulos:** 5 y 6

## 1. Introducción

Este documento describe la implementación de la capa de controladores del
proyecto, que conecta la base de datos con la interfaz de usuario mediante
endpoints REST construidos con FastAPI.  Los controladores son el puente
entre los datos almacenados (capa de persistencia de Jofier) y las vistas
HTML que consume el usuario final.

El módulo 5 corresponde a la **interfaz de usuario** (endpoints que sirven
páginas HTML y JSON), y el módulo 6 al **análisis de datos** (endpoints que
agregan y transforman datos crudos en estadísticas útiles para la
visualización).

## 2. Arquitectura del Controlador

### Framework: FastAPI

Se eligió FastAPI como framework HTTP por las siguientes razones:

- **Asincronía nativa**: los endpoints pueden usar `async/await`, lo que
  permite servir múltiples peticiones concurrentes sin bloquear el hilo.
- **Documentación automática**: FastAPI genera una interfaz Swagger UI en
  `/docs` y ReDoc en `/redoc` sin configuración adicional.
- **Validación de parámetros**: los parámetros de ruta, query y formularios
  se validan automáticamente, retornando errores 422 descriptivos.
- **Integración con Jinja2**: el motor de plantillas `Jinja2Templates` se
  integra directamente con `TemplateResponse` para servir HTML.

### Estructura del Controlador (`controllers/main_controller.py`)

El archivo se organiza en cuatro secciones:

| Sección | Propósito |
|---|---|
| Configuración | Instancia de `FastAPI`, montaje de estáticos y plantillas |
| Helper | Función `_session()` para obtener sesiones de SQLAlchemy |
| Páginas HTML | Endpoints `GET` que retornan plantillas Jinja2 |
| API JSON | Endpoints `GET/POST/PUT/DELETE` que retornan datos en JSON |

### Configuración de Static y Templates

```python
app.mount("/static", StaticFiles(directory=os.path.join(ROOT, "views", "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(ROOT, "views", "templates"))
```

Los archivos estáticos (CSS, JS, imágenes) se sirven desde `views/static/`
y las plantillas HTML desde `views/templates/`.  Esto mantiene la convención
de Django/FastAPI donde los templates viven junto a las vistas.

## 3. Endpoints de Páginas HTML (Módulo 5)

Cuatro rutas sirven páginas HTML completas usando el motor de plantillas Jinja2:

| Ruta | Plantilla | Descripción |
|---|---|---|
| `GET /` | `index.html` | Página de inicio con resumen del proyecto y accesos rápidos |
| `GET /dashboard` | `dashboard.html` | Panel de estadísticas con KPIs y gráficos interactivos |
| `GET /mapa` | `mapa.html` | Mapa de calor geoespacial con Leaflet |
| `GET /registro` | `registro.html` | Formulario para registrar nuevos accidentes manualmente |

Cada plantilla extiende `base.html`, que define el layout común: sidebar
de navegación, topbar con indicador de estado, y bloques de contenido
y scripts que cada página personaliza.

## 4. Operaciones CRUD (Módulo 5)

El controlador expone las cuatro operaciones CRUD completas sobre la
entidad Accidente, accesibles desde la API JSON:

### 4.1 Create — `POST /api/accidentes`

Recibe los datos del formulario HTML como `Form(...)` y crea un nuevo
registro en la base de datos:

```python
@app.post("/api/accidentes")
async def crear_accidente(
    fecha_accidente: str = Form(...),
    hora_accidente: str = Form(...),
    gravedad_accidente: str = Form(...),
    ...
):
```

Retorna `{"ok": true, "id": <nuevo_id>}` si la inserción fue exitosa.

### 4.2 Read — `GET /api/accidentes`

Lista los accidentes almacenados con filtros opcionales por gravedad y año:

```python
@app.get("/api/accidentes")
async def listar_accidentes(limit: int = 50, gravedad: str = None, año: int = None):
```

Retorna un array JSON con los campos más relevantes de cada accidente.
El orden es descendente por ID (los más recientes primero).

### 4.3 Update — `PUT /api/accidentes/{id}`

Permite editar un accidente existente.  Recibe un JSON con los campos
a modificar (parcial o completo):

```python
@app.put("/api/accidentes/{accidente_id}")
async def actualizar_accidente(accidente_id: int, request: Request):
```

Internamente usa `setattr()` para actualizar solo los campos presentes
en el JSON, lo que permite actualizaciones parciales sin necesidad de
enviar todos los campos.  Retorna 404 si el ID no existe.

### 4.4 Delete — `DELETE /api/accidentes/{id}`

Elimina un accidente por ID:

```python
@app.delete("/api/accidentes/{accidente_id}")
async def eliminar_accidente(accidente_id: int):
```

Retorna `{"ok": true, "id": <id_eliminado>}` o 404 si no existe.
La eliminación es física (no soft-delete).

## 5. Endpoints de Estadísticas (Módulo 6)

El módulo 6 transforma los datos crudos de la base de datos en
agregaciones útiles para los gráficos del dashboard.  Cada endpoint
usa consultas SQL con `GROUP BY` y funciones de agregación de
SQLAlchemy (`func.sum`, `func.count`) para evitar traer todos los
registros a memoria.

### 5.1 Resumen general — `GET /api/stats/resumen`

Retorna los KPIs principales para las tarjetas del dashboard:

```json
{
  "total": 28328,
  "muertos": 1234,
  "heridos": 12345,
  "año_inicio": 2018,
  "año_fin": 2024
}
```

### 5.2 Por año — `GET /api/stats/por_año`

Agrupa accidentes por año con conteo de muertos y heridos.  Usado
por el gráfico de línea + barras del dashboard.

### 5.3 Por gravedad — `GET /api/stats/por_gravedad`

Distribución de accidentes por categoría de gravedad (Con muertos,
Con heridos, Solo daños).  Usado por el gráfico de dona (pie chart).

### 5.4 Por clase — `GET /api/stats/por_clase`

Top 10 de clases de accidente (Choque, Atropello, Volcamiento, etc.).
Usado por el gráfico de barras horizontales.

### 5.5 Por mes — `GET /api/stats/por_mes`

Accidentes agrupados por mes del año en orden cronológico fijo
(ENERO a DICIEMBRE).  Los meses que no tienen datos se rellenan con 0
para que el gráfico no salte meses.

### 5.6 Por día — `GET /api/stats/por_dia`

Accidentes por día de la semana.  Incluye normalización de abreviaturas
(LUN → LUNES, SÁB → SABADO) usando un diccionario de mapeo para
garantizar que todas las variantes apunten al mismo día.

### 5.7 Por hora — `GET /api/stats/por_hora`

Distribución de accidentes por hora del día (0–23).  Parsea formatos
mixtos (12h AM/PM y 24h) y los normaliza a un bucket por hora.

### 5.8 Clusters — `GET /api/stats/clusters`

Ejecuta el pipeline de clustering DBSCAN (del módulo analytics) y
retorna los centros de cada cluster con su severidad.  Este endpoint
conecta el análisis geoespacial con la interfaz web.

## 6. Manejo de Sesiones de Base de Datos

Cada endpoint sigue el patrón try/finally para garantizar que la sesión
de SQLAlchemy se cierre siempre, incluso si ocurre una excepción:

```python
db = _session()
try:
    # ... operaciones ...
finally:
    db.close()
```

Esto evita fugas de conexión que podrían agotar el pool de SQLite o
PostgreSQL bajo carga.

## 7. Integración con el Módulo Analytics

El endpoint `/api/stats/clusters` importa directamente
`obtener_clusters_pipeline()` del módulo analytics.  Esto conecta
el clustering DBSCAN con la interfaz web: el frontend puede solicitar
las zonas calientes y renderizarlas como círculos en el mapa de Leaflet.

```python
from analytics.clustering import obtener_clusters_pipeline
```

El flujo es:

```
Frontend → GET /api/stats/clusters → Controller → Repositorio → DB
                                                        ↓
                                                  DBSCAN puro
                                                        ↓
                                                  JSON con centros
```

## 8. Dificultades Encontradas

### 8.1. FastAPI no detecta plantillas fuera del directorio del controlador

**Problema:** `Jinja2Templates` busca las plantillas relativo al directorio
donde se define el `app`.  Como el controlador vive en `controllers/` pero
las plantillas están en `views/templates/`, las rutas relativas no funcionaban.

**Solución:** Calcular la ruta absoluta usando `os.path.dirname()` dos veces
(una para subir de `controllers/` a la raíz del proyecto) y construir la
ruta completa: `os.path.join(ROOT, "views", "templates")`.

### 8.2. Form data vs JSON en el endpoint POST

**Problema:** El formulario HTML envía datos como `multipart/form-data`,
pero FastAPI esperaba JSON por defecto.  Los campos llegaban vacíos al
controlador.

**Solución:** Usar `Form(...)` de FastAPI como tipo de parámetro en lugar
de definir un modelo Pydantic.  Esto le indica a FastAPI que extraiga los
valores del formulario en lugar del body JSON.  Se agregó `python-multipart`
a `requirements.txt` como dependencia requerida.

### 8.3. PUT parcial: no todos los campos se envían en la edición

**Problema:** Un endpoint PUT que recibe un modelo Pydantic completo exige
que todos los campos estén presentes.  Para la edición parcial desde el
frontend, esto era demasiado restrictivo.

**Solución:** Usar `request.json()` directamente y aplicar `setattr()`
solo para los campos presentes en el diccionario.  Esto permite
actualizaciones parciales sin necesidad de enviar el objeto completo.

### 8.4. Normalización de días abreviados en la base de datos

**Problema:** Algunos registros almacenados tienen el día en formato
abreviado ("LUN", "MAR") mientras que el endpoint espera nombres completos
("LUNES", "MARTES").  Esto causaba que el gráfico por día mostrara barras
duplicadas.

**Solución:** Crear un diccionario `ABREV_A_FULL` en el endpoint
`stats_por_dia()` que mapea todas las abreviaturas conocidas a su nombre
completo, y acumular los conteos con `defaultdict(int)`.

## 9. Pruebas

El controlador se prueba indirectamente a través de los tests de storage
y database, ya que los endpoints son delgados (solo llaman al repositorio).
La verificación funcional se realiza manualmente arrancando el servidor:

```bash
uvicorn controllers.main_controller:app --reload
```

Y accediendo a:
- http://127.0.0.1:8000/ — Página de inicio
- http://127.0.0.1:8000/dashboard — Dashboard con gráficos
- http://127.0.0.1:8000/mapa — Mapa de calor
- http://127.0.0.1:8000/registro — Formulario CRUD
- http://127.0.0.1:8000/docs — Documentación Swagger automática

## 10. Resumen de Endpoints

| Método | Ruta | Tipo | Descripción |
|---|---|---|---|
| GET | `/` | HTML | Página de inicio |
| GET | `/dashboard` | HTML | Panel de estadísticas |
| GET | `/mapa` | HTML | Mapa de calor |
| GET | `/registro` | HTML | Formulario de registro |
| GET | `/api/stats/resumen` | JSON | KPIs principales |
| GET | `/api/stats/por_año` | JSON | Accidentes por año |
| GET | `/api/stats/por_gravedad` | JSON | Distribución por gravedad |
| GET | `/api/stats/por_clase` | JSON | Top 10 clases |
| GET | `/api/stats/por_mes` | JSON | Accidentes por mes |
| GET | `/api/stats/por_dia` | JSON | Accidentes por día |
| GET | `/api/stats/por_hora` | JSON | Accidentes por hora |
| GET | `/api/stats/clusters` | JSON | Zonas calientes DBSCAN |
| GET | `/api/mapa/puntos` | JSON | Puntos geolocalizados |
| GET | `/api/accidentes` | JSON | Listar accidentes (CRUD Read) |
| POST | `/api/accidentes` | JSON | Crear accidente (CRUD Create) |
| PUT | `/api/accidentes/{id}` | JSON | Editar accidente (CRUD Update) |
| DELETE | `/api/accidentes/{id}` | JSON | Eliminar accidente (CRUD Delete) |
