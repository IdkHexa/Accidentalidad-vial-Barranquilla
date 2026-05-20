# Documentación Técnica: Persistencia y Repositorio DAO
**Proyecto:** Análisis de Accidentalidad Vial en Barranquilla
**Responsable:** Jofier Salas
**Módulos:** 3 y 4

## 1. Introducción

Este documento describe la implementación de la capa de persistencia del
proyecto, que toma los datos ya limpios y geocodificados (resultado de los
módulos 1 y 2) y los almacena en una base de datos relacional para que
puedan ser consultados posteriormente por la interfaz web.

El diseño se basa en dos pilares:
- **ORM (SQLAlchemy)**: Permite trabajar con los registros como objetos de
  Python en lugar de escribir sentencias SQL manualmente.
- **Patrón Repositorio (DAO)**: Encapsula la lógica de acceso a datos en una
  clase dedicada, aislando al resto del sistema de los detalles del motor de
  base de datos.

## 2. Configuración del Motor de Base de Datos

### Motor Dual: SQLite o PostgreSQL (`data/database.py`)

El proyecto soporta dos motores de base de datos intercambiables gracias a
la abstracción de SQLAlchemy:

| Motor | Cuándo usarlo |
|-------|--------------|
| **SQLite** | Desarrollo rápido, sin dependencias externas, portátil |
| **PostgreSQL** | Entorno de producción o cuando se requiere un gestor servido |

La selección se define en `config.py` mediante la variable de entorno
`DATABASE_URL`:

```python
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///accidentalidad.db")
```

Si `DATABASE_URL` está definida en `.env`, se usa ese motor; si no, cae
automáticamente a SQLite sin necesidad de cambiar código.

La configuración sigue el patrón estándar de SQLAlchemy:

| Componente | Propósito |
|---|---|
| `engine` | Conexión a la base de datos (`DATABASE_URL` desde configuración) |
| `SessionLocal` | Fábrica de sesiones: cada operación abre y cierra su propia sesión |
| `Base` | Clase declarativa base de la que heredan todos los modelos ORM |
| `init_db()` | Crea las tablas si no existen (idempotente, seguro de llamar múltiples veces) |

### Modelo ORM: `AccidenteDB`

La clase `AccidenteDB` mapea la tabla `accidentes` en la base de datos.
Cada columna corresponde a un campo del DTO de Pydantic (`AccidenteDTO`),
pero con los nombres en snake_case y sin tildes (por ejemplo, `AÑO_ACCIDENTE`
del DTO se almacena como `a_o_accidente` en la tabla).

**Columna adicional**: `id` (clave primaria autoincremental). Este campo no
viene del dataset original; lo genera SQLite automáticamente para identificar
cada registro de forma única.

### Puente DTO ↔ ORM: `desde_dto()`

El método de clase `desde_dto(dto)` convierte una instancia de `AccidenteDTO`
(objeto de memoria validado por Pydantic) en una instancia de `AccidenteDB`
(lista para insertar en la base de datos). Este método es el único punto del
sistema donde se tocan ambos mundos, lo que facilita el mantenimiento: si
cambia la estructura del DTO, solo hay que ajustar este método.

### Nota sobre tamaños de columna

Al migrar de SQLite a PostgreSQL se descubrió que `String(20)` para
`fecha_accidente` era insuficiente: el formato ISO completo
(`2018-01-01T00:00:00.000`) ocupa 23 caracteres. En SQLite no hay problema
porque ignora el límite, pero PostgreSQL lo enforce. Se actualizó a
`String(50)` para evitar truncamiento.

## 3. Repositorio DAO (`data/storage.py`)

### Justificación del Patrón

En lugar de dispersar consultas SQL por todo el código, se centralizan en
una única clase: `AccidenteRepository`. Las ventajas de este enfoque son:

- **Desacoplamiento**: El ETL y los futuros controladores nunca importan
  `session` ni `AccidenteDB` directamente; solo hablan con el repositorio.
- **Migrabilidad**: El cambio de SQLite a PostgreSQL (o viceversa) solo
  requiere modificar `DATABASE_URL` en `.env`; el repositorio permanece
  igual porque usa la API genérica de SQLAlchemy.
- **Testeabilidad**: Se puede probar el repositorio con una base de datos
  en memoria sin tocar el archivo real.

### Operaciones Implementadas

| Método | Descripción |
|---|---|
| `insertar_lote(dtos)` | Convierte una lista de DTOs a objetos ORM y los inserta en una sola transacción con `add_all()` |
| `contar()` | Retorna el total de registros almacenados |
| `obtener_todos(limit)` | Retorna los registros más recientes (orden descendente por ID) |
| `obtener_por_gravedad(gravedad)` | Filtra accidentes por gravedad (ej: "Fatal", "Grave", "Leve") |
| `obtener_por_año(año)` | Filtra accidentes por año (ej: 2018, 2019) |

Los filtros por gravedad y año están diseñados para alimentar los futuros
gráficos interactivos de la interfaz web (Apache ECharts).

## 4. Migración a PostgreSQL con Docker

Como mejora posterior a la implementación inicial, se migró la base de datos
de SQLite a PostgreSQL, manteniendo la capacidad de volver a SQLite mediante
configuración.

