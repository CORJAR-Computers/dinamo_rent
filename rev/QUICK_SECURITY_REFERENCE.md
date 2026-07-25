# 🔐 Quick Reference - Seguridad Dinamo Rent ERP

## Comandos Rápidos

### Verificar Estado de Seguridad
```bash
python security_audit.py
```

### Instalar Dependencias de Seguridad
```bash
pip install cryptography
```

---

## Uso de Funciones de Seguridad

### 1. Validar Contraseña
```python
from core.security import SecurityManager

errors = SecurityManager.validate_password_strength("MiPass123!")
if not errors:
    print("✓ Contraseña segura")
else:
    print("Errores:", errors)
```

### 2. Encriptar Backup
```python
from services.backup_service import BackupService

# Crear backup encriptado
success, msg = BackupService.crear(encrypt=True)
```

### 3. Desencriptar Backup
```python
success, msg = BackupService.decrypt_file(
    encrypted_path="Backups/backup.sql.enc",
    output_path="Backups/backup.sql",
    password="mi_password",
)
```

### 4. Sanitizar Input
```python
from core.security import SecurityManager

# Sanitización general
clean = SecurityManager.sanitize_input(user_input, max_length=500)
```

### 5. Verificar Permisos RBAC
```python
from core.rbac import PermissionChecker

# Verificar acceso a informes
if PermissionChecker.can_access_informes(session_id):
    # Generar informe
    pass

# Verificar gestión de usuarios
if PermissionChecker.can_manage_users(session_id):
    # Crear/editar usuario
    pass
```

### 6. Encriptar Archivo .env
```python
from core.security_utils import FileEncryptor

# Encriptar
FileEncryptor.encrypt_file(file_path=".env", password="mi_password_seguro", output_path=".env.enc")

# Desencriptar
FileEncryptor.decrypt_file(
    encrypted_path=".env.enc", password="mi_password_seguro", output_path=".env"
)
```

### 7. Validar Seguridad de .env
```python
from core.security_utils import SecureEnvManager

issues = SecureEnvManager.validate_env_security()
for issue in issues:
    print("⚠️", issue)
```

### 8. Eliminar Archivo Seguro
```python
from core.security_utils import SecureEnvManager

# Sobrescribir 3 veces antes de eliminar
SecureEnvManager.secure_delete_file("archivo_sensible.db", passes=3)
```

---

## Configuración de Seguridad

### Rate Limiting (config.py)
```python
MAX_LOGIN_ATTEMPTS = 5  # Intentos antes de bloqueo
ACCOUNT_LOCKOUT_DURATION = 1800  # 30 minutos
LOGIN_RATE_LIMIT_WINDOW = 300  # 5 minutos ventana
MAX_LOGIN_ATTEMPTS_IN_WINDOW = 10  # Máx en ventana
```

### Roles con Acceso (config.py)
```python
ROLES_CON_INFORMES = {"Administrador", "Supervisor"}
ROLES_CON_USUARIOS = {"Administrador"}
```

---

## Solución de Problemas

### Error: Cuenta Bloqueada
```python
from services.auth_service import AuthService

# Desbloquear cuenta (solo admins)
AuthService.unlock_account("usuario")
```

### Error: cryptography no instalado
```bash
pip install cryptography>=41.0.0
```

### Validar Contraseña de MySQL
```python
from core.security_utils import SecureEnvManager

issues = SecureEnvManager.validate_env_security()
# Buscar: "Contraseña vacía" o "Contraseña muy corta"
```

---

## Archivos de Seguridad

| Archivo | Propósito |
|---------|-----------|
| `core/security.py` | Hash, sanitización, login tracker |
| `core/rbac.py` | Control de acceso por roles |
| `core/security_utils.py` | Encriptación, gestión credenciales |
| `core/validators.py` | Sanitización SQL/XSS |
| `services/auth_service.py` | Login con rate limiting |
| `services/backup_service.py` | Backups encriptados |
| `services/usuario_service.py` | Gestión usuarios con RBAC |
| `services/informe_service.py` | Informes protegidos |
| `security_audit.py` | Auditoría automatizada |
| `SEGURIDAD.md` | Guía completa |
| `.env.example` | Plantilla segura |

---

## Checklist de Seguridad Diario

- [ ] Verificar logs de auditoría: `logs/audit.log`
- [ ] Revisar intentos fallidos de login
- [ ] Verificar backups creados
- [ ] Ejecutar `security_audit.py` semanalmente

---

## Emergencias

### Base de Datos Comprometida
1. Cambiar contraseña de MySQL inmediatamente
2. Actualizar `.env`
3. Forzar cambio de contraseñas de usuarios
4. Revisar `logs/audit.log`

### Acceso No Autorizado
1. Revisar `logs/audit.log` para rastrear acceso
2. Bloquear cuentas comprometidas
3. Cambiar todas las contraseñas
4. Notificar al administrador

---

**Última actualización**: 15/04/2026  
**Versión**: 3.2.0
