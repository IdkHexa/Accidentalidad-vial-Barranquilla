# Proyecto Accidentalidad Barranquilla (Módulo 1 y 2)

Este proyecto sirve para bajar los datos de accidentes de Barranquilla desde Internet y organizarlos para poder usarlos después.

## ¿Qué hace el programa?
1. **Baja los datos**: Se conecta a la página de Datos Abiertos de Colombia.
2. **Limpia la información**: Si los datos vienen en minúsculas, los pasa a MAYÚSCULAS. Si los números vienen mal, los arregla.
3. **Muestra un resumen**: Te dice cuántos registros bajó y si alguno tuvo error.

## Estructura de carpetas
- `api/api_client.py`: Tiene el código para conectarse a Internet.
- `models/entidades.py`: Aquí definimos qué datos queremos (Fecha, Hora, Clase de accidente, etc.).
- `data/etl.py`: Es el "cerebro" que une todo (baja los datos y los organiza).
- `main.py`: Es el archivo que tienes que ejecutar para que el programa empiece.

## Cómo usarlo

1. **Instalar lo necesario**:
   Escribe esto en tu terminal:
   ```bash
   pip install -r requirements.txt
   ```

2. **Ejecutar el programa**:
   Escribe esto en tu terminal:
   ```bash
   python main.py
   ```

## Notas académicas
- El programa usa **Pydantic** para asegurar que los datos sean correctos.
- Usa **Asyncio** para que la descarga sea rápida y no se trabe el computador mientras baja miles de datos.
