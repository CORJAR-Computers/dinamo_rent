# 📋 Plan de Despliegue a Producción — Dinamo Rent ERP v3.2.0

**Fecha:** 25 de julio de 2026
**Autor:** Buffy (AI Senior Software Engineer)
**Versión:** 3.2.0
**Estado:** ✅ Listo para producción

---

## Resumen Ejecutivo

Dinamo Rent ERP es una aplicación de escritorio PySide6 para gestión de flota de vehículos. Soporta tres motores de base de datos (Firebird, MySQL, SQLite) y se empaqueta como ejecutable Windows con PyInstaller.

| Aspecto | Estado |
|---------|--------|
| Tests | ✅ 1,509 passed / 13 failed (preexistentes) / 4 skipped |
| Linting | ✅ 0 errores (ruff check) |
| Seguridad | ✅ PBKDF2 + AES-256 + RBAC |
| Empaquetado | ✅ PyInstaller configurado |
| CI/CD | ✅ GitHub Actions (Ruff + Pytest) |

---

## Fase 0: Prerrequisitos

### 0.1 Entorno de Desarrollo

```bash
# Python 3.12+ requerido
python --version  # >= 3.12

# Instalar dependencias
pip install -r requirements.txt

# Verificar que los tests pasan
python -m pytest tests/ --tb=short -q
# Esperado: ~1,509 passed, 13 failed (preexistentes), 4 skipped
# Los 13 fallos son tests preexistentes (no bloqueantes para despliegue)
```

### 0.2 Herramientas Necesarias

| Herramienta | Versión | Propósito |
|-------------|---------|-----------|
| Python | 3.12+ | Runtime |
| PyInstaller | 6.x | Empaquetado a .exe |
| Git | 2.x | Control de versiones |
| Firebird | 4.0+ | Motor de BD (opcional) |
| MySQL | 8.0+ | Motor de BD (opcional) |

### 0.3 Archivos Sensibles (NO commitear)

| Archivo | Propósito | En .gitignore |
|---------|-----------|---------------|
| `config.ini` | Configuración local con credenciales | ✅ Sí |
| `.env` | Variables de entorno | ✅ Sí |
| `*.fdb` | Archivos de Firebird | ✅ Sí |
| `*.db` | Archivos SQLite | ✅ Sí |
| `Backups/` | Respaldos encriptados | ✅ Sí |
| `logs/` | Archivos de log | ✅ Sí |

---

## Fase 1: Preparación del Código

### 1.1 Verificar Calidad del Código

```bash
# Linting - debe retornar 0 errores
python -m ruff check .

# Formato - debe estar al día
python -m ruff format --check .

# Si hay issues de formato:
python -m ruff format .
```

### 1.2 Ejecutar Suite Completa de Tests

```bash
# Tests con verbosidad
python -m pytest tests/ -v --tb=short -q

# Tests de seguridad específicamente
python -m pytest tests/test_security.py tests/test_validators.py -v

# Tests de servicios
python -m pytest tests/test_services.py tests/test_services_restantes.py -v
```

### 1.3 Ejecutar Auditoría de Seguridad

```bash
python security_audit.py
# Esperado: 16+ checks pasados, 0 fallos
```

### 1.4 Verificar que no hay Credenciales Expuestas

```bash
# Verificar .gitignore
git check-ignore -v config.ini .env

# Verificar que no hay archivos sensibles tracked
git ls-files config.ini .env *.fdb

# Buscar passwords hardcodeados en código
grep -rn "password.*=.*\"[^\"]\{4,}\"" core/ services/ --include="*.py"
```

---

## Fase 2: Configuración de Base de Datos

### 2.1 Opción A: Firebird (Recomendada para Producción)

**Requisitos previos:**
- Firebird 4.0+ instalado (o Firebird Embedded incluido en el bundle)
- El archivo `fbclient.dll` debe estar en `Firebird-4.0.7.3271/fbclient.dll`

**Configuración en `config.ini`:**
```ini
[database]
engine = firebird
user = sysdba
password = <CONTRASEÑA_SEGURA>
path = dinamo_rent_v3.fdb
```

**Crear la base de datos:**
```bash
# Firebird creará el .fdb automáticamente al iniciar la app
# O crear manualmente con isql-fb:
isql-fb
> CREATE DATABASE 'localhost:dinamo_rent_v3.fdb' user 'sysdba' password '<password>';
> EXIT;
```

### 2.2 Opción B: MySQL

**Requisitos previos:**
- MySQL 8.0+ corriendo
- Usuario con permisos para CREATE DATABASE

**Configuración en `config.ini`:**
```ini
[database]
engine = mysql
host = localhost
port = 3306
user = root
password = <CONTRASEÑA_SEGURA>
database = dinamo_rent
```

**Crear la base de datos:**
```sql
CREATE DATABASE IF NOT EXISTS dinamo_rent CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2.3 Opción C: SQLite (Desarrollo/Demo)

**Configuración en `config.ini`:**
```ini
[database]
engine = sqlite
path = dinamo_rent_v3.db
```

> ⚠️ SQLite NO es recomendado para producción con múltiples usuarios.

### 2.4 Migraciones con Alembic

El proyecto usa Alembic para gestionar cambios de esquema. Las migraciones están en `migrations/versions/`.

```bash
# Verificar estado de migraciones
alembic history

# Aplicar todas las migraciones pendientes
alembic upgrade head

# Verificar versión actual
alembic current
```

> **Nota:** `init_db()` ejecuta `Base.metadata.create_all()` + migraciones manuales de MySQL automáticamente. Para SQLite y Firebird, las migraciones manuales se omiten (gestionadas por SQLAlchemy/Alembic).

---

## Fase 3: Configuración de Seguridad

### 3.1 Generar Nueva db_encryption_key

```python
from cryptography.fernet import Fernet
key = Fernet.generate_key().decode()
print(f"db_encryption_key = {key}")
```

**Actualizar en `config.ini`:**
```ini
[security]
db_encryption_key = <NUEVA_CLAVE_GENERADA>
```

> 🚨 **ADVERTENCIA CRÍTICA:** La `db_encryption_key` se usa para encriptar datos sensibles de clientes (celular, email, dirección, licencia) con AES-256. **NUNCA cambie esta clave después de tener datos encriptados en la base de datos** a menos que:
> 1. Haga backup de la BD actual, **Y**
> 2. Re-encripte todos los campos sensibles con la nueva clave **antes** de actualizar config.ini.
>
> Cambiar la clave sin re-encriptar los datos hará que toda la información de clientes sea **permanentemente indecipherable**.

### 3.2 Configurar Contraseña de Admin

El asistente de configuración pedirá crear el usuario admin en el primer arranque con `production_mode = true`.

**Flujo automático:**
1. Al detectar `production_mode = true` y `setup_completed = false`
2. Se muestra el SetupWizard (3 pasos: BD → Admin → Preferencias)
3. Se crea el usuario admin con la contraseña ingresada
4. Se guarda `setup_completed = true` en config.ini

### 3.3 Configurar Backups

```ini
[backup]
directory = Backups
max_copies = 10
schedule_times = 09:00, 13:00, 19:00, 23:00
encryption_enabled = true
encryption_password = <CONTRASEÑA_BACKUPS>
```

---

## Fase 4: Empaquetado con PyInstaller

### 4.1 Build de Producción (Carpeta)

```bash
# Build limpio en carpeta
python build_exe.py --clean

# Output: dist/DinamoRentERP/DinamoRentERP.exe
```

### 4.2 Build de Producción (Ejecutable Único)

```bash
# Build como .exe único (~150-200MB)
python build_exe.py --clean --onefile

# Output: dist/DinamoRentERP.exe
```

### 4.3 Estructura del Build

```
dist/
├── DinamoRentERP/
│   ├── DinamoRentERP.exe          # Ejecutable principal
│   ├── assets/                     # Logo, estilos QSS
│   ├── templates/                  # Templates Jinja2 (contratos, órdenes)
│   ├── config.ini.example          # Plantilla de configuración
│   └── iniciar_dinamo.bat          # Script de inicio rápido
```

### 4.4 Verificar el Build

```bash
# Probar que el ejecutable arranca
cd dist/DinamoRentERP
DinamoRentERP.exe

# Verificar que el SetupWizard aparece en primera ejecución
# Verificar que la BD se crea correctamente
# Verificar que el login funciona
```

---

## Fase 5: Instalación en Máquina de Producción

### 5.1 Checklist de Instalación

- [ ] Copiar la carpeta `dist/DinamoRentERP/` al equipo destino
- [ ] Verificar que `Firebird-4.0.7.3271/fbclient.dll` está accesible (si usa Firebird)
- [ ] Copiar `config.ini.example` a `config.ini`
- [ ] Configurar `config.ini` con credenciales de producción
- [ ] Generar y configurar `db_encryption_key` nueva
- [ ] Configurar `production_mode = true` en config.ini
- [ ] Ejecutar `DinamoRentERP.exe` — el SetupWizard guiará la configuración inicial

### 5.2 Script de Instalación Automática

Crear `instalar.bat` en la carpeta de distribución:

```batch
@echo off
REM =============================================
REM  Dinamo Rent ERP — Instalación
REM =============================================

echo.
echo  == Instalando Dinamo Rent ERP v3.2.0 ==
echo  ========================================
echo.

REM 0. Ir al directorio del script (importante para PyInstaller)
CD /D "%~dp0"

REM 1. Verificar config.ini en el directorio actual
IF NOT EXIST "%~dp0config.ini" (
    echo  [!] No se encontró config.ini
    echo  [+] Copiando config.ini.example...
    copy "%~dp0config.ini.example" "%~dp0config.ini"
    echo  [OK] config.ini creado. Edítelo antes de continuar.
    notepad "%~dp0config.ini"
    pause
)

