"""Punto de entrada del proyecto.

Este archivo ejecuta el proceso principal de acceso, transformacion y salida
basica de los datos obtenidos desde la API.
"""

import asyncio
from data.etl import ejecutar_etl


async def main():
    """
    Ejecuta la ETL y muestra una salida minima de verificacion.

    `cantidad` indica el numero de registros solicitados para la prueba.
    """
    cantidad = 500
    resultados = await ejecutar_etl(cantidad)

    print("\n--- Vista de datos extraidos ---")
    if len(resultados) > 0:
        # Se muestra el primer registro para comprobar que la carga fue correcta.
        primero = resultados[0]
        print(f"Fecha: {primero.FECHA_ACCIDENTE}")
        print(f"Mes: {primero.MES_ACCIDENTE}")
        print(f"Numero de muertos: {primero.CANT_MUERTOS_EN_SITIO_ACCIDENTE}")
        print(f"Dia: {primero.DIA_ACCIDENTE}")
    else:
        print("No se encontraron registros.")


if __name__ == "__main__":
    # Inicia el flujo asincrono principal.
    asyncio.run(main())
