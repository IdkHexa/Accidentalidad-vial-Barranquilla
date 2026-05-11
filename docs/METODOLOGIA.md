# Metodología de Desarrollo y Acuerdos del Equipo

**Proyecto:** Análisis Web de Accidentalidad Vial en Barranquilla
**Arquitectura:** MVC (Modelo-Vista-Controlador) y API REST
**Integrantes:** Jofier Salas y Juan Medina

Este documento define las reglas de trabajo colaborativo y la asignación de responsabilidades para el proyecto de Desarrollo de Aplicaciones con Acceso a Datos.

## 1. Reglas de Colaboración
* **Uso de Git y GitHub:** Utilizaremos un repositorio centralizado. Las credenciales, la base de datos compilada (`.db`) y cachés de Python se omiten obligatoriamente vía `.gitignore`.
* **Separación de Capas (MVC):** Para evitar cuellos de botella e interferencias en Git, se acordó segmentar el proyecto horizontalmente por responsabilidades tecnológicas.

## 2. Roles Asignados

### Capas de Conexión, Modelo y Repositorio (Jofier Salas)
Responsable del ecosistema de almacenamiento y extracción ETL.
* Ingesta de la API pública Socrata (*datos.gov.co*) con paginación estable.
* Transformación de tipos de datos, homologación de fechas e identificación de datos corruptos.
* Estructuración del mapeo objeto-relacional (ORM) usando SQLAlchemy.
* Desarrollo y auditoría de todas las consultas CRUD base.

### Capas de Controlador, Vista e Interfaz (Juan Medina)
Responsable del despliegue web, endpoints del servidor y reactividad del cliente.
* Configuración de la plataforma principal en FastAPI.
* Enrutado de peticiones y respuestas mediante esquemas JSON (Pydantic).
* Programación de vistas HTML y asincronía de la UI mediante Alpine.js.
* Renderizado paramétrico e interactivo del panel de visualización en Apache ECharts.
