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

### Motor SQLite y Fábrica de Sesiones (`data/database.py`)

Se eligió **SQLite** como motor de base de datos porque:
- No requiere instalar ni configurar un servidor externo.
- El archivo `accidentalidad.db` es autocontenido y portátil.
- Es suficiente para el volumen de datos del proyecto (miles de registros,
  no millones).

La configuración sigue el patrón estándar de SQLAlchemy:

| Componente | Propósito |
|---|---|
| `engine` | Conexión al archivo SQLite (`sqlite:///accidentalidad.db`) |
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
(lista para insertar en SQLite). Este método es el único punto del sistema
donde se tocan ambos mundos, lo que facilita el mantenimiento: si cambia la
estructura del DTO, solo hay que ajustar este método.

## 3. Repositorio DAO (`data/storage.py`)

### Justificación del Patrón

En lugar de dispersar consultas SQL por todo el código, se centralizan en
una única clase: `AccidenteRepository`. Las ventajas de este enfoque son:

- **Desacoplamiento**: El ETL y los futuros controladores nunca importan
  `session` ni `AccidenteDB` directamente; solo hablan con el repositorio.
- **Migrabilidad**: Si en el futuro se cambia SQLite por PostgreSQL, solo
  hay que modificar la configuración del engine; el repositorio permanece
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

## 4. Integración con el Pipeline ETL

El archivo `data/etl.py` fue modificado para incorporar un tercer paso al
final del proceso:

```
Paso 1: Extracción (API Socrata)
  → Paso 2: Transformación + Geocodificación (Pydantic + Google Maps)
    → Paso 3: Carga en Base de Datos (Repository DAO)  ← NUEVO
```

La función `ejecutar_etl()` ahora recibe un parámetro `guardar_en_bd=True`.
Cuando está activo, al finalizar la transformación se crea una sesión de
SQLAlchemy, se instancia el repositorio y se insertan todos los registros
válidos. La sesión se cierra en un bloque `finally` para garantizar que
los recursos se liberen incluso si ocurre un error.

### Manejo de Errores

Si la inserción falla, se ejecuta `session.rollback()` para dejar la base
de datos en un estado consistente (sin datos a medio insertar). El error
se imprime en consola pero no interrumpe el flujo: los registros procesados
se siguen retornando al llamador.

## 5. Degradación Graceful del Geocodificador

Como mejora de robustez, se modificó `data/geocoding.py` para que no falle
si la variable de entorno `GOOGLE_MAPS_KEY` no está configurada. En lugar
de crear un cliente de Google Maps con `key=None` (que lanza excepción),
ahora se asigna `self.gmaps = None` y el método `obtener_coordenadas()`
retorna `None` inmediatamente si no hay cliente disponible. El ETL ya
manejaba coordenadas nulas, por lo que esta mejora no requirió cambios
adicionales en el pipeline.

## 6. Pruebas del Repositorio

Se creó el archivo `tests/test_storage.py` con 5 pruebas que validan:

1. **Inserción y conteo**: Insertar un registro y verificar que `contar()` devuelva 1.
2. **Inserción por lotes**: Insertar 3 registros y verificar el conteo total.
3. **Filtro por año**: Insertar registros de distintos años y verificar que `obtener_por_año()` filtre correctamente.
4. **Filtro por gravedad**: Insertar registros con distintas gravedades y verificar el filtro.
5. **Orden descendente**: Verificar que `obtener_todos()` retorna los registros del más reciente al más antiguo.

Las pruebas usan una base de datos SQLite en memoria (`:memory:`) para no
contaminar el archivo `accidentalidad.db` real. Cada test crea y destruye
su propio entorno en `setUp()` y `tearDown()`.

## 7. Resultados

En la ejecución de prueba, el sistema procesó **500 registros** desde la
API, los transformó, geocodificó y almacenó correctamente en SQLite. Las
5 pruebas del repositorio pasaron sin errores, validando que las operaciones
CRUD funcionan según lo esperado.

| Métrica | Resultado |
|---|---|
| Registros extraídos | 500 |
| Registros insertados en BD | 500 |
| Coordenadas geocodificadas | 500 (100%) |
| Tests del repositorio | 5/5 OK |
