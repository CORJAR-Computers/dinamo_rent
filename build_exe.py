"""
build_exe.py -- Script de compilacion para Dinamo Rent ERP v3.2.1
Genera un ejecutable unico con PyInstaller.

Uso:
    python build_exe.py                  # Build normal (una carpeta)
    python build_exe.py --onefile        # Build unico .exe
    python build_exe.py --clean          # Limpia build/dist previo
    python build_exe.py --name "MiApp"   # Nombre personalizado

Requiere: pip install pyinstaller
"""

import os
import sys
import shutil
import argparse
import subprocess
from pathlib import Path

# --- Rutas -----------------------------------------------------------------
PROJECT_DIR = Path(__file__).resolve().parent
DIST_DIR = PROJECT_DIR / "dist"
BUILD_DIR = PROJECT_DIR / "build"
SPEC_FILE = PROJECT_DIR / "dinamo_rent.spec"

APP_NAME = "DinamoRentERP"
APP_VERSION = "3.2.1"
ENTRY_POINT = "main_qt.py"

# --- Recursos a incluir en el ejecutable -----------------------------------

ASSETS_DIR = PROJECT_DIR / "assets"
TEMPLATES_DIR = PROJECT_DIR / "templates"
CONFIG_EXAMPLE = PROJECT_DIR / "config.ini.example"

# Modulos con importacion dinamica que PyInstaller NO detecta automaticamente
HIDDEN_IMPORTS = [
    # Vistas (lazy loading en _cargar_vistas)
    "views.dashboard_view",
    "views.calendario_view",
    "views.rentas_view",
    "views.reservas_view",
    "views.clientes_view",
    "views.autos_view",
    "views.mantenimiento_view",
    "views.usuarios_view",
    "views.informes_view",
    "views.comparendos_view",
    "views.alertas_view",
    "views.gastos_view",
    # Componentes
    "views.components",
    "views.components.modern_messagebox",
    "views.components.toast_notification",
    "views.components.avatar_widget",
    "views.components.card_widget",
    "views.components.form_validators",
    "views.components.icon_button",
    "views.components.loading_spinner",
    "views.components.status_badge",
    # Temas
    "views.themes",
    "views.themes.theme_manager",
    "views.themes.build_stylesheet",
    "views.themes.themes",
    # Layouts
    "views.layouts",
    "views.layouts.form_helpers",
    # Dialogos cargados dinamicamente
    "views.about_dialog",
    "views.database_config_dialog",
    "views.setup_wizard",
    "views.force_change_password_dialog",
    "views.base_dialog",
    # Servicios con lazy loading desde __init__.py
    "services.alerta_service",
    "services.auth_service",
    "services.auto_service",
    "services.backup_service",
    "services.cliente_service",
    "services.comparendo_service",
    "services.dashboard_service",
    "services.financial_service",
    "services.gasto_service",
    "services.informe_service",
    "services.inspeccion_service",
    "services.mantenimiento_service",
    "services.pago_service",
    "services.renta_service",
    "services.reserva_service",
    "services.usuario_service",
    # Core (lazy loading de modelos)
    "core.models",
    "core.database_sa",
    "core.config",
    "core.app_config",
    "core.exceptions",
    "core.logger",
    "core.security",
    "core.security_utils",
    "core.schemas",
    "core.utils",
    "core.validators",
    "core.unit_of_work",
    "core.rbac",
    # Repositorios
    "repositories",
    "repositories.base_repository_sa",
    "repositories.alerta_repository_sa",
    "repositories.auto_repository_sa",
    "repositories.cliente_repository_sa",
    "repositories.comparendo_repository_sa",
    "repositories.gasto_repository_sa",
    "repositories.informe_repository_sa",
    "repositories.inspeccion_repository_sa",
    "repositories.mantenimiento_repository_sa",
    "repositories.pago_repository_sa",
    "repositories.renta_repository_sa",
    "repositories.reserva_repository_sa",
    "repositories.usuario_repository_sa",
    # DB drivers
    "pymysql",
    "sqlalchemy",
    # Reportes / PDF
    "jinja2",
    "jinja2.ext",
    "weasyprint",
    "reportlab",
    "reportlab.lib.pagesizes",
    "reportlab.platypus",
    "reportlab.lib.styles",
    "reportlab.lib.units",
    "reportlab.pdfbase",
    "reportlab.pdfbase.ttfonts",
    # Excel
    "pandas",
    "openpyxl",
    # Seguridad
    "cryptography",
    "cryptography.hazmat.primitives",
    "cryptography.hazmat.primitives.ciphers",
    "cryptography.hazmat.backends",
    # Config
    "configparser",
]


