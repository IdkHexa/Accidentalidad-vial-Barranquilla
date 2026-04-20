import asyncio
from data.etl import ejecutar_etl

async def main():
    # Pedimos 500 registros para probar
    cantidad = 500
    resultados = await ejecutar_etl(cantidad)
    
    print("\n--- Vista de datos extraídos ---")
    if len(resultados) > 0:
        # Mostramos los datos del primer accidente
        primero = resultados[0]
        print(f"Fecha: {primero.FECHA_ACCIDENTE}")
        print(f"Mes: {primero.MES_ACCIDENTE}")
        print(f"Número de muertos: {primero.CANT_MUERTOS_EN_SITIO_ACCIDENTE}")
        print(f"Día: {primero.DIA_ACCIDENTE}")
    else:
        print("No se encontraron registros.")

if __name__ == "__main__":
    # Arrancamos el programa
    asyncio.run(main())