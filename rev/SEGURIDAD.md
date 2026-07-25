# Guía de Seguridad - Dinamo Rent ERP

## Resumen de Medidas de Seguridad Implementadas

Este documento describe todas las medidas de seguridad implementadas para proteger los datos y el código del sistema Dinamo Rent ERP.

---

## 🔐 1. Autenticación y Control de Acceso

### 1.1 Rate Limiting y Bloqueo de Cuentas
**Archivo**: `core/security.py`, `services/auth_service.py`

- **Bloqueo automático**: Después de **5 intentos fallidos**, la cuenta se bloquea por **30 minutos**
- **Rate limiting**: Máximo **10 intentos en 5 minutos**
- **Seguimiento en memoria**: Todos los intentos se registran con timestamp
- **Desbloqueo manual**: Solo administradores pueden desbloquear cuentas

**Configuración**:
```python
MAX_LOGIN_ATTEMPTS = 5  # Intentos antes de bloqueo
ACCOUNT_LOCKOUT_DURATION = 1800  # 30 minutos
LOGIN_RATE_LIMIT_WINDOW = 300  # 5 minutos
MAX_LOGIN_ATTEMPTS_IN_WINDOW = 10
```

### 1.2 Validación de Fortaleza de Contraseña
**Archivo**: `core/security.py`