def _collect_assets():
    """Recopila assets/ completos."""
    items = []
    if ASSETS_DIR.exists():
        for f in ASSETS_DIR.iterdir():
            if f.is_file():
                items.append((str(f), "assets"))
    return items


def _collect_templates():
    """Recopila templates/ completos."""
    items = []
    if TEMPLATES_DIR.exists():
        for f in TEMPLATES_DIR.rglob("*"):
            if f.is_file():
                items.append((str(f), str(f.parent.relative_to(PROJECT_DIR))))
    return items


def _build_spec(args):
    """Genera el archivo .spec de PyInstaller y lo ejecuta."""

    data_files = []
    data_files.extend(_collect_assets())
    data_files.extend(_collect_templates())

    # Incluir config.ini.example (el usuario debe copiar a config.ini)
    if CONFIG_EXAMPLE.exists():
        data_files.append((str(CONFIG_EXAMPLE), "."))

    # Incluir assets/styles.qss
    qss_path = ASSETS_DIR / "styles.qss"
    if qss_path.exists():
        data_files.append((str(qss_path), "assets"))

    # Flags de PyInstaller
    mode_flag = "--onefile" if args.onefile else "--onedir"
    flags = [
        sys.executable or "python",
        "-m",
        "PyInstaller",
        "--noconfirm",
        mode_flag,
        "--name",
        args.name,
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR}",
        "--log-level=INFO",
        "--windowed",  # Sin consola (GUI)
        "--optimize=2",
        "--noupx",
    ]
    if args.clean:
        flags.append("--clean")

    # --- Hidden imports ---
    for mod in HIDDEN_IMPORTS:
        flags.append(f"--hidden-import={mod}")

    # --- Data files ---
    for src, dst in data_files:
        flags.append(f"--add-data={src}{os.pathsep}{dst}")

    # --- Excluir modulos innecesarios ---
    EXCLUDES = [
        "tkinter",
        "matplotlib",
        "scipy",
        "PIL",
        "Pillow",
        "cv2",
        "numpy.testing",
        "pandas.testing",
        "setuptools",
        "pip",
        "IPython",
        "jupyter",
        "notebook",
        "PySide6.QtWebEngine",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebChannel",
        "PySide6.QtBluetooth",
        "PySide6.Qt3D*",
        "PySide6.QtGraphs",
        "PySide6.QtHelp",
        "PySide6.QtLocation",
        "PySide6.QtMultimedia",
        "PySide6.QtNfc",
        "PySide6.QtOpenGLWidgets",
        "PySide6.QtPositioning",
        "PySide6.QtQml",
        "PySide6.QtQuick",
        "PySide6.QtRemoteObjects",
        "PySide6.QtScxml",
        "PySide6.QtSensors",
        "PySide6.QtSerialPort",
        "PySide6.QtSpeech",
        "PySide6.QtStateMachine",
        "PySide6.QtTest",
        "PySide6.QtTextToSpeech",
        "PySide6.QtUiTools",
        "PySide6.QtWebSockets",
        "PySide6.QtXml",
        "PySide6.QtXmlPatterns",
        "tests",
        "docs",
        "rev",
    ]
    for excl in EXCLUDES:
        flags.append(f"--exclude-module={excl}")

    # --- Icono ---
    ico_path = ASSETS_DIR / "LogoDinamo.ico"
    if ico_path.exists():
        flags.append(f"--icon={ico_path}")
    else:
        png_path = ASSETS_DIR / "LogoDinamo.png"
        if png_path.exists():
            flags.append(f"--icon={png_path}")

    # --- Entry point ---
    flags.append(str(ENTRY_POINT))

    # Filtrar flags condicionales que quedaron vacios
    flags = [f for f in flags if f]

    print("=" * 60)
    print(f" BUILD: {args.name} v{APP_VERSION}")
    print(f" MODE: {'One-file' if args.onefile else 'Folder'}")
    print(f" HIDDEN IMPORTS: {len(HIDDEN_IMPORTS)}")
    print(f" DATA FILES: {len(data_files)}")
    print("=" * 60)
    print()

    cmd = " ".join(flags)
    print(f"Ejecutando:\n  {cmd}\n")

    result = subprocess.run(flags, cwd=PROJECT_DIR, capture_output=False)
    return result.returncode


