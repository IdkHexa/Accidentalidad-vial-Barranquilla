import asyncio
from data.etl import ejecutar_etl

# Esta es la función principal que orquesta todo el programa
async def main():
    # Definimos cuántos registros queremos traer de la API (500 para pruebas)
    cantidad = 500
    # Llamamos a la función ETL que hace la magia de extraer y limpiar
    resultados = await ejecutar_etl(cantidad)
    
    print("\n--- Vista de datos extraídos ---")
    if len(resultados) > 0:
        # Mostramos los datos del primer accidente para confirmar que todo funciona
        primero = resultados[0]
        print(f"Fecha: {primero.FECHA_ACCIDENTE}")
        print(f"Mes: {primero.MES_ACCIDENTE}")
        print(f"Número de muertos: {primero.CANT_MUERTOS_EN_SITIO_ACCIDENTE}")
        print(f"Día: {primero.DIA_ACCIDENTE}")
    else:
        print("No se encontraron registros.")

if __name__ == "__main__":
    # Arrancamos el bucle de eventos asíncronos para que el programa corra
    asyncio.run(main())
