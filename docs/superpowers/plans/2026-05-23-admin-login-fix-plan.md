# Plan de Implementación: Solución al Inicio de Sesión de la Cuenta `admin`

**Fecha:** 2026-05-23  
**Autor:** Antigravity  
**Tema:** TDD Plan para solucionar el acceso admin en desarrollo  

---

## Paso 1: Escribir la prueba fallante (TDD)
Crearemos un nuevo archivo de prueba `tests/test_admin_init.py` que importe `inicializar_base_datos` de `main_qt.py` y valide el comportamiento esperado bajo desarrollo y producción.

### Código de `tests/test_admin_init.py`:
```python
import pytest
from core.models import Usuario
from core.security import SecurityManager
from core.database_sa import get_session, Base, engine
import main_qt

def test_inicializar_base_datos_dev_mode(db_session, monkeypatch):
    """En modo desarrollo (PRODUCTION_MODE = False), el admin debe tener la contraseña Admin123!"""
    monkeypatch.setattr(main_qt, "PRODUCTION_MODE", False)
    
    # 1. Ejecutar inicialización
    main_qt.inicializar_base_datos()
    
    # 2. Verificar que se creó y que la contraseña es "Admin123!"
    with get_session() as session:
        admin = session.query(Usuario).filter(Usuario.username == 'admin').first()
        assert admin is not None
        assert admin.activo == 1
        assert SecurityManager.verify_password(admin.password, "Admin123!")

def test_inicializar_base_datos_dev_mode_restablece_existente(db_session, monkeypatch):
    """En modo desarrollo, si el admin ya existe con otra contraseña, debe restablecerse a Admin123!"""
    monkeypatch.setattr(main_qt, "PRODUCTION_MODE", False)
    
    # 1. Crear usuario admin previamente con contraseña aleatoria/diferente
    with get_session() as session:
        existing_admin = Usuario(
            username='admin',
            password=SecurityManager.hash_password("ContrasenaVieja123!"),
            nombre='Admin',
            rol='Administrador',
            activo=0  # inactivo para probar que lo activa
        )
        session.add(existing_admin)
        session.commit()
    
    # 2. Ejecutar inicialización
    main_qt.inicializar_base_datos()
    
    # 3. Verificar que se restableció
    with get_session() as session:
        admin = session.query(Usuario).filter(Usuario.username == 'admin').first()
        assert admin is not None
        assert admin.activo == 1
        assert SecurityManager.verify_password(admin.password, "Admin123!")
```

### Comando para ejecutar y comprobar el fallo:
```bash
pytest tests/test_admin_init.py -v
```

---

## Paso 2: Implementar el código mínimo para pasar la prueba
Modificaremos la función `inicializar_base_datos` en `main_qt.py` para cumplir con las especificaciones del diseño:

```python
def inicializar_base_datos(force_dialog=False):
    """Inicializa la base de datos con SQLAlchemy y crea admin si no existe.

    Args:
        force_dialog: Si True, muestra el diálogo de setup aunque no sea producción.
    """
    from core.config import SETUP_COMPLETED

    if (not SETUP_COMPLETED and PRODUCTION_MODE) or force_dialog:
        log.info("Primera ejecución o force_dialog - mostrando asistente de configuración")
        return "SETUP_NEEDED"

    log.info("Inicializando base de datos con SQLAlchemy...")
    try:
        init_db()
    except Exception as e:
        log.error(f"Error conectando a la base de datos: {e}")
        if PRODUCTION_MODE:
            return "SETUP_NEEDED"
        else:
            raise e

    from core.models import Usuario
    from core.database_sa import get_session

    with get_session() as session:
        admin = session.query(Usuario).filter(Usuario.username == 'admin').first()
        
        dev_password = "Admin123!"
        
        if not PRODUCTION_MODE:
            if not admin:
                admin = Usuario(
                    username='admin',
                    password=SecurityManager.hash_password(dev_password),
                    nombre='Administrador Principal',
                    rol='Administrador',
                    activo=1,
                    debe_cambiar_password=1
                )
                session.add(admin)
                log.info("Usuario admin creado con contraseña de desarrollo: Admin123!")
            else:
                admin.password = SecurityManager.hash_password(dev_password)
                admin.activo = 1
                log.info("Usuario admin verificado. Contraseña restablecida a la contraseña de desarrollo: Admin123!")
            return

        if admin:
            return

        import secrets
        new_password = secrets.token_urlsafe(12)
        admin = Usuario(
            username='admin',
            password=SecurityManager.hash_password(new_password),
            nombre='Administrador Principal',
            rol='Administrador',
            activo=1,
            debe_cambiar_password=1
        )
        session.add(admin)
        log.info("Usuario admin creado con contraseña aleatoria de producción")
        log.warning("Contraseña temporal generada: %s (no almacenar, cambiarla en primer inicio)", new_password)
```

---

## Paso 3: Ejecutar pruebas y verificar éxito
Ejecutaremos el comando pytest para asegurar el éxito de la prueba unitaria y de la suite completa.
```bash
pytest tests/test_admin_init.py -v
pytest
```