def _make_postinstall_script(dist_path: Path, onefile: bool):
    """
    Crea un script .bat de post-instalacion para facilitar
    la configuracion inicial.
    """
    if onefile:
        exe_path = dist_path / f"{APP_NAME}.exe"
        bat_content = f"""@echo off
REM =============================================
REM  Dinamo Rent ERP -- Inicio Rapido
REM =============================================

echo.
echo  == Dinamo Rent ERP v{APP_VERSION} ==
echo  =================================
echo.

REM Verificar config.ini
IF NOT EXIST "%CD%\\config.ini" (
    echo  [ERROR] No se encontro config.ini
    echo  [ERROR] Copie config.ini.example a config.ini
    echo          y ajuste la configuracion de base de datos.
    echo.
    pause
    exit /b 1
)

echo  [OK] config.ini encontrado
echo.
echo  Iniciando aplicacion...
echo.
start "" "{exe_path}"
exit /b 0
"""
    else:
        exe_path = dist_path / APP_NAME / f"{APP_NAME}.exe"
        bat_content = f"""@echo off
REM =============================================
REM  Dinamo Rent ERP -- Inicio Rapido
REM =============================================

echo.
echo  == Dinamo Rent ERP v{APP_VERSION} ==
echo  =================================
echo.

REM Verificar config.ini
IF NOT EXIST "%CD%\\config.ini" (
    echo  [ERROR] No se encontro config.ini en la carpeta actual.
    echo  [ERROR] Copie config.ini.example a config.ini
    echo          y ajuste la configuracion de base de datos.
    echo.
    pause
    exit /b 1
)

echo  [OK] config.ini encontrado
echo.
echo  Iniciando aplicacion...
echo.
start "" "{exe_path}"
exit /b 0
"""

    bat_path = dist_path / "iniciar_dinamo.bat"
    bat_path.write_text(bat_content, encoding="utf-8")
    print(f"  OK - Script de inicio creado: {bat_path}")


