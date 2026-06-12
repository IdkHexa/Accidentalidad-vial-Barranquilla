# Proyecto Accidentalidad Vial en Barranquilla

Este proyecto descarga, limpia, geocodifica, almacena y analiza datos de
accidentes de tránsito en Barranquilla desde el portal de Datos Abiertos
de Colombia.

## ¿Qué hace el programa?

1. **Baja los datos**: Se conecta a la API de Socrata y descarga registros en lotes paginados.
2. **Limpia y normaliza**: Convierte fechas, meses, días y números a un formato uniforme usando Pydantic.
3. **Geocodifica direcciones**: Obtiene coordenadas (latitud/longitud) con Google Maps. Las respuestas se guardan en un caché local para no repetir consultas.
4. **Persiste los datos**: Los registros limpios se guardan en una base de datos (SQLite o PostgreSQL) usando el patrón Repositorio (DAO).
5. **Analiza zonas calientes**: Ejecuta DBSCAN ponderado por severidad para identificar clusters de accidentalidad con alta densidad de víctimas.

## Estructura de carpetas

- `api/` — Cliente HTTP para conectarse a la API de datos abiertos.
- `models/` — Modelos Pydantic (DTO) que definen la estructura de los datos.
- `data/` — Pipeline ETL, parser de direcciones, geocodificador, base de datos y repositorio DAO.
- `analytics/` — Clustering geoespacial con DBSCAN (función pura + pipeline orquestador).
- `controllers/` — Lógica de controladores (próximos módulos, Juan).
- `views/` — Interfaz web con plantillas HTML, CSS y JavaScript (próximos módulos, Juan).
- `tests/` — Pruebas unitarias con unittest (18 tests de clustering + tests de módulos 1-4).
- `docs/` — Documentación detallada de cada entregable.
- `scratch/` — Archivos temporales no versionados (excluidos de git).

## Módulo de Analytics: Clustering

El clustering identifica zonas críticas de accidentalidad usando DBSCAN con las siguientes mejoras sobre el enfoque básico:

- **Ponderación por severidad**: Cada accidente tiene un peso basado en víctimas (heridos ×1.5, muertos ×3.0), no solo conteo de filas.
- **Bounding box geográfico**: Excluye coordenadas corruptas o fuera de Barranquilla antes del cómputo.
- **Conversión explícita**: `kilometros_a_radianes()` elimina números mágicos en el radio de vecindad.
- **Optimización**: Usa `algorithm="ball_tree"` y `n_jobs=-1` para cálculo paralelo.
- **Separación de responsabilidades**: La función de clustering es pura (no toca la BD). El orquestador conecta el repositorio con el análisis.

```bash
# Ejecutar el clustering directamente
python -m analytics.clustering

# Ejecutar solo los tests de clustering
python -m unittest tests.test_clustering -v
```

## Cómo usarlo

1. **Instalar las dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurar la llave de Google Maps** (opcional para geocodificación):
   Crear un archivo `.env` con:
   ```
   GOOGLE_MAPS_KEY=tu_llave_aqui
   ```

3. **(Opcional) Configurar PostgreSQL** (si no se define, se usa SQLite automáticamente):
   ```bash
   docker compose up -d
   ```

4. **Ejecutar el pipeline completo** (API → ETL → SQLite):
   ```bash
   python main.py
   ```

5. **Ejecutar el clustering**:
   ```bash
   python -m analytics.clustering
   ```

## Pruebas

```bash
# Ejecutar todas las pruebas
python -m unittest discover tests/ -v

# Ejecutar tests de clustering específicamente
python -m unittest tests.test_clustering -v

# Ejecutar tests de storage
python -m unittest tests.test_storage -v
```

## Documentación

| Documento | Contenido |
|-----------|-----------|
| [`docs/Entregable1.md`](docs/Entregable1.md) | Módulos 1 y 2: Ingesta, limpieza y geocodificación. |
| [`docs/Entregable2.md`](docs/Entregable2.md) | Módulos 3 y 4: Persistencia, repositorio DAO y migración a PostgreSQL. |
| [`docs/ENTREGABLES.md`](docs/ENTREGABLES.md) | Plan general de entregables y delimitación técnica. |
| [`docs/METODOLOGIA.md`](docs/METODOLOGIA.md) | Roles del equipo y acuerdos de colaboración. |

## Notas académicas

- **Pydantic v2** valida y normaliza los datos automáticamente (tipos, fechas, meses, direcciones).
- **Asyncio** permite que la descarga de datos no bloquee el programa mientras espera la respuesta de internet.
- **SQLAlchemy + PostgreSQL (Docker) / SQLite** gestionan la persistencia con mapeo objeto-relacional (ORM).
- **Patrón Repositorio (DAO)** aísla la lógica de base de datos para que el resto del código no dependa del motor subyacente.
- **DBSCAN con haversine** detecta clusters geográficos usando la distancia real sobre la esfera terrestre, no la distancia euclidiana.
- **Docker Compose** orquesta PostgreSQL 16 Alpine; el puerto 8448 evita conflictos con instancias existentes de PostgreSQL en el host.
