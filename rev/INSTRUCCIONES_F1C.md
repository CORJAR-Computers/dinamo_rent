# INSTRUCCIONES F1C — Reestructuración del Módulo de Repositorios

## Resumen

F1C separa el archivo monolítico `repositories_sa.py` (~631 líneas) en **13 archivos individuales**, cada uno con un solo repositorio. Se mantiene compatibilidad total con los servicios existentes mediante re-exportación.

## Cambios Realizados

### 1. Archivos Nuevos (14 archivos)

| Archivo | Contenido | Líneas aprox. |
|---------|-----------|---------------|
| `repositories/__init__.py` | Importa y expone los 12 repositorios + BaseRepositorySA | ~55 |
| `repositories/base_repository_sa.py` | Clase base compartida con imports comunes | ~40 |
| `repositories/auto_repository_sa.py` | AutoRepositorySA (6 métodos) | ~180 |
| `repositories/cliente_repository_sa.py` | ClienteRepositorySA (4 métodos) | ~110 |
| `repositories/renta_repository_sa.py` | RentaRepositorySA (7 métodos) | ~210 |
| `repositories/usuario_repository_sa.py` | UsuarioRepositorySA (6 métodos) | ~120 |
| `repositories/reserva_repository_sa.py` | ReservaRepositorySA (5 métodos) | ~110 |
| `repositories/mantenimiento_repository_sa.py` | MantenimientoRepositorySA (4 métodos) | ~85 |
| `repositories/comparendo_repository_sa.py` | ComparendoRepositorySA (4 métodos) | ~85 |
| `repositories/pago_repository_sa.py` | PagoRepositorySA (3 métodos) | ~65 |
| `repositories/gasto_repository_sa.py` | GastoRepositorySA (4 métodos) | ~70 |
| `repositories/inspeccion_repository_sa.py` | InspeccionRepositorySA (3 métodos) | ~60 |
| `repositories/alerta_repository_sa.py` | AlertaRepositorySA (3 métodos) | ~85 |
| `repositories/informe_repository_sa.py` | InformeRepositorySA (4 métodos) | ~100 |

### 2. Archivos Modificados (2 archivos)

#### `repositories/repositories_sa.py`
**Antes**: 631 líneas con toda la lógica de 8 repositorios inline.
**Después**: ~40 líneas con re-exportación desde módulos individuales.

Todos los imports existentes siguen funcionando:
```python
from repositories.repositories_sa import AutoRepositorySA  # ← Sigue funcionando
```

#### `core/schemas.py`
Se agregaron campos identificadores a los schemas de actualización:

| Schema | Campo agregado | Tipo | Descripción |
|--------|---------------|------|-------------|
| `AutoUpdate` | `placa` | `str` (requerido) | Identifica el vehículo a actualizar |
| `ClienteUpdate` | `id` | `int` (requerido) | Identifica el cliente a actualizar |
| `UsuarioUpdate` | `username` | `str` (requerido) | Identifica el usuario a actualizar |

**Justificación**: Los servicios (`auto_service.py`, `cliente_service.py`, `usuario_service.py`) ya creaban instancias de estos schemas con el campo identificador (`AutoUpdate(placa=placa, ...)`) pero Pydantic v2 rechazaba campos extra por defecto. Ahora los schemas son auto-contenidos.

### 3. Archivo Nuevo: `core/database_sa.py`

Versión limpia del módulo de base de datos:
- `get_session()` — Context manager de sesión (commit/rollback/close automático)
- `SessionLocal` — Fábrica de sesiones para uso manual
- `init_db()` — Creación de tablas (solo desarrollo/testing)
- `engine` — SQLAlchemy engine configurado

**Código muerto eliminado**: imports no utilizados, configuraciones legacy, funciones duplicadas.

---

## Repositorios Nuevos (antes no existían)

### AutoRepositorySA
Los servicios ya lo importaban pero el archivo no existía. Métodos implementados:

| Método | Usado por |
|--------|-----------|
| `obtener_todos()` | `dashboard_service`, `financial_service` |
| `obtener_disponibles()` | `auto_service` |
| `obtener_por_placa(placa)` | `auto_service`, `renta_service` |
| `existe(placa)` | `auto_service` |
| `insertar(datos)` | `auto_service` |
| `actualizar(datos)` | `auto_service` |
| `cambiar_estado(placa, estado, kilometraje)` | `renta_service`, `mantenimiento_service` |
| `obtener_alertas_flota()` | `auto_service` |

### ClienteRepositorySA
| Método | Usado por |
|--------|-----------|
| `buscar(termino)` | `cliente_service` |
| `obtener_por_id(id)` | `cliente_service` |
| `insertar(datos)` | `cliente_service` |
| `actualizar(datos)` | `cliente_service` |

### RentaRepositorySA
| Método | Usado por |
|--------|-----------|
| `insertar(datos)` | `renta_service` |
| `obtener_por_id(id)` | `renta_service` |
| `obtener_activas()` | `renta_service`, `dashboard_service` |
| `cerrar_renta(id, datos_cierre)` | `renta_service` |
| `extender(id, fecha, hora, dias, total, saldo)` | `renta_service` |
| `actualizar_placa(id, placa_nueva, nota)` | `renta_service` |
| `obtener_datos_documento(id)` | `renta_service` |
| `obtener_para_calendario(mes, anio)` | `renta_service` |

### UsuarioRepositorySA
| Método | Usado por |
|--------|-----------|
| `obtener_todos()` | `usuario_service` |
| `obtener_por_username(username)` | `usuario_service`, `auth_service` |
| `insertar(datos)` | `usuario_service` |
| `actualizar(datos)` | `usuario_service` |
| `eliminar(username)` | `usuario_service` |
| `registrar_acceso(username)` | `auth_service` |