def _make_spec_manual(dist_path: Path, onefile: bool):
    """Genera un archivo .spec editable como alternativa."""
    spec_path = PROJECT_DIR / "dinamo_rent.spec"

    # --- Preparar data files ---
    data_lines = []
    for src, dst in _collect_assets():
        data_lines.append(f"    ('{src}', '{dst}'),")
    for src, dst in _collect_templates():
        data_lines.append(f"    ('{src}', '{dst}'),")
    if CONFIG_EXAMPLE.exists():
        data_lines.append(f"    ('{CONFIG_EXAMPLE}', '.'),")
    data_str = "\n".join(data_lines)  # --- Hidden imports ---
    hidden_str = ",\n    ".join(f"'{m}'" for m in HIDDEN_IMPORTS)

    # --- Icono ---
    icon_path = ASSETS_DIR / "LogoDinamo.ico"
    icon_str = f"r'{icon_path}'" if icon_path.exists() else "None"

    # --- Construir contenido con Python plano ---
    lines = []
    lines.append("# -*- mode: python ; coding: utf-8 -*-")
    lines.append(f"# Dinamo Rent ERP v{APP_VERSION} -- PyInstaller Spec")
    lines.append("# Generado automaticamente por build_exe.py")
    lines.append("# Editar este archivo para personalizar la compilacion.")
    lines.append("")
    lines.append("import os")
    lines.append("import sys")
    lines.append("from pathlib import Path")
    lines.append("")
    lines.append("block_cipher = None")
    lines.append("")
    lines.append("a = Analysis(")
    lines.append("    ['main_qt.py'],")
    lines.append("    pathex=[],")
    lines.append("    binaries=[],")
    lines.append("    datas=[")
    lines.append(data_str)
    lines.append("    ],")
    lines.append("    hiddenimports=[")
    lines.append(f"    {hidden_str}")
    lines.append("    ],")
    lines.append("    hookspath=[],")
    lines.append("    hooksconfig={},")
    lines.append("    runtime_hooks=[],")
    lines.append("    excludes=[")
    lines.append("        'tkinter', 'matplotlib', 'scipy', 'PIL', 'Pillow',")
    lines.append("        'cv2', 'numpy.testing', 'pandas.testing',")
    lines.append("        'setuptools', 'pip',")
    lines.append("        'IPython', 'jupyter', 'notebook',")
    lines.append("        'PySide6.QtWebEngine*', 'PySide6.Qt3D*',")
    lines.append("        'PySide6.QtHelp', 'PySide6.QtLocation',")
    lines.append("        'PySide6.QtMultimedia*', 'PySide6.QtNfc',")
    lines.append("        'PySide6.QtQml', 'PySide6.QtQuick*',")
    lines.append("        'PySide6.QtRemoteObjects', 'PySide6.QtScxml',")
    lines.append("        'PySide6.QtSensors', 'PySide6.QtSerialPort',")
    lines.append("        'PySide6.QtSpeech', 'PySide6.QtStateMachine',")
    lines.append("        'PySide6.QtTest', 'PySide6.QtTextToSpeech',")
    lines.append("        'PySide6.QtUiTools', 'PySide6.QtWebSockets',")
    lines.append("        'PySide6.QtXml*', 'PySide6.QtBluetooth',")
    lines.append("        'tests', 'docs', 'rev',")
    lines.append("    ],")
    lines.append("    noarchive=False,")
    lines.append(")")
    lines.append("")
    lines.append("pyz = PYZ(a.pure)")
    lines.append("")

    if onefile:
        lines.append("exe = EXE(")
    else:
        lines.append("exe = EXE(")

    lines.append("    pyz,")
    lines.append("    a.scripts,")
    lines.append("    a.binaries,")
    lines.append("    a.datas,")
    lines.append("    [],")
    lines.append(f"    name='{APP_NAME}',")
    lines.append("    debug=False,")
    lines.append("    bootloader_ignore_signals=False,")
    lines.append("    strip=False,")
    lines.append("    upx=False,")
    lines.append("    upx_exclude=[],")
    lines.append("    runtime_tmpdir=None,")
    lines.append(f"    exclude_binaries={str(not onefile).lower()},")
    lines.append("    console=False,")
    lines.append(f"    disable_windowed_traceback={str(onefile).lower()},")
    lines.append("    argv_emulation=False,")
    lines.append("    target_arch=None,")
    lines.append("    codesign_identity=None,")
    lines.append("    enterprise_certificate=None,")
    lines.append("")
    lines.append("    # Icono")
    lines.append(f"    icon={icon_str},")
    lines.append("")
    lines.append("    # Metadatos (Windows)")
    lines.append(f"    version='{APP_VERSION}',")
    lines.append("    company_name='Corjar Computers',")
    lines.append("    file_description='Dinamo Rent ERP - Sistema de Gestion de Flota',")
    lines.append("    legal_copyright='(c) Corjar Computers',")
    lines.append(f"    product_name='{APP_NAME}',")
    lines.append(")")

    if not onefile:
        lines.append("")
        lines.append("coll = COLLECT(")
        lines.append("    exe,")
        lines.append("    a.binaries,")
        lines.append("    a.datas,")
        lines.append("    strip=False,")
        lines.append("    upx=False,")
        lines.append("    upx_exclude=[],")
        lines.append(f"    name='{APP_NAME}',")
        lines.append(")")

    lines.append("")
    spec_content = "\n".join(lines)

    spec_path.write_text(spec_content, encoding="utf-8")
    print(f"  [OK] Spec file generado: {spec_path}")
    return spec_path


