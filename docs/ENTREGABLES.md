# Plan de Entregables y Delimitación Técnica (Actualizado)

Este cronograma ajusta las entregas de la asignatura a una distribución bimodal, permitiendo un desarrollo más granular y enfocado por fases.

---

## ENTREGA 1: Ingesta y Limpieza de Datos
**Responsable:** Jofier Salas (Capas de Conexión y Modelo)
*(Referente a Módulos 1 y 2)*

**Objetivo:** Desarrollar el mecanismo robusto de conexión y el perfilamiento de datos crudos.

*   **Alcances:** 
    *   Conexión estable a la API Socrata con paginación avanzada.
    *   Mapeo de registros crudos a clases DTO (Pydantic).
    *   Homogeneización de campos (Días, meses y tipos numéricos).
*   **Archivos Clave:** `api/api_client.py`, `models/entidades.py`, `data/etl.py`.

---

## ENTREGA 2: Persistencia y Repositorio DAO
**Responsable:** Jofier Salas (Repositorio y ETL)
*(Referente a Módulos 3 y 4)*

**Objetivo:** Implementar la capa de almacenamiento para que los datos limpios sean persistentes.

*   **Alcances:**
    *   Diseño del patrón Repositorio (DAO) para aislar la lógica de datos.
    *   Configuración del motor de base de datos relacional (SQLite/SQLAlchemy).
    *   Migración de objetos de memoria a tablas físicas.
*   **Archivos Clave:** `data/storage.py`, `data/database.py`.

---

## ENTREGA 3: Controladores y Lógica de Negocio
**Responsable:** Juan Medina (Capas de Controlador y Enrutado)
*(Referente a Módulos 5 y 6)*

**Objetivo:** Conectar la base de datos con la interfaz de usuario mediante la lógica del controlador.

*   **Alcances:**
    *   Configuración de endpoints con FastAPI.
    *   Implementación de la lógica de negocio en los controladores.
    *   Preparación de los datos para ser consumidos por el Frontend.

---

## ENTREGA FINAL: Interfaz, Visualización y Calidad
**Responsable:** Juan Medina (Capas de Vista Interfaz)
*(Referente a Módulos 7 y 8)*

**Objetivo:** Desplegar la interfaz web interactiva y asegurar la estabilidad del sistema.

*   **Alcances:**
    *   Renderizado de plantillas HTML y componentes reactivos (Alpine.js).
    *   Generación de analítica interactiva (Apache ECharts).
    *   Manejo global de excepciones, bitácoras (logs) y manuales técnicos.
*   **Archivos Clave:** `views/`, `main.py`.