---

## Pasos de Integración

### 1. Reemplazar archivos existentes

```bash
# En el directorio raíz del proyecto:

# 1. Backup del archivo original
cp repositories/repositories_sa.py repositories/repositories_sa.py.bak

# 2. Copiar los archivos nuevos de repositorios
cp download/repositories/__init__.py repositories/__init__.py
cp download/repositories/base_repository_sa.py repositories/base_repository_sa.py
cp download/repositories/auto_repository_sa.py repositories/auto_repository_sa.py
cp download/repositories/cliente_repository_sa.py repositories/cliente_repository_sa.py
cp download/repositories/renta_repository_sa.py repositories/renta_repository_sa.py
cp download/repositories/usuario_repository_sa.py repositories/usuario_repository_sa.py
cp download/repositories/reserva_repository_sa.py repositories/reserva_repository_sa.py
cp download/repositories/mantenimiento_repository_sa.py repositories/mantenimiento_repository_sa.py
cp download/repositories/comparendo_repository_sa.py repositories/comparendo_repository_sa.py
cp download/repositories/pago_repository_sa.py repositories/pago_repository_sa.py
cp download/repositories/gasto_repository_sa.py repositories/gasto_repository_sa.py
cp download/repositories/inspeccion_repository_sa.py repositories/inspeccion_repository_sa.py
cp download/repositories/alerta_repository_sa.py repositories/alerta_repository_sa.py
cp download/repositories/informe_repository_sa.py repositories/informe_repository_sa.py

# 3. Reemplazar repositories_sa.py con la versión thin wrapper
cp download/repositories/repositories_sa.py repositories/repositories_sa.py

# 4. Actualizar schemas
cp download/core/schemas.py core/schemas.py

# 5. Actualizar/reemplazar database_sa.py
cp download/core/database_sa.py core/database_sa.py
```

### 2. Verificar que no hay imports rotos

```bash
# Desde la raíz del proyecto:
python -c "
from repositories.repositories_sa import (
    AutoRepositorySA, ClienteRepositorySA, RentaRepositorySA,
    UsuarioRepositorySA, ReservaRepositorySA, MantenimientoRepositorySA,
    ComparendoRepositorySA, PagoRepositorySA, GastoRepositorySA,
    InspeccionRepositorySA, AlertaRepositorySA, InformeRepositorySA,
)
print('Todos los imports desde repositories_sa OK')
"

python -c "
from repositories import AutoRepositorySA, ClienteRepositorySA
print('Imports desde __init__.py OK')
"
```

### 3. Verificar schemas actualizados

```bash
python -c "
from core.schemas import AutoUpdate, ClienteUpdate, UsuarioUpdate

# AutoUpdate debe aceptar placa
au = AutoUpdate(placa='ABC123')
print(f'AutoUpdate.placa = {au.placa}')

# ClienteUpdate debe aceptar id
cu = ClienteUpdate(id=1)
print(f'ClienteUpdate.id = {cu.id}')

# UsuarioUpdate debe aceptar username
uu = UsuarioUpdate(username='test')
print(f'UsuarioUpdate.username = {uu.username}')

print('Schemas OK')
"
```

### 4. Ejecutar la aplicación

Iniciar la aplicación y verificar las funcionalidades principales:
- [ ] Login de usuario
- [ ] Listar vehículos
- [ ] Crear/editar cliente
- [ ] Crear renta
- [ ] Registrar pago
- [ ] Ver alertas
- [ ] Ver dashboard / KPIs
- [ ] Ver informe financiero

---

## Notas de Diseño

### ¿Por qué `@staticmethod` y no herencia de `BaseRepositorySA`?

Los repositorios existentes usan `@staticmethod` en todos sus métodos. Cambiar a métodos de instancia rompería la compatibilidad con los servicios. `BaseRepositorySA` se incluye como referencia futura para cuando se quiera refactorizar a métodos de instancia con herencia.

### ¿Por qué mantener `repositories_sa.py`?

Todos los servicios importan desde `repositories.repositories_sa`. Eliminar ese archivo rompería 12+ imports. La solución de thin wrapper mantiene compatibilidad total sin costo de rendimiento (Python resuelve los imports en tiempo de carga).

### Migración futura recomendada

Cuando se actualicen los servicios, cambiar los imports al módulo directo:
```python
# Antes (compatible):
from repositories.repositories_sa import AutoRepositorySA

# Después (recomendado):
from repositories.auto_repository_sa import AutoRepositorySA
```

---

## Archivos Eliminables Después de la Migración

- `repositories/repositories_sa.py.bak` — Backup del archivo original
- El código inline de los 8 repositorios que estaba en `repositories_sa.py` ya no es necesario

---

## Dependencias Requeridas

Estos módulos deben existir en `core/` para que los repositorios funcionen:

| Módulo | Usado por | Funciones requeridas |
|--------|-----------|---------------------|
| `core.database_sa` | Todos | `get_session`, `SessionLocal` |
| `core.exceptions` | Casi todos | `RegistroNoEncontrado` |
| `core.logger` | Todos | `get_logger` |
| `core.security` | `usuario_repository_sa` | `SecurityManager.hash_password` |
| `core.config` | `database_sa` | `DB_ENGINE`, `DB_MYSQL`, `DB_PATH` |

Si alguno de estos módulos no existe, los repositorios fallarán al importar. Verificar su existencia antes de la integración.