### Infraestructura con Docker Compose

Se creó `docker-compose.yml` en la raíz del proyecto para levantar un
contenedor de PostgreSQL 16 Alpine:

```yaml
services:
  db:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRE_USER}
      POSTGRES_PASSWORD: ${POSTGRE_PASSWORD}
      POSTGRES_DB: ${POSTGRE_DB}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

Las credenciales se definen en `.env` y son leídas automáticamente por Docker
Compose. El volumen `pgdata` garantiza que los datos persistan entre reinicios
del contenedor.

### Conexión desde la Aplicación

`config.py` expone `DATABASE_URL` que se construye desde la variable de entorno
del mismo nombre. Si no está definida, cae a SQLite automáticamente:

```python
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///accidentalidad.db")
```

Ejemplo de configuración en `.env` para usar PostgreSQL:

```env
DATABASE_URL=postgresql+psycopg2://usuario:password@127.0.0.1:5432/nombre_db
```

### Driver PostgreSQL

Se agregó `psycopg2-binary` a `requirements.txt` como driver de conexión entre
SQLAlchemy y PostgreSQL.

### Nuevo Flujo de Trabajo

```bash
# 1. Iniciar PostgreSQL
docker compose up -d

# 2. Ejecutar el ETL (se conecta automáticamente a PostgreSQL)
python main.py

# 3. Para detener PostgreSQL
docker compose down
```

### Cómo Volver a SQLite

Simplemente comentar o eliminar `DATABASE_URL` del archivo `.env`. La aplicación
cae automáticamente a `sqlite:///accidentalidad.db`.

## 5. Integración con el Pipeline ETL

El archivo `data/etl.py` fue modificado para incorporar un tercer paso al
final del proceso:

```
Paso 1: Extracción (API Socrata)
  → Paso 2: Transformación + Geocodificación (Pydantic + Google Maps)
    → Paso 3: Carga en Base de Datos (Repository DAO)
```

La función `ejecutar_etl()` ahora recibe un parámetro `guardar_en_bd=True`.
Cuando está activo, al finalizar la transformación se crea una sesión de
SQLAlchemy, se instancia el repositorio y se insertan todos los registros
válidos. La sesión se cierra en un bloque `finally` para garantizar que
los recursos se liberen incluso si ocurre un error.

### Manejo de Errores en Inserción

Si la inserción falla, se ejecuta `session.rollback()` para dejar la base
de datos en un estado consistente (sin datos a medio insertar). El error
se imprime en consola pero no interrumpe el flujo: los registros procesados
se siguen retornando al llamador.

### Trazabilidad de Errores de Validación

Se reemplazó el `continue` silencioso del bloque `except ValidationError`
por un sistema de contadores que registra qué campos causaron el rechazo
de cada registro. Al finalizar el ETL, si hubo descartes, se muestra un
resumen agrupado por campo:

```
Registros descartados por validación:
 - cant_muertos_en_sitio_accidente: 3 errores
 - fecha_accidente: 2 errores
```

Esto permite rastrear problemas de calidad del dataset sin interrumpir
el proceso de carga. Los errores de todos los campos de un mismo registro
se contabilizan de forma independiente.

## 6. Degradación Graceful del Geocodificador

Como mejora de robustez, se modificó `data/geocoding.py` para que no falle
si la variable de entorno `GOOGLE_MAPS_KEY` no está configurada. En lugar
de crear un cliente de Google Maps con `key=None` (que lanza excepción),
ahora se asigna `self.gmaps = None` y el método `obtener_coordenadas()`
retorna `None` inmediatamente si no hay cliente disponible. El ETL ya
manejaba coordenadas nulas, por lo que esta mejora no requirió cambios
adicionales en el pipeline.

## 7. Pruebas del Repositorio

Se creó el archivo `tests/test_storage.py` con 5 pruebas que validan:

1. **Inserción y conteo**: Insertar un registro y verificar que `contar()` devuelva 1.
2. **Inserción por lotes**: Insertar 3 registros y verificar el conteo total.
3. **Filtro por año**: Insertar registros de distintos años y verificar que `obtener_por_año()` filtre correctamente.
4. **Filtro por gravedad**: Insertar registros con distintas gravedades y verificar el filtro.
5. **Orden descendente**: Verificar que `obtener_todos()` retorna los registros del más reciente al más antiguo.

Las pruebas usan una base de datos SQLite en memoria (`:memory:`) para no
contaminar los datos reales. Cada test crea y destruye su propio entorno
en `setUp()` y `tearDown()`.

## 8. Resultados

En la ejecución de prueba, el sistema procesó **500 registros** desde la
API, los transformó, geocodificó y almacenó correctamente tanto en SQLite
como en PostgreSQL (según configuración de `DATABASE_URL`). Las 5 pruebas
del repositorio pasaron sin errores, validando que las operaciones CRUD
funcionan independientemente del motor subyacente.

| Métrica | Resultado |
|---|---|
| Registros extraídos | 500 |
| Registros insertados en BD | 500 |
| Coordenadas geocodificadas | 500 (100%) |
| Registros descartados | 0 |
| Tests del repositorio | 5/5 OK |
| Tests totales (12) | 12/12 OK |