Todas las contraseñas deben cumplir:
- ✅ Mínimo **8 caracteres**
- ✅ Máximo **128 caracteres**
- ✅ Al menos una **letra mayúscula**
- ✅ Al menos una **letra minúscula**
- ✅ Al menos un **número**
- ✅ Al menos un **carácter especial** (!@#$%^&*(),.?":{}|<>)

### 1.3 Hash de Contraseñas
- **Algoritmo**: PBKDF2-HMAC-SHA256
- **Iteraciones**: 100,000
- **Salt**: 16 bytes aleatorios
- **Protección timing attacks**: `secrets.compare_digest()`

### 1.4 Control de Acceso Basado en Roles (RBAC)
**Archivo**: `core/rbac.py`

Decoradores para proteger funciones a nivel de servicio:

```python
@require_role('Administrador', 'Supervisor')
def generar_informe(session_id, ...):
    ...

@require_active_session
def obtener_datos(session_id, ...):
    ...
```

**Roles implementados**:
- `Administrador`: Acceso completo
- `Supervisor`: Informes financieros
- `Operador`: Operaciones diarias
- `Mecánico`: Mantenimiento de vehículos

---

## 🛡️ 2. Protección de Datos

### 2.1 Encriptación de Backups
**Archivo**: `services/backup_service.py`

- **Algoritmo**: AES-256 (Fernet)
- **Derivación de clave**: PBKDF2-HMAC-SHA256 (100,000 iteraciones)
- **Salt**: 16 bytes aleatorios por archivo
- **Formato**: `[salt: 16 bytes] + [datos encriptados]`

**Uso**:
```python
# Crear backup encriptado
BackupService.crear(encrypt=True, encryption_password="mi_password")

# Desencriptar backup
BackupService.decrypt_file(
    encrypted_path="backup.sql.enc", output_path="backup.sql", password="mi_password"
)
```

### 2.2 Encriptación de Archivos Sensibles
**Archivo**: `core/security_utils.py`

Encriptar archivos .env, configuraciones, etc.:

```python
from core.security_utils import FileEncryptor

# Encriptar
FileEncryptor.encrypt_file(file_path=".env", password="password_seguro", output_path=".env.enc")

# Desencriptar
FileEncryptor.decrypt_file(
    encrypted_path=".env.enc", password="password_seguro", output_path=".env"
)
```

### 2.3 Sanitización de Entradas
**Archivo**: `core/security.py`, `core/validators.py`

Protección contra:
- ✅ **SQL Injection**: Escapar comillas, detectar patrones peligrosos
- ✅ **XSS (Cross-Site Scripting)**: Bloquear scripts, event handlers
- ✅ **Null Byte Injection**: Eliminar caracteres nulos
- ✅ **Buffer Overflow**: Limitar longitud máxima

**Funciones disponibles**:
```python
from core.security import SecurityManager
from core.validators import sanitize_for_sql, validate_no_xss

# Sanitización general
SecurityManager.sanitize_input(user_input, max_length=500)

# Sanitización SQL
sanitize_for_sql(user_input)

# Validación XSS
validate_no_xss(user_input)
```

---

## 📋 3. Auditoría y Logging

### 3.1 Audit Trail Mejorado
**Archivo**: `core/logger.py`

Todos los eventos de seguridad se registran en `logs/audit.log`:
- ✅ Logins exitosos y fallidos
- ✅ Cuentas bloqueadas
- ✅ Accesos denegados
- ✅ Creación/eliminación de usuarios
- ✅ Cambios críticos en datos

### 3.2 Auditoría de Seguridad Automatizada
**Archivo**: `security_audit.py`

Script para verificar el estado de seguridad:

```bash
python security_audit.py
```

**Verifica**:
- Archivo .env protegido
- Gitignore configurado correctamente
- Contraseñas seguras
- Dependencias instaladas
- Backups encriptados
- Logging activo

---

## 🔑 4. Gestión de Credenciales

### 4.1 Archivo .env Seguro
**Recomendaciones**:

1. **Nunca commitear** el archivo .env al repositorio
2. **Contraseña de base de datos**:
   ```env
   DINAMO_DB_PASSWORD=TuPasswordSeguro123!
   ```
3. **Validar regularmente**:
   ```python
   from core.security_utils import SecureEnvManager

   issues = SecureEnvManager.validate_env_security()
   ```

### 4.2 Eliminación Segura de Archivos
```python
from core.security_utils import SecureEnvManager

# Sobrescribir 3 veces antes de eliminar
SecureEnvManager.secure_delete_file("archivo_sensible.db", passes=3)
```

### 4.3 Credenciales en Memoria
```python
from core.security_utils import CredentialManager

# Almacenar temporalmente
CredentialManager.store("database", "user", "password")

# Obtener
creds = CredentialManager.get("database")

# Limpiar al salir
CredentialManager.clear()
```

---

## 📦 5. Dependencias de Seguridad

### 5.1 Librerías Instaladas
**Archivo**: `requirements.txt`

```
cryptography>=41.0.0  # Encriptación AES-256
```

### 5.2 Instalar Dependencias
```bash
pip install -r requirements.txt
```

---

## 🚀 6. Buenas Prácticas Implementadas

### 6.1 Protección de Archivos Sensibles
**Archivo**: `gitignore` (renombrar a `.gitignore`)

Archivos ignorados:
- `.env`, `.env.local`, `.env.production`
- `Backups/` (contiene dumps de BD)
- `logs/` (contiene audit logs)
- `*.db` (archivos SQLite)
- `.idea/`, `venv/`, `__pycache__/`

### 6.2 Sesiones Seguras
- **Token**: `secrets.token_urlsafe(32)` (256 bits)
- **Timeout**: 1 hora de inactividad
- **Purga automática**: Sesiones expiradas se eliminan

### 6.3 Transacciones Atómicas
**Archivo**: `core/unit_of_work.py`

Operaciones críticas usan Unit of Work para garantizar atomicidad:
- Creación de rentas
- Cierre de rentas
- Registro de pagos
- Mantenimientos

---

## ⚠️ 7. Recomendaciones Adicionales

### 7.1 Base de Datos MySQL

**Cambiar contraseña por defecto**:
```sql
ALTER USER 'root'@'localhost' IDENTIFIED BY 'NuevoPasswordSeguro123!';
FLUSH PRIVILEGES;
```

**Actualizar .env**:
```env
DINAMO_DB_PASSWORD=NuevoPasswordSeguro123!
```

### 7.2 Contraseña de Administrador por Defecto

**IMPORTANTE**: Cambiar inmediatamente después del primer uso:
```python
# Credenciales por defecto (en main_qt.py):
# Usuario: admin
# Contraseña: admin123  ← CAMBIAR INMEDIATAMENTE
```

### 7.3 Backups Regulares

**Automatizar backups encriptados**:
```python
from services.backup_service import BackupService

# Backup con encriptación
success, msg = BackupService.crear(
    encrypt=True, encryption_password=f"Backup_{datetime.now().strftime('%Y%m')}"
)
```

### 7.4 Rotación de Contraseñas

**Política recomendada**:
- 🔑 Contraseñas de usuarios: cada **90 días**
- 🔑 Contraseña de BD: cada **180 días**
- 🔑 Contraseñas de backups: cada **30 días**

---

## 🔍 8. Verificación de Seguridad

### 8.1 Ejecutar Auditoría
```bash
python security_audit.py
```

### 8.2 Verificar Dependencias
```bash
pip list | grep cryptography
```

### 8.3 Validar Contraseñas
```python
from core.security import SecurityManager

errors = SecurityManager.validate_password_strength("MiPassword123!")
if errors:
    print("Contraseña débil:", errors)
else:
    print("Contraseña segura ✓")
```

---

## 📞 9. Contacto y Soporte

Para problemas de seguridad o dudas:
1. Revisar logs en `logs/audit.log`
2. Ejecutar `security_audit.py`
3. Contactar al administrador del sistema

---

## 📝 10. Historial de Cambios

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 3.2.0 | 2026-04-15 | - Rate limiting y bloqueo de cuentas<br>- RBAC a nivel de servicios<br>- Encriptación de backups<br>- Sanitización de entradas<br>- Auditoría de seguridad |

---

## ✅ Checklist de Seguridad

- [x] Rate limiting de login implementado
- [x] Bloqueo automático de cuentas (5 intentos)
- [x] Validación de fortaleza de contraseña
- [x] Hash PBKDF2 con 100,000 iteraciones
- [x] RBAC en capa de servicios
- [x] Encriptación de backups (AES-256)
- [x] Sanitización contra SQL injection
- [x] Sanitización contra XSS
- [x] Audit trail mejorado
- [x] Script de auditoría de seguridad
- [x] Gestión segura de credenciales
- [x] Eliminación segura de archivos
- [ ] Cambiar contraseña de admin por defecto
- [ ] Configurar contraseña MySQL fuerte
- [ ] Programar backups automáticos encriptados
- [ ] Renombrar `gitignore` a `.gitignore`

---

**Última actualización**: 15 de abril de 2026  
**Versión**: 3.2.0
