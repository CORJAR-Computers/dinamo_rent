#!/usr/bin/env python3
"""
migrate_env_to_ini.py — Migración de configuración .env a config.ini

Este script:
1. Lee el archivo .env existente
2. Crea/configura config.ini con los valores encontrados
3. Mantiene compatibilidad con el sistema anterior
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv


def migrate_env_to_ini(env_path: str = None, ini_path: str = None):
    """
    Migra configuración de .env a config.ini.

    Args:
        env_path: Ruta al archivo .env (None = .env en directorio actual)
        ini_path: Ruta al archivo config.ini de salida
    """
    base_dir = Path(__file__).resolve().parent

    if env_path is None:
        env_path = base_dir / ".env"
    else:
        env_path = Path(env_path)

    if ini_path is None:
        ini_path = base_dir / "config.ini"
    else:
        ini_path = Path(ini_path)

    # Verificar que .env exista
    if not env_path.exists():
        print(f"❌ No se encontró {env_path}")
        return False

    print(f"📖 Leyendo {env_path}...")
    load_dotenv(env_path, override=True)

    # Leer config.ini existente o crear nuevo
    import configparser
    config = configparser.ConfigParser(interpolation=None)

    if ini_path.exists():
        print(f"📖 Leyendo {ini_path} existente...")
        config.read(ini_path, encoding='utf-8')
    else:
        print(f"📝 Creando nuevo {ini_path}...")
        # Copiar desde config.ini.example si existe
        example_path = base_dir / "config.ini.example"
        if example_path.exists():
            config.read(example_path, encoding='utf-8')
            print("✅ Usando config.ini.example como plantilla")
        else:
            print("⚠️ No se encontró config.ini.example, creando desde cero")

    # Migrar valores de .env a config.ini
    migrations = {
        # (.env variable, ini_section, ini_key)
        'DINAMO_DB_ENGINE': ('database', 'engine'),
        'DINAMO_DB_HOST': ('database', 'host'),
        'DINAMO_DB_PORT': ('database', 'port'),
        'DINAMO_DB_USER': ('database', 'user'),
        'DINAMO_DB_PASSWORD': ('database', 'password'),
        'DINAMO_DB_NAME': ('database', 'database'),
    }

    migrated = []
    for env_var, (ini_section, ini_key) in migrations.items():
        value = os.getenv(env_var)
        if value:
            if not config.has_section(ini_section):
                config.add_section(ini_section)
            config.set(ini_section, ini_key, value)
            migrated.append(f"  ✅ {env_var} -> [{ini_section}] {ini_key}")

    # Guardar config.ini
    print(f"\n💾 Guardando {ini_path}...")
    with open(ini_path, 'w', encoding='utf-8') as f:
        config.write(f)

    print("\n🎉 Migración completada!")
    print("\nValores migrados:")
    for m in migrated:
        print(m)

    print("\n⚠️ IMPORTANTE:")
    print(f"  1. Revisar que {ini_path} tenga todos los valores correctos")
    print(f"  2. Agregar {ini_path} a .gitignore si contiene contraseñas")
    print("  3. Usar config.ini.example para version control")

    return True


if __name__ == "__main__":
    success = migrate_env_to_ini()
    sys.exit(0 if success else 1)
