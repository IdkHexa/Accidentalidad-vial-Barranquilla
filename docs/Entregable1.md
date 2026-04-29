# Documentación Técnica: Módulo de Geocoding y ETL
**Proyecto:** Análisis de Accidentalidad Vial en Barranquilla
**Responsable:** Jofier Salas

## 1. Introducción
Este documento detalla la implementación técnica del motor de ingesta, limpieza y geocodificación de datos para el proyecto de accidentalidad. Se ha priorizado la robustez del código y la eficiencia en el uso de recursos externos.

## 2. Fase de Diseño y Normalización
Para garantizar una geocodificación precisa, se implementó una capa de pre-procesamiento de direcciones:
*   **Limpieza de Ruido**: Eliminación de términos no geográficos (ej: "FRENTE", "BARRIO", "ESQUINA") que introducen error en los motores de búsqueda.
*   **Estandarización**: Conversión de abreviaturas locales (`CL`, `CRA`, `TV`) a términos canónicos reconocidos por estándares internacionales.
*   **Regex Robusto**: Implementación de expresiones regulares que permiten capturar variaciones tipográficas, incluyendo nomenclaturas con letras (ej: 45B, 9G).

## 3. Arquitectura del Sistema

### A. Parser de Direcciones (`direccion_parser.py`)
Módulo encargado de la lógica de negocio para entender las direcciones de Barranquilla. Utiliza `dataclasses` para mantener la integridad de los datos parseados (vía, cruce, placa e intersecciones).

### B. Geocodificador con Google Maps y Caché (`geocoding.py`)
Se integró la API de Google Maps para obtener coordenadas de alta precisión.
*   **Sistema de Caché Persistente**: Se diseñó un almacén local en `data/geocache.json`. Este sistema actúa como un "escudo" que evita peticiones duplicadas a la API, optimizando costos y permitiendo que el sistema funcione instantáneamente para direcciones ya conocidas.

### C. Proceso ETL (`etl.py`)
Tubería asíncrona que coordina la extracción desde la API de Socrata, la validación mediante Pydantic y el enriquecimiento geográfico.

## 4. Validación de Calidad (Unit Testing)
A diferencia de métodos manuales, la calidad del sistema se garantiza mediante una suite de pruebas automatizadas en la carpeta `tests/`:
*   **Pruebas de Parser**: Verificación de casos de borde, intersecciones y limpieza de ruido.
*   **Pruebas de Geocoding**: Validación de la generación de queries y el comportamiento del caché.

## 5. Resultados de Performance
En pruebas de carga, el sistema procesó **500 registros en 110 segundos**, logrando una efectividad del **100% en la ubicación geográfica** de los incidentes.
