# 📋 Guía de Configuración - Dinamo Rent ERP

## 🎯 Nuevo Sistema de Configuración Centralizada

La aplicación ahora utiliza un archivo **`config.ini`** centralizado en lugar de múltiples variables de entorno `.env`.

---

## 📂 Estructura del Archivo `config.ini`

El archivo está organizado en **secciones temáticas**:

### 1. `[database]` — Base de Datos
```ini
[database]
engine = mysql
host = localhost
port = 3306
user = root
password = TuPasswordSeguro123!
database = dinamo_rent

# Pool de conexiones (MySQL)
pool_size = 10
pool_max_overflow = 20
pool_pre_ping = true
```

### 2. `[security]` — Seguridad
```ini
[security]
hash_algorithm = sha256
hash_iterations = 100000
session_timeout = 3600
max_login_attempts = 5
account_lockout_duration = 1800
```

### 3. `[backup]` — Backups
```ini
[backup]
directory = Backups
max_copies = 10
schedule_times = 09:00, 13:00, 19:00, 23:00
encryption_enabled = true
```

### 4. `[logging]` — Logs
```ini
[logging]
directory = logs
max_size_mb = 5
backup_count = 5
level = INFO
audit_enabled = true
```

### 5. `[application]` — General
```ini
[application]
name = Dinamo Rent ERP
version = 3.2.0
language = es
timezone = America/Bogota
```

### 6. `[ui]` — Interfaz de Usuario
```ini
[ui]
color_primario = #004aad
font_family = Segoe UI
font_size = 10
window_width = 1366
window_height = 768
```

### 7. `[business]` — Reglas de Negocio
```ini
[business]
alert_soat_days = 15
roles_con_informes = Administrador, Supervisor
tipos_auto = Automóvil, Camioneta, Van, Lujo, Moto
```

### 8. `[email]` — Correo Electrónico (Opcional)
```ini
[email]
enabled = false
smtp_server = smtp.gmail.com
smtp_port = 587
```

### 9. `[whatsapp]` — WhatsApp
```ini
[whatsapp]
enabled = true
base_url = https://wa.me/
```

### 10. `[reports]` — Reportes
```ini
[reports]
pdf_engine = weasyprint
currency_symbol = $
tax_percentage = 19
```

---

## 🚀 Configuración Rápida

### Paso 1: Crear `config.ini` desde la plantilla
```bash
# Copiar el archivo de ejemplo
copy config.ini.example config.ini
```

### Paso 2: Configurar contraseñas
Editar `config.ini` y establecer:

```ini
[database]
password = TuPasswordSeguro123!
```

### Paso 3: ¡Listo!
La aplicación leerá automáticamente la configuración al iniciar.

---

## 🔧 Uso en Código

### Acceso Básico
```python
from core.app_config import config

# Obtener valor como string
db_host = config.get('database', 'host')

# Obtener como entero
db_port = config.getint('database', 'port')

# Obtener como booleano
audit_enabled = config.getboolean('logging', 'audit_enabled')

# Obtener lista separada por comas
roles = config.getlist('business', 'roles_con_informes')
```

### Accesos Directos (Recomendado)
```python
from core.app_config import config

# Configuración de base de datos
db_config = config.get_database_config()
print(db_config['host'])
print(db_config['port'])

# Configuración de seguridad
sec_config = config.get_security_config()
print(sec_config['max_login_attempts'])

# Configuración de backups
backup_config = config.get_backup_config()
print(backup_config['encryption_enabled'])

# Configuración de UI
ui_config = config.get_ui_config()
print(ui_config['color_primario'])

# Configuración de negocio
business_config = config.get_business_config()
print(business_config['alert_soat_days'])
```

### Modificar Configuración en Runtime
```python
from core.app_config import config

# Cambiar valor
config.set('database', 'host', '192.168.1.100')

# Recargar desde archivo
config.reload()

# Guardar cambios al archivo
config.save()
```

---

## 🔄 Migración desde `.env`

### Opción 1: Script Automático
```bash
python migrate_env_to_ini.py
```

El script:
1. ✅ Lee el archivo `.env` existente
2. ✅ Migra los valores a `config.ini`
3. ✅ Mantiene el formato correcto

### Opción 2: Manual
1. Abrir `.env` y `config.ini` lado a lado
2. Copiar valores manualmente:

| Variable `.env` | Sección `[ini]` | Clave `ini` |
|-----------------|-----------------|-------------|
| `DINAMO_DB_ENGINE` | `[database]` | `engine` |
| `DINAMO_DB_HOST` | `[database]` | `host` |
| `DINAMO_DB_PORT` | `[database]` | `port` |
| `DINAMO_DB_USER` | `[database]` | `user` |
| `DINAMO_DB_PASSWORD` | `[database]` | `password` |
| `DINAMO_DB_NAME` | `[database]` | `database` |

---

## 🔒 Seguridad

### Archivos a NO Commitear
```bash
# Agregar a gitignore
config.ini          # Contiene contraseñas reales
.env                # Legacy (si aún existe)
```

### Archivos a SÍ Commitear
```bash
# Estos SÍ van al repositorio
config.ini.example  # Plantilla sin contraseñas
gitignore          # Reglas de exclusión
```

### Actualizar `.gitignore`
El archivo `.gitignore` ya está configurado correctamente:
```gitignore
# Configuración con contraseñas
config.ini
!config.ini.example
```

---

## 📊 Comparación: `.env` vs `config.ini`

| Característica | `.env` | `config.ini` |
|----------------|--------|--------------|
| **Estructura** | Plano | Jerárquico con secciones |
| **Tipos de datos** | Solo strings | Strings, ints, floats, bools, lists |
| **Validación** | Manual | Nativa con `configparser` |
| **Comentarios** | `#` | `#` o `;` |
| **Valores por defecto** | No nativos | Nativos |
| **Organización** | Difícil con muchas variables | Secciones claras |
| **Uso en código** | `os.getenv()` | `config.get()` typed |
| **Ideal para** | Apps web, cloud | Apps desktop, Windows |

---

## 🎨 Personalización

### Cambiar Colores de la UI
```ini
[ui]
color_primario = #ff5722
color_fondo = #fafafa
font_family = Roboto
font_size = 11
```

### Agregar Nuevos Roles
```ini
[business]
roles_con_informes = Administrador, Supervisor, Auditor
```

### Configurar Alertas Personalizadas
```ini
[business]
alert_soat_days = 30
alert_tecno_mecanica_days = 30
km_alert_aceite = 1000
```

### Configurar Backup Personalizado
```ini
[backup]
schedule_times = 08:00, 14:00, 20:00
max_copies = 20
encryption_enabled = true
```

---

## 🐛 Solución de Problemas

### Error: "No se encontró config.ini"
```bash
# Copiar desde el ejemplo
copy config.ini.example config.ini
```

### Error: "Sección requerida no encontrada"
Verificar que existan las secciones obligatorias:
- `[database]`
- `[security]`
- `[application]`

### La configuración no se actualiza
```python
# Recargar configuración en runtime
from core.app_config import reload_config
reload_config()
```

### Migrar valores antiguos
```bash
# Ejecutar script de migración
python migrate_env_to_ini.py
```

---

## 📚 Referencia de Secciones

| Sección | Propósito | Obligatoria |
|---------|-----------|-------------|
| `[database]` | Conexión a BD | ✅ Sí |
| `[security]` | Hash, sesiones, login | ✅ Sí |
| `[backup]` | Respaldos automáticos | No |
| `[logging]` | Logs y auditoría | No |
| `[application]` | Info general | ✅ Sí |
| `[ui]` | Colores, fuentes, ventanas | No |
| `[business]` | Reglas de negocio | No |
| `[email]` | Envío de correos | No |
| `[whatsapp]` | Integración WhatsApp | No |
| `[reports]` | PDFs y Excel | No |

---

## ✅ Checklist de Configuración

- [ ] Crear `config.ini` desde `config.ini.example`
- [ ] Configurar contraseña de base de datos
- [ ] Verificar que `.gitignore` excluya `config.ini`
- [ ] Ejecutar `python migrate_env_to_ini.py` (si viene de `.env`)
- [ ] Probar que la aplicación inicia correctamente
- [ ] Verificar logs en `logs/dinamo_rent.log`

---

## 📞 Soporte

Para dudas o problemas:
1. Revisar esta documentación
2. Verificar que `config.ini` tenga la sintaxis correcta
3. Revisar logs en `logs/dinamo_rent.log`
4. Contactar al administrador del sistema

---

**Última actualización**: 15 de abril de 2026  
**Versión**: 3.2.0
