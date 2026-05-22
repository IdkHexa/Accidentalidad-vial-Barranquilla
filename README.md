# Proyecto Accidentalidad Barranquilla (Módulos 1 al 4)

Este proyecto descarga, limpia, geocodifica y almacena datos de accidentes de
tránsito en Barranquilla desde el portal de Datos Abiertos de Colombia.

## ¿Qué hace el programa?
1. **Baja los datos**: Se conecta a la API de Socrata y descarga registros en lotes paginados.
2. **Limpia y normaliza**: Convierte fechas, meses, días y números a un formato uniforme usando Pydantic.
3. **Geocodifica direcciones**: Obtiene coordenadas (latitud/longitud) con Google Maps. Las respuestas se guardan en un caché local para no repetir consultas.
4. **Persiste los datos**: Los registros limpios se guardan en una base de datos (SQLite o PostgreSQL) usando el patrón Repositorio (DAO) para que estén listos para ser consultados por la interfaz web.

## Estructura de carpetas
- `api/` — Cliente HTTP para conectarse a la API de datos abiertos.
- `models/` — Modelos Pydantic (DTO) que definen la estructura de los datos.
- `data/` — Pipeline ETL, parser de direcciones, geocodificador, base de datos y repositorio DAO.
- `controllers/` — Lógica de controladores (próximos módulos).
- `views/` — Interfaz web con plantillas HTML, CSS y JavaScript (próximos módulos).
- `tests/` — 9 archivos de pruebas unitarias, 44 tests cubriendo el 100% de los módulos 1-4.
- `docs/` — Documentación detallada de cada entregable y de la metodología del equipo:
  - [`docs/Entregable1.md`](docs/Entregable1.md) — Módulos 1 y 2: Ingesta, limpieza y geocodificación.
  - [`docs/Entregable2.md`](docs/Entregable2.md) — Módulos 3 y 4: Persistencia y repositorio DAO.
  - [`docs/ENTREGABLES.md`](docs/ENTREGABLES.md) — Plan general de entregables y delimitación técnica.
  - [`docs/METODOLOGIA.md`](docs/METODOLOGIA.md) — Roles del equipo y acuerdos de colaboración.
  - [`docs/Guion_Sustentacion_Modulos_1_4.md`](docs/Guion_Sustentacion_Modulos_1_4.md) — Guión de presentación para sustentación.
- `config.py` — Configuración global (URL de la API, llave de Google Maps y conexión a base de datos).
- `docker-compose.yml` — Orquestación de PostgreSQL en contenedor Docker (puerto 8448).
- `main.py` — Punto de entrada que ejecuta el pipeline completo.
- `seed_geocache.py` — Precarga masiva del geocaché (ejecutar una vez antes del ETL completo).

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

4. **Ejecutar el programa**:
   ```bash
   python main.py
   ```

## Documentación de entregables

Cada fase del proyecto tiene su documento técnico en la carpeta [`docs/`](docs/):

| Documento | Contenido |
|-----------|-----------|
| [`docs/Entregable1.md`](docs/Entregable1.md) | Módulos 1 y 2: Ingesta, limpieza y geocodificación. |
| [`docs/Entregable2.md`](docs/Entregable2.md) | Módulos 3 y 4: Persistencia, repositorio DAO y migración a PostgreSQL. |
| [`docs/ENTREGABLES.md`](docs/ENTREGABLES.md) | Plan general de entregables y delimitación técnica. |
| [`docs/METODOLOGIA.md`](docs/METODOLOGIA.md) | Roles del equipo y acuerdos de colaboración. |

## Precarga del geocaché (antes del primer ETL completo)

Para evitar llamadas duplicadas a Google Maps, se precargan todas las coordenadas:

```bash
# Modo simulación (sin gastar créditos de Google)
python seed_geocache.py --dry-run

# Ejecución real (geocodifica ~26k direcciones, ~1-2 horas)
python seed_geocache.py
```

Después de la precarga, cambiar `main.py` línea 31 de `cantidad = 500` a `cantidad = 28328`.

## Pruebas

```bash
# Ejecutar todas las pruebas (44 tests en 9 archivos)
python -m unittest discover tests/ -v

# Ejecutar un archivo específico
python -m unittest tests.test_storage
```

## Notas académicas
- **Pydantic v2** valida y normaliza los datos automáticamente (tipos, fechas, meses, direcciones).
- **Asyncio** permite que la descarga de datos no bloquee el programa mientras espera la respuesta de internet.
- **SQLAlchemy + PostgreSQL (Docker) / SQLite** gestionan la persistencia con mapeo objeto-relacional (ORM).
- **Patrón Repositorio (DAO)** aísla la lógica de base de datos para que el resto del código no dependa del motor subyacente.
- **Docker Compose** orquesta PostgreSQL 16 Alpine; el puerto 8448 evita conflictos con instancias existentes de PostgreSQL en el host.
- **Geocaché persistente** (`data/geocache.json`) almacena coordenadas para no repetir llamadas a Google Maps.
