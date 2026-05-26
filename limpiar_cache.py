#!/usr/bin/env python3
"""
limpiar_cache.py — Script de limpieza de caché de Python

F1E: Elimina todos los directorios __pycache__ y archivos .pyc del proyecto.
Ejecutar después de cambios estructurales (F1A-F1E) para evitar
que Python use bytecode obsoleto.

Uso:
    python limpiar_cache.py
"""

import os
import shutil


def limpiar_cache(directorio_raiz: str = ".") -> None:
    """Elimina __pycache__ y .pyc de forma recursiva."""
    eliminados = 0

    for raiz, dirs, archivos in os.walk(directorio_raiz):
        # Eliminar directorios __pycache__
        if "__pycache__" in dirs:
            ruta = os.path.join(raiz, "__pycache__")
            shutil.rmtree(ruta)
            eliminados += 1
            print(f"  Eliminado: {ruta}")

        # Eliminar archivos .pyc sueltos
        for archivo in archivos:
            if archivo.endswith(".pyc"):
                ruta = os.path.join(raiz, archivo)
                os.remove(ruta)
                eliminados += 1
                print(f"  Eliminado: {ruta}")

    print(f"\nLimpieza completada: {eliminados} elementos eliminados.")


if __name__ == "__main__":
    print("Limpiando caché de Python...")
    limpiar_cache()