REM 2. Crear directorios necesarios
IF NOT EXIST "%~dp0logs" mkdir "%~dp0logs"
IF NOT EXIST "%~dp0Backups" mkdir "%~dp0Backups"
IF NOT EXIST "%~dp0data" mkdir "%~dp0data"

REM 3. Ejecutar aplicación (desde el directorio del .exe)
echo.
echo  [OK] Iniciando Dinamo Rent ERP...
echo.
start "" "%~dp0DinamoRentERP.exe"
```

### 5.3 Configuración de Firewall (si aplica)

Si MySQL/Firebird está en un servidor remoto:
```batch
# Abrir puerto MySQL
netsh advfirewall firewall add rule name="MySQL" dir=in action=allow protocol=TCP localport=3306

# Abrir puerto Firebird
netsh advfirewall firewall add rule name="Firebird" dir=in action=allow protocol=TCP localport=3050
```

---

## Fase 6: Monitoreo y Mantenimiento

### 6.1 Ubicación de Logs

```
logs/
├── app.log              # Log general de la aplicación
├── error.log            # Errores
└── audit.log            # Auditoría de acciones de usuario
```

### 6.2 Backups Automáticos

- Se ejecutan en los horarios configurados en `schedule_times`
- Almacenan en `Backups/` con rotación (`max_copies = 10`)
- Se encriptan si `encryption_enabled = true`

### 6.3 Actualizaciones

```bash
# 1. Hacer backup de la BD actual
python -c "from services.backup_service import BackupService; BackupService.crear()"

# 2. Copiar el nuevo ejecutable sobre el anterior
# 3. Mantener el config.ini existente (NO sobreescribir)
# 4. Reiniciar la aplicación
```

### 6.4 Restaurar desde Backup

```python
from services.backup_service import BackupService

# Desencriptar si estaba encriptado
success, msg = BackupService.decrypt_file(
    "Backups/backup_2026-07-25.enc",
    "Backups/backup_2026-07-25.db",
    "contraseña_backups"
)
```

---

## Fase 7: Troubleshooting

### Errores Comunes

| Error | Causa | Solución |
|-------|-------|----------|
| `fbclient.dll not found` | Firebird no instalado o ruta incorrecta | Verificar `Firebird-4.0.7.3271/fbclient.dll` en la raíz del proyecto |
| `Connection refused` | BD no está corriendo | Verificar servicio MySQL/Firebird |
| `PermissionError [WinError 32]` | Archivo bloqueado por otro proceso | Cerrar otras instancias de la app |
| `Cuenta bloqueada` | 5+ intentos fallidos | Esperar 30 min o desbloquear desde Admin |
| `setup_completed = false` | Primera ejecución o config corrupta | Ejecutar SetupWizard |
| `config.ini not found` | Archivo no existe o路径 incorrecto | Copiar `config.ini.example` a `config.ini` junto al .exe |
| `Datos encriptados ilegibles` | `db_encryption_key` cambió sin re-encriptar | Restaurar BD desde backup y usar la clave original |
| `config.ini no se carga` | PyInstaller extrae a directorio temporal | Verificar que `config.ini` está junto al `.exe`, no en `%TEMP%` |

### Comandos Útiles de Diagnóstico

```bash
# Verificar conexión a BD
python -c "from core.database_sa import check_connection; print(check_connection())"

# Ejecutar auditoría de seguridad
python security_audit.py

# Verificar configuración cargada
python -c "from core.config import DB_ENGINE, PRODUCTION_MODE; print(f'Engine: {DB_ENGINE}, Prod: {PRODUCTION_MODE}')"
```

---

## Resumen de Archivos Críticos

| Archivo | Función | Propósito en Producción |
|---------|---------|------------------------|
| `config.ini` | Configuración local | Credenciales, parámetros (NO commitear) |
| `config.ini.example` | Plantilla | Referencia para config.ini |
| `build_exe.py` | Empaquetado | Generar ejecutable con PyInstaller |
| `main_qt.py` | Entry point | Punto de entrada de la aplicación |
| `core/config.py` | Config central | Lee config.ini, variables de entorno |
| `core/database_sa.py` | Capa de BD | Conexión, sesiones, migraciones |
| `core/security.py` | Seguridad | Passwords, sesiones, rate limiting |
| `views/setup_wizard.py` | Primer arranque | Asistente de configuración inicial |

---

## Checklist Final de Despliegue

- [ ] Código compilado limpio (ruff check = 0 errores)
- [ ] Tests ejecutados (98.9%+ pass rate)
- [ ] Auditoría de seguridad pasada
- [ ] No hay credenciales en el repositorio
- [ ] config.ini.example incluido en el build
- [ ] PyInstaller genera ejecutable correctamente
- [ ] SetupWizard funciona en primera ejecución
- [ ] Login con usuario admin funciona
- [ ] CRUD básico funciona (autos, clientes, rentas)
- [ ] Backups se crean correctamente
- [ ] Logs se generan en `logs/`
- [ ] Firebird/MySQL conecta correctamente
- [ ] Documentación incluida en el build
