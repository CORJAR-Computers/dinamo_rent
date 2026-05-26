# 🚗 Dinamo Rent ERP - Sistema de Gestión de Flota

> Sistema de gestión de flota vehicular para Dinamo Rent a Car - Sincelejo, Colombia

[![CI — Ruff + Pytest](https://github.com/aleksei-corom/dinamo_rent/actions/workflows/ruff-lint.yml/badge.svg?branch=master)](https://github.com/aleksei-corom/dinamo_rent/actions/workflows/ruff-lint.yml)

---

## 📋 Configuración Rápida

### 1. Crear archivo de configuración
```bash
copy config.ini.example config.ini
```

### 2. Configurar base de datos
Editar `config.ini` y establecer la contraseña:
```ini
[database]
password = TuPasswordSeguro123!
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Ejecutar aplicación
```bash
python main_qt.py
```

---

## 📚 Documentación

| Documento | Propósito |
|-----------|-----------|
| **[CONFIGURACION.md](CONFIGURACION.md)** | 📋 Guía completa del sistema de configuración `config.ini` |
| **[SEGURIDAD.md](SEGURIDAD.md)** | 🔐 Medidas de seguridad implementadas |
| **[MIGRACION_CONFIGINI.md](MIGRACION_CONFIGINI.md)** | 🔄 Guía de migración a `config.ini` |
| **[QUICK_SECURITY_REFERENCE.md](QUICK_SECURITY_REFERENCE.md)** | ⚡ Referencia rápida de seguridad |

---

## 🆕 Novedades (v3.2.0)

### ✅ Sistema de Configuración Centralizada
- **Nuevo**: Archivo `config.ini` jerárquico y organizado por secciones
- **Mejor**: Tipos de datos nativos (int, bool, list)
- **Mejor**: Secciones temáticas claras (`[database]`, `[security]`, `[ui]`, etc.)
- **Mejor**: Validación automática de secciones requeridas

### ✅ Seguridad Reforzada
- Rate limiting y bloqueo automático de cuentas
- Validación de fortaleza de contraseñas
- Control de acceso por roles (RBAC) en servicios
- Encriptación de backups con AES-256
- Sanitización contra SQL injection y XSS

---

## 📂 Estructura del Proyecto

```
Dinamo_Rent/
├── config.ini              # Configuración local (NO commitear)
├── config.ini.example      # Plantilla para git (SÍ commitear)
├── main_qt.py              # Punto de entrada
├── core/                   # Núcleo del sistema
│   ├── app_config.py       # Gestor de configuración nueva
│   ├── config.py           # Variables de compatibilidad
│   ├── security.py         # Seguridad y autenticación
│   ├── rbac.py             # Control de acceso por roles
│   └── ...
├── services/               # Lógica de negocio
├── views/                  # Interfaz de usuario
└── repositories/           # Acceso a datos
```

---

## ⚙️ Configuración Detallada

Ver **[CONFIGURACION.md](CONFIGURACION.md)** para la guía completa.

### Migración desde `.env`
```bash
python migrate_env_to_ini.py
```

---

## 🔒 Seguridad

Ver **[SEGURIDAD.md](SEGURIDAD.md)** para la guía completa.

### Verificar Estado de Seguridad
```bash
python security_audit.py
```

---

## 📞 Soporte

- 📖 Revisar documentación en archivos `.md`
- 🔍 Ejecutar auditoría: `python security_audit.py`
- 📝 Revisar logs: `logs/dinamo_rent.log`

---

**Versión**: 3.2.0  
**Última actualización**: 15 de abril de 2026