def main():
    parser = argparse.ArgumentParser(
        description="Compila Dinamo Rent ERP a ejecutable con PyInstaller",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python build_exe.py                    # Build carpeta normal
  python build_exe.py --onefile          # Build .exe unico
  python build_exe.py --spec             # Solo genera .spec (no compila)
  python build_exe.py --clean --onefile  # Limpia y compila .exe unico
        """,
    )
    parser.add_argument(
        "--onefile", action="store_true", help="Generar un solo .exe en lugar de carpeta"
    )
    parser.add_argument(
        "--clean", action="store_true", help="Eliminar dist/ y build/ antes de compilar"
    )
    parser.add_argument(
        "--name", default=APP_NAME, help=f"Nombre del ejecutable (default: {APP_NAME})"
    )
    parser.add_argument(
        "--spec", action="store_true", help="Solo generar el archivo .spec (no compilar)"
    )

    args = parser.parse_args()

    print()
    print("  " + "=" * 55)
    print(f"  |  Dinamo Rent ERP  v{APP_VERSION}  Build Script  |")
    print("  " + "=" * 55)
    print()

    # --- Validacion previa ---
    if not (PROJECT_DIR / ENTRY_POINT).exists():
        print(f"  [ERROR] No se encuentra el punto de entrada: {ENTRY_POINT}")
        print("     Asegurate de ejecutar el script desde la raiz del proyecto.")
        sys.exit(1)

    if not ASSETS_DIR.exists():
        print("  ADVERTENCIA: No se encuentra el directorio assets/")
        print("     El ejecutable se generara sin recursos visuales.")

    # --- Clean ---
    if args.clean:
        for p in [DIST_DIR, BUILD_DIR, SPEC_FILE]:
            if p.exists():
                print(f"  Eliminando: {p}")
                if p.is_dir():
                    shutil.rmtree(p)
                else:
                    p.unlink()
        print("  OK - Limpieza completada")
        print()

    # --- Generar .spec ---
    if args.spec:
        _make_spec_manual(DIST_DIR, args.onefile)
        print()
        print("  [TIP] Para compilar manualmente:")
        print("     pyinstaller dinamo_rent.spec")
        print()
        return

    # --- Ejecutar PyInstaller ---
    retcode = _build_spec(args)

    if retcode == 0:
        print()
        print("=" * 70)
        print("  [OK] COMPILACION EXITOSA")
        print("=" * 70)
        print()

        if args.onefile:
            exe = DIST_DIR / f"{args.name}.exe"
            if exe.exists():
                size_mb = exe.stat().st_size / (1024 * 1024)
                print(f"  Ejecutable: {exe}")
                print(f"  Tamano: {size_mb:.1f} MB")
        else:
            exe = DIST_DIR / args.name / f"{args.name}.exe"
            if exe.exists():
                size_mb = sum(
                    f.stat().st_size for f in (DIST_DIR / args.name).rglob("*") if f.is_file()
                ) / (1024 * 1024)
                print(f"  Carpeta: {DIST_DIR / args.name}")
                print(f"  Tamano total: {size_mb:.1f} MB")

        # Crear script de inicio
        _make_postinstall_script(DIST_DIR, args.onefile)

        print()
        print("  PROXIMOS PASOS:")
        print("  1. Copiar config.ini.example a config.ini")
        print("  2. Configurar base de datos en config.ini")
        print(f"  3. Ejecutar: dist\\{args.name}\\{args.name}.exe")
        print("     o usar:    dist\\iniciar_dinamo.bat")
        print()
    else:
        print()
        print("=" * 70)
        print(f"  [ERROR] COMPILACION FALLIDA (codigo: {retcode})")
        print("=" * 70)
        print()
        print("  Posibles causas:")
        print("  - Falta alguna dependencia (pip install -r requirements.txt)")
        print("  - El enlace simbolico de PyInstaller no funciona")
        print("  - Espacio en disco insuficiente")
        print()
        print("  Soluciones:")
        print("  - python build_exe.py --spec   genera .spec para depurar")
        print("  - pyinstaller dinamo_rent.spec  compilar manual")
        print()

    sys.exit(retcode)


if __name__ == "__main__":
    main()
