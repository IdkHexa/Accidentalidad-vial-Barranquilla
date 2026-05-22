"""Precarga masiva de coordenadas en el geocaché.

Este script recorre todas las direcciones del dataset completo de
Socrata, geocodifica únicamente las que aún no están en el caché
y actualiza ``geocache.json`` para que el ETL posterior no tenga
que llamar a Google Maps ni una sola vez.

Es una operación que se ejecuta UNA SOLA VEZ.  Después de correrlo,
el ETL normal corre completamente gratis en términos de geocodificación.
"""

import asyncio
import sys

from api.api_client import ApiClient
from data.direccion_parser import parsear_texto
from data.geocoding import GeoCoder
from config import API_URL, DATASET_ID


async def obtener_total(cliente):
    """Descubre cuántos registros tiene el dataset en la API de Socrata.

    Usa ``$select=count(*)`` para traer solo el número, no los datos,
    y así evitar descargar 28k registros solo para saber el total.
    """
    resp = await cliente.client.get(
        API_URL,
        params={"$select": "count(*)"},
    )
    resp.raise_for_status()
    return int(resp.json()[0]["count"])


async def precargar_geocache(dry_run=False):
    """Orquesta la descarga masiva y la geocodificación diferida.

    La función trabaja en tres etapas:
    1. Consulta el total de registros en la API.
    2. Descarga todos los registros.
    3. Por cada dirección que no esté en ``geocache.json``,
    llama a Google Maps para obtener sus coordenadas y las guarda.

    El parámetro ``dry_run`` permite simular la operación sin gastar
    créditos de la API de Google Maps, útil para estimar costos antes
    de ejecutar la precarga real.
    """
    cliente = ApiClient()
    geocoder = GeoCoder()

    try:
        print("Consultando la API para obtener el total de registros...")
        total = await obtener_total(cliente)
        print(f"Total de registros disponibles: {total}")

        print(f"Descargando {total} registros para precarga de coordenadas...")
        datos = await cliente.get_dataset_limit(DATASET_ID, total)
        print(f"Descargados {len(datos)} registros para precarga.\n")

        if not datos:
            print("No se descargaron registros.  Nada que procesar.")
            return

        cacheadas = 0
        nuevas = 0
        fallidas = 0
        sin_direccion = 0

        print("Procesando direcciones...")
        for i, fila in enumerate(datos):
            raw = fila.get("sitio_exacto_accidente", "")
            if not raw:
                sin_direccion += 1
                continue

            direccion = parsear_texto(raw)

            if dry_run:
                key = str(direccion)
                if key in geocoder.cache:
                    cacheadas += 1
                else:
                    nuevas += 1
            else:
                coords = geocoder.obtener_coordenadas(direccion)
                if coords is None:
                    if str(direccion) in geocoder.cache:
                        cacheadas += 1
                    else:
                        fallidas += 1
                else:
                    nuevas += 1

            if (i + 1) % 500 == 0:
                pct = (i + 1) / len(datos) * 100
                print(
                    f" {i+1}/{len(datos)} ({pct:.0f}%)"
                    f" - cacheadas: {cacheadas}, nuevas: {nuevas},"
                    f" fallidas: {fallidas}, sin dirección: {sin_direccion}"
                )

        _mostrar_reporte(len(datos), cacheadas, nuevas, fallidas, sin_direccion)

        if dry_run:
            print(
                "\n[DRY RUN] No se realizaron geocodificaciones reales."
                f"\nEn un escenario real, se habrían geocodificado {nuevas} direcciones nuevas."
            )

    finally:
        # Guarda las coordenadas pendientes antes de salir.
        geocoder.guardar()
        # Libera las conexiones HTTP abiertas para no dejar fugas.
        await cliente.close()


def _mostrar_reporte(total, cacheadas, nuevas, fallidas, sin_direccion):
    """Imprime el resumen final de la precarga.

    Separar esto en una función mantiene el método principal enfocado
    exclusivamente en el flujo de datos.
    """
    print("\nPrecarga de coordenadas completada.")
    print("Reporte final:")
    print(f"  Total registros procesados: {total}")
    print(f"  Cacheadas:                 {cacheadas}")
    print(f"  Nuevas geocodificaciones:  {nuevas}")
    print(f"  Fallidas:                  {fallidas}")
    print(f"  Sin dirección:             {sin_direccion}")


def main():
    """Punto de entrada del script.

    Interpreta ``--dry-run`` en los argumentos de línea de comandos
    para permitir una ejecución de prueba sin consumir créditos de la
    API de Google Maps.
    """
    dry_run = "--dry-run" in sys.argv
    asyncio.run(precargar_geocache(dry_run=dry_run))


if __name__ == "__main__":
    main()
