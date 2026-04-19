# Plan de Entregables y Delimitación Técnica

El siguiente cronograma vincula las exigencias modulares de la asignatura con la arquitectura real de la aplicación web, marcando los límites de cada fase para un desarrollo ordenado.

---

## ENTREGA 1: Ingesta de Datos Abiertos
*(Referente a Módulos 1, 2 y 3)*

**Objetivo:** Desarrollar el mecanismo robusto que se conecte a *datos.gov.co*, obtenga y perfile los paquetes de datos abstrayéndolos a clases.

*   **Puntos Lógicos:** `api/api_client.py`, `models/entidades.py` y `data/etl.py`.
*   **Alances y Criterios:** Lograr mapear un lote de JSON crudo a clases de transferencia (DTO) estructuradas en Python, forzando la corrección de campos sucios (p. ej. homogeneizar meses y asegurar números enteros).

---

## ENTREGA 2: Motor de Persistencia de Datos DAO (CRUD)
*(Referente al Módulo 4)*

**Objetivo:** Integrar un gestor de base de datos relacional para sostener la información obtenida.

*   **Puntos Lógicos:** `data/database.py` y `data/storage.py`.
*   **Alcances y Criterios:** Emplear SQLAlchemy para diseñar modelos fijos en SQLite locales. Desarrollar el Repositorio CRUD aislando enteramente las sentencias SQL para que puedan ser convocadas transparentemente por cualquier parte del sistema superior. Debe ser capaz de insertar bloques de cientos de registros con transacciones limpias.

---

## ENTREGA 3: Despliegue Web MVC y Analítica
*(Referente a Módulos 5, 6 y 7)*

**Objetivo:** Articular el flujo central, conectando los servicios internos construidos para proveer información estructurada al usuario final a través de la web.

*   **Puntos Lógicos:** `views/app.py`, `controllers/main_controller.py`, `views/templates/index.html` y los recursos de `views/static/`.
*   **Alcances y Criterios:** Instanciar las rutas REST y las vistas HTML con FastAPI. Establecer asincronía en el frontend (`Alpine.js`) para manejar peticiones que alimenten diagramas analíticos reactivos usando librerías de dibujo orientadas a desempeño masivo (`Apache ECharts`). El navegador no debe saturarse con la recarga de datos.

---

## ENTREGA FINAL: Calidad, Excepciones y Presentación
*(Referente al Módulo 8)*

**Objetivo:** Estabilizar el software contra fallas no previstas o caídas de red, y redactar los manuales base.

*   **Alcances y Criterios:** Sustituir las pruebas de consola estándar por bitácoras transaccionales y de depuración (`logs`). Consolidar un `requirements.txt` o documentación del entorno virtual que garantice que la plataforma puede desplegarse en frío desde otro dispositivo.
