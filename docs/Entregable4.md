# Documentación Técnica: Interfaz, Visualización y Calidad
**Proyecto:** Análisis de Accidentalidad Vial en Barranquilla
**Responsable:** Juan David Medina
**Módulos:** 7 y 8 — Entrega Final

## 1. Introducción

Este documento describe la capa de presentación del proyecto: las plantillas
HTML, los gráficos interactivos con Apache ECharts, el mapa geoespacial con
Leaflet, y el sistema de logging centralizado.  También cubre la estrategia
de pruebas unitarias y la integración completa del sistema.

La interfaz web permite al usuario explorar los 28,328 registros de
accidentalidad vial en Barranquilla a través de un dashboard con KPIs,
gráficos estadísticos, un mapa de calor interactivo y un formulario
para registrar nuevos accidentes.

## 2. Arquitectura del Frontend

### Stack Técnico

| Componente | Tecnología | Propósito |
|---|---|---|
| Motor de plantillas | Jinja2 | Renderizado HTML del lado servidor |
| Reactividad ligera | Alpine.js | Interactividad sin framework pesado |
| Gráficos estadísticos | Apache ECharts 5.4 | Gráficas de barras, líneas, dona |
| Mapas interactivos | Leaflet 1.9 | Mapa de Barranquilla con markers y heat layer |
| Heatmap | leaflet.heat 0.2 | Capa de densidad sobre el mapa |
| Estilos | CSS custom (variables) | Tema oscuro con paleta consistente |
| Fuentes | Space Grotesk + JetBrains Mono | Tipografía sans-serif + monoespaciada |

### Estructura de Plantillas

```
views/templates/
├── base.html        ← Layout común: sidebar, topbar, CSS global
├── index.html       ← Landing page (no extiende base, layout propio)
├── dashboard.html   ← Panel de estadísticas con 6 gráficos
├── mapa.html        ← Mapa de calor con filtros
└── registro.html    ← Formulario CRUD con mini-mapa
```

### Layout Base (`base.html`)

El layout común define:

- **Sidebar** con navegación entre las tres secciones principales
  (Dashboard, Mapa, Registro) y pie con metadata del dataset.
- **Topbar** sticky con título de página e indicador de estado (pulso).
- **Bloques Jinja2** para que cada página personalice contenido:
  - `{% block title %}` — título de pestaña
  - `{% block page_title %}` — título en la topbar
  - `{% block head %}` — CSS/HTML adicional en `<head>`
  - `{% block content %}` — contenido principal
  - `{% block scripts %}` — JavaScript al final del `<body>`

El CSS global incluye las variables de diseño (--accent, --bg, etc.),
estilos para KPIs, tarjetas, tablas, formularios, badges de gravedad,
toasts de notificación, scrollbar personalizado y animaciones de entrada.

## 3. Página de Inicio (`index.html`)

Landing page con layout propio (no extiende base.html) que presenta
el proyecto al usuario:

- **Hero section** con título animado, subtítulo y estadísticas clave
  que se cargan dinámicamente desde `/api/stats/resumen`.
- **Tarjetas de navegación** hacia las tres secciones principales
  (Dashboard, Mapa, Registro) con efectos hover y iconos.
- **Barra de stack técnico** que muestra las tecnologías usadas.
- **Footer** con información de la asignatura y los integrantes.

El fondo tiene una rejilla animada y dos halos de color (glow) que
dan profundidad visual sin afectar el rendimiento.

## 4. Dashboard de Estadísticas (`dashboard.html`)

### 4.1 KPIs (Tarjetas Superiores)

Cuatro tarjetas con indicadores clave que se cargan asíncronamente:

| KPI | Endpoint | Formato |
|---|---|---|
| Total registros | `/api/stats/resumen` → `total` | Número con separador de miles |
| Muertos en sitio | `/api/stats/resumen` → `muertos` | Número con separador de miles |
| Heridos en sitio | `/api/stats/resumen` → `heridos` | Número con separador de miles |
| Rango de años | `/api/stats/resumen` → `año_inicio` / `año_fin` | "2018 → 2024" |

Cada tarjeta tiene un color de acento diferente (cyan, rojo, amarillo,
púrpura) y una animación de entrada escalonada (`fade-up` con delays).

### 4.2 Gráficos Interactivos (Apache ECharts)

Seis gráficos se renderizan con ECharts, cada uno consumiendo un endpoint
distinto de la API:

| Gráfico | Tipo | Endpoint | Descripción |
|---|---|---|---|
| Accidentes por año | Línea + barras | `/api/stats/por_año` | Tendencia anual con muertos y heridos superpuestos |
| Distribución por gravedad | Dona (pie) | `/api/stats/por_gravedad` | Proporción de accidentes por categoría |
| Por mes del año | Barras | `/api/stats/por_mes` | Estacionalidad mensual |
| Por día de la semana | Barras | `/api/stats/por_dia` | Fines de semana en rojo para resaltar |
| Por hora del día | Línea de área | `/api/stats/por_hora` | Picos de accidentalidad por hora |
| Clase de accidente | Barras horizontales | `/api/stats/por_clase` | Top 10 con colores rotativos |

**Configuración común**: todos los gráficos comparten fondo transparente,
fuente Space Grotesk, rejilla con líneas oscuras y paleta de colores
coherente con el tema.  Todos responden al redimensionamiento de la
ventana con `window.addEventListener('resize', ()=>c.resize())`.

**Carga paralela**: los 8 recursos (6 gráficos + KPIs + tabla) se
solicitan simultáneamente con `Promise.all()` para minimizar el tiempo
de carga inicial.

### 4.3 Tabla de Registros Recientes

Panel derecho inferior que muestra los últimos 30 accidentes en una
tabla con columnas: Fecha, Gravedad (badge de color), Clase, Heridos
y Muertos.  Los valores numéricos usan fuente monoespaciada con los
colores del tema (amarillo para heridos, rojo para muertos).

## 5. Mapa de Calor (`mapa.html`)

### 5.1 Mapa Base

Se usa Leaflet con tiles de CartoDB Dark Matter para mantener la
coherencia visual con el tema oscuro del dashboard.  El mapa se
centra en Barranquilla (10.9685, -74.7813) con zoom 12.

### 5.2 Modos de Visualización

El panel de controles permite alternar entre dos modos:

- **Mapa de calor** (`leaflet.heat`): capa de densidad con gradiente
  cyan → amarillo → naranja → rojo.  Radio 18px, blur 20.
- **Puntos individuales**: circleMarkers coloreados por gravedad
  (rojo=muertos, amarillo=heridos, gris=solo daños) con popups
  que muestran clase, fecha, sitio y coordenadas.

### 5.3 Filtros

- **Por gravedad**: dropdown que filtra los puntos mostrados
  (Todas, Con muertos, Con heridos, Solo daños).
- **Clústers**: toggle para mostrar/ocultar las zonas calientes
  detectadas por DBSCAN (conectadas al endpoint `/api/stats/clusters`).

### 5.4 Panel de Estadísticas

Muestra en tiempo real la cantidad de puntos cargados y cuántos
tienen coordenadas válidas.

## 6. Formulario de Registro (`registro.html`)

### 6.1 Layout

Panel izquierdo con el formulario completo y panel derecho con un
mini-mapa interactivo y el historial de registros de la sesión.

### 6.2 Campos del Formulario

| Campo | Tipo | Validación |
|---|---|---|
| Fecha | date | Requerido, auto-fill con fecha actual |
| Hora | time | Requerido, auto-fill con hora actual |
| Gravedad | select | Requerido (Con muertos/Con heridos/Solo daños) |
| Clase | select | Requerido (Choque/Atropello/Caida/Volcamiento/Incendio/Otro) |
| Año | number | Requerido, rango 2018–2030, auto-fill con año actual |
| Mes | select | Requerido (ENERO–DICIEMBRE) |
| Día | select | Requerido (LUNES–DOMINGO) |
| Sitio exacto | text | Opcional |
| Heridos | number | Default 0, mínimo 0 |
| Muertos | number | Default 0, mínimo 0 |
| Latitud/Longitud | hidden | Llenados automáticamente al hacer clic en el mapa |

### 6.3 Mini-mapa Interactivo

Un mapa Leaflet centrado en Barranquilla donde el usuario puede hacer
clic para fijar las coordenadas del accidente.  Se muestra un
circleMarker cyan en la posición seleccionada y las coordenadas se
reflejan en los campos de solo lectura debajo del mapa.

### 6.4 Historial de Sesión

Cada accidente registrado exitosamente se agrega a una lista en el
panel derecho con badge de gravedad, ID asignado, clase y fecha.
El historial se mantiene solo en memoria del navegador (no persiste
entre recargas).

### 6.5 Notificaciones Toast

Al registrar un accidente, aparece un toast animado en la esquina
inferior derecha confirmando el ID asignado o reportando error.
El toast se oculta automáticamente después de 3.5 segundos.

## 7. Sistema de Logging (`utils/logger.py`)

### 7.1 Diseño

Se implementó un módulo de logging centralizado usando el módulo
estándar `logging` de Python.  Cualquier componente del sistema puede
obtener un logger con:

```python
from utils.logger import obtener_logger
log = obtener_logger(__name__)
log.info("Mensaje informativo")
```

### 7.2 Configuración

- **Nivel**: se controla con la variable de entorno `LOG_LEVEL`
  (DEBUG, INFO, WARNING, ERROR).  Por defecto es INFO.
- **Salida**: escribe en stderr por defecto.  Si existe el directorio
  `logs/`, también escribe en `logs/app.log`.
- **Formato**: `2026-06-16 10:30:00 | INFO     | data.etl             | Mensaje`
- **Idempotente**: `configurar_logging()` solo se ejecuta una vez
  gracias a la bandera `_configurado`, evitando handlers duplicados.

## 8. Pruebas Unitarias (Módulo 8)

### 8.1 Suite de Tests

El proyecto cuenta con **10 archivos de prueba** en la carpeta `tests/`
que cubren los módulos 1 al 4 (implementados por Jofier) y el módulo
de analytics:

| Archivo | Módulo | Pruebas | Qué valida |
|---|---|---|---|
| `test_parser.py` | Parser de direcciones | 4 | Normalización de nomenclaturas |
| `test_geocoding.py` | Geocodificador | 2 | Caché y generación de queries |
| `test_entidades.py` | DTO Pydantic | 12 | Validación y normalización de campos |
| `test_api_client.py` | Cliente HTTP | 6 | Paginación y manejo de errores |
| `test_database.py` | Mapeo ORM | 4 | Conversión DTO → ORM |
| `test_storage.py` | Repositorio DAO | 6 | CRUD y filtros |
| `test_etl.py` | Pipeline ETL | 5 | Flujo completo de transformación |
| `test_config.py` | Configuración | 3 | Fallbacks y variables de entorno |
| `test_seed_geocache.py` | Precarga caché | 2 | Script de geocodificación masiva |
| `test_clustering.py` | DBSCAN | 18 | Clustering con datos sintéticos |

### 8.2 Estrategia de Testing

- **Aislamiento**: cada test usa su propia base de datos en memoria
  (`:memory:`) para no contaminar los datos reales.
- **Datos sintéticos**: los tests de clustering usan DataFrames
  generados programáticamente, sin dependencia de la API ni la BD.
- **Caché separado**: los tests de geocoding usan un archivo
  `tests/test_geocache.json` para no mezclar con el caché de producción.
- **Limpieza**: `tearDown()` llama a `engine.dispose()` para liberar
  conexiones y evitar `ResourceWarning`.

### 8.3 Ejecución

```bash
# Todos los tests
python -m unittest discover tests/ -v

# Un archivo específico
python -m unittest tests.test_storage -v

# Tests de clustering
python -m unittest tests.test_clustering -v
```

## 9. Limpieza de Archivos Placeholder

Como parte de la entrega final, se eliminaron los archivos placeholder
que no eran necesarios para el funcionamiento del sistema:

| Archivo eliminado | Razón |
|---|---|
| `api/sync_manager.py` | La sincronización la maneja `etl.py` directamente |
| `utils/visualizer.py` | Los gráficos los genera ECharts en el frontend |
| `views/app.py` | Solo contenía un import; el controller ya expone `app` |
| `views/static/css/style.css` | Los estilos están en `base.html` (inline) |
| `views/static/js/chart_builder.js` | Los gráficos se configuran inline en cada template |

Se implementó `utils/logger.py` como reemplazo funcional del placeholder
`utils/logger.py`, proporcionando logging centralizado para todo el sistema.

## 10. Integración Completa del Sistema

### Flujo de Datos End-to-End

```
1. API Socrata (datos.gov.co)
     ↓  api/api_client.py (httpx async + paginación)
2. Validación Pydantic (models/entidades.py)
     ↓  data/etl.py (transformación + geocodificación)
3. Base de datos (data/database.py + data/storage.py)
     ↓  controllers/main_controller.py (FastAPI)
4. Interfaz web (views/templates/ + ECharts + Leaflet)
     ↓  analytics/clustering.py (DBSCAN)
5. Zonas calientes → Mapa de calor
```

### Cómo Levantar el Sistema Completo

```bash
# 1. Activar entorno virtual
venv\Scripts\activate

# 2. (Opcional) Levantar PostgreSQL
docker compose up -d

# 3. Ejecutar el pipeline ETL (descarga + transforma + persiste)
python main.py

# 4. Arrancar el servidor web
uvicorn controllers.main_controller:app --reload

# 5. Abrir en el navegador
# http://127.0.0.1:8000/
```

### Documentación Automática de la API

FastAPI genera documentación interactiva en:
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## 11. Dificultades Encontradas

### 11.1. ECharts no redimensiona al cambiar de pestaña

**Problema:** Los gráficos de ECharts no se redimensionaban automáticamente
cuando el usuario cambiaba de pestaña del navegador o redimensionaba la
ventana, quedando con el tamaño incorrecto.

**Solución:** Agregar `window.addEventListener('resize', ()=>c.resize())`
inmediatamente después de inicializar cada gráfico.  Esto le indica a
ECharts que recalcule sus dimensiones cuando cambie el tamaño del contenedor.

### 11.2. Leaflet popup con estilo del tema oscuro

**Problema:** Los popups por defecto de Leaflet tienen fondo blanco, lo
que rompía la estética del tema oscuro del dashboard.

**Solución:** Sobrescribir los estilos de Leaflet con `!important` en el
bloque `<style>` de `mapa.html`:

```css
.leaflet-popup-content-wrapper {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
}
```

### 11.3. Auto-fill de fecha/hora en el formulario

**Problema:** El formulario de registro requería que el usuario ingresara
fecha, hora y año manualmente, lo que era propenso a errores.

**Solución:** Agregar un IIFE en el script de `registro.html` que usa
`new Date()` para pre-llenar los campos de fecha, hora y año con los
valores actuales.  El usuario puede cambiarlos si lo necesita.

### 11.4. Carga lenta del dashboard con muchos gráficos

**Problema:** El dashboard cargaba los 8 recursos (6 gráficos + KPIs + tabla)
de forma secuencial, lo que causaba una espera notable.

**Solución:** Usar `Promise.all()` para disparar todas las peticiones
`fetch()` simultáneamente.  Los gráficos se renderizan en paralelo y el
dashboard completo aparece en el tiempo que tarde el endpoint más lento.

## 12. Resultados

| Métrica | Resultado |
|---|---|
| Endpoints implementados | 17 (4 HTML + 13 JSON) |
| CRUD completo | Create, Read, Update, Delete |
| Gráficos interactivos | 6 (ECharts) |
| Mapas interactivos | 2 (Leaflet: dashboard + registro) |
| Plantillas HTML | 5 (base + index + dashboard + mapa + registro) |
| Tests unitarios | 62 pruebas en 10 archivos |
| Archivos placeholder eliminados | 5 |
| Módulos de logging | 1 (utils/logger.py) |
| Tiempo de carga del dashboard | < 2s (con datos en BD local) |
