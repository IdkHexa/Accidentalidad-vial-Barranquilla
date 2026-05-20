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
- `tests/` — Pruebas unitarias del parser, geocodificador y repositorio.
- `docs/` — Documentación detallada de cada entregable y de la metodología del equipo:
  - [`docs/Entregable1.md`](docs/Entregable1.md) — Módulos 1 y 2: Ingesta, limpieza y geocodificación.
  - [`docs/Entregable2.md`](docs/Entregable2.md) — Módulos 3 y 4: Persistencia y repositorio DAO.
  - [`docs/ENTREGABLES.md`](docs/ENTREGABLES.md) — Plan general de entregables y delimitación técnica.
  - [`docs/METODOLOGIA.md`](docs/METODOLOGIA.md) — Roles del equipo y acuerdos de colaboración.
- `config.py` — Configuración global (URL de la API, llave de Google Maps y conexión a base de datos).
- `docker-compose.yml` — Orquestación de PostgreSQL en contenedor Docker.
- `main.py` — Punto de entrada que ejecuta el pipeline completo.

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

## Pruebas

```bash
# Ejecutar todas las pruebas
python -m unittest discover tests/

# Ejecutar un archivo específico
python -m unittest tests.test_storage
```

## Notas académicas
- **Pydantic** valida y normaliza los datos automáticamente (tipos, fechas, meses, direcciones).
- **Asyncio** permite que la descarga de datos no bloquee el programa mientras espera la respuesta de internet.
- **SQLAlchemy + PostgreSQL / SQLite** gestionan la persistencia con mapeo objeto-relacional (ORM).
- **Patrón Repositorio (DAO)** aísla la lógica de base de datos para que el resto del código no dependa del motor subyacente.
- **Docker Compose** orquesta el contenedor de PostgreSQL para entornos que requieran un gestor servido.
