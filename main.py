"""Punto de entrada principal del proyecto.

Este archivo es el que se ejecuta cuando corres ``python main.py``
en la terminal.  Su responsabilidad es inicializar la base de datos
y lanzar el pipeline ETL que descarga, transforma y persiste los
datos de accidentalidad de Barranquilla.

Al ejecutarlo, la consola mostrara el progreso de cada etapa y un
resumen del primer registro procesado para confirmar que todo
funciono correctamente.
"""

import asyncio

from data.database import init_db
from data.etl import ejecutar_etl


async def main():
    """Orquesta el flujo completo del programa.

    1. Llama a ``init_db()`` para asegurarse de que la tabla
       ``accidentes`` existe en SQLite.
    2. Ejecuta el ETL con 500 registros y persistencia habilitada.
    3. Muestra una vista previa del primer registro para verificar
       que los datos se cargaron y transformaron correctamente.
    """
    init_db()
    print("Base de datos inicializada.\n")

    cantidad = 10**6 # Numero grande para asegurar que se procesen todos los registros disponibles.
    resultados = await ejecutar_etl(cantidad, guardar_en_bd=True)

    print("\n--- Vista de datos extraidos ---")
    if resultados:
        primero = resultados[0]
        print(f"Fecha: {primero.FECHA_ACCIDENTE}")
        print(f"Mes: {primero.MES_ACCIDENTE}")
        print(f"Numero de muertos: {primero.CANT_MUERTOS_EN_SITIO_ACCIDENTE}")
        print(f"Dia: {primero.DIA_ACCIDENTE}")
    else:
        print("No se encontraron registros.")


if __name__ == "__main__":
    asyncio.run(main())
