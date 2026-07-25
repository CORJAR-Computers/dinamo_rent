# Plan de Implementación: Transición a Producción y Ajustes de Seguridad en Desarrollo

**Fecha:** 2026-05-23  
**Autor:** Antigravity  
**Tema:** Plan de TDD para simplificar seguridad en desarrollo y capturar datos en la transición a producción  

---

## Paso 1: Modificar las pruebas de desarrollo (TDD - Fase RED)
Actualizaremos las pruebas existentes en `tests/test_admin_init.py` para asegurar que el flag `debe_cambiar_password` sea `False` (o `0`) en desarrollo, tanto para la creación inicial como para el restablecimiento.

### Cambios en `tests/test_admin_init.py`:
```python
def test_inicializar_base_datos_dev_mode(db_session, monkeypatch):
    """En modo desarrollo (PRODUCTION_MODE = False), el admin debe tener la contraseña Admin123! y no estar forzado a cambiarla."""
    monkeypatch.setattr(main_qt, "PRODUCTION_MODE", False)

    # 1. Ejecutar inicialización
    main_qt.inicializar_base_datos()

    # 2. Verificar que se creó, que la contraseña es "Admin123!" y debe_cambiar_password es False
    with get_session() as session:
        admin = session.query(Usuario).filter(Usuario.username == "admin").first()
        assert admin is not None
        assert admin.activo == 1
        assert SecurityManager.verify_password(admin.password, "Admin123!")
        assert admin.debe_cambiar_password == 0  # <--- NUEVA ASERCIÓN


def test_inicializar_base_datos_dev_mode_restablece_existente(db_session, monkeypatch):
    """En modo desarrollo, si el admin ya existe con otra contraseña y flag activado, debe restablecerse y desactivar el flag."""
    monkeypatch.setattr(main_qt, "PRODUCTION_MODE", False)

    # 1. Crear usuario admin previamente con contraseña aleatoria y debe_cambiar_password = 1
    with get_session() as session:
        session.query(Usuario).filter(Usuario.username == "admin").delete()
        session.commit()

        existing_admin = Usuario(
            username="admin",
            password=SecurityManager.hash_password("ContrasenaVieja123!"),
            nombre="Admin",
            rol="Administrador",
            activo=0,
            debe_cambiar_password=1,  # <--- Activo
        )
        session.add(existing_admin)
        session.commit()

    # 2. Ejecutar inicialización
    main_qt.inicializar_base_datos()

    # 3. Verificar que se restableció y debe_cambiar_password se desactivó
    with get_session() as session:
        admin = session.query(Usuario).filter(Usuario.username == "admin").first()
        assert admin is not None
        assert admin.activo == 1
        assert SecurityManager.verify_password(admin.password, "Admin123!")
        assert admin.debe_cambiar_password == 0  # <--- NUEVA ASERCIÓN
```

### Ejecutar para confirmar fallo:
```bash
pytest tests/test_admin_init.py -v
```

---

## Paso 2: Implementar el código mínimo en `main_qt.py` (TDD - Fase GREEN)
Modificaremos `inicializar_base_datos` en `main_qt.py` para desactivar el flag `debe_cambiar_password` en desarrollo:

```python
if not PRODUCTION_MODE:
    if not admin:
        admin = Usuario(
            username="admin",
            password=SecurityManager.hash_password(dev_password),
            nombre="Administrador Principal",
            rol="Administrador",
            activo=1,
            debe_cambiar_password=0,  # <--- Cambiado a 0
        )
        session.add(admin)
        log.info("Usuario admin creado con contraseña de desarrollo: Admin123!")
    else:
        admin.password = SecurityManager.hash_password(dev_password)
        admin.activo = 1
        admin.debe_cambiar_password = 0  # <--- Forzado a 0 en restablecimiento
        log.info(
            "Usuario admin verificado. Contraseña restablecida a la contraseña de desarrollo: Admin123!"
        )
    return
```

### Ejecutar para confirmar éxito:
```bash
pytest tests/test_admin_init.py -v
```

---

## Paso 3: Modificar `views/setup_wizard.py` para capturar dirección y teléfono
Expandiremos la clase `PreferencesSetupPage` y su lógica de guardado:

1. **Añadir campos y widgets a `PreferencesSetupPage.__init__`:**
   ```python
   self.txt_direccion = QLineEdit()
   self.txt_telefono = QLineEdit()
   
   input_field(self.txt_direccion)
   input_field(self.txt_telefono)
   self.txt_direccion.setPlaceholderText("Ej. Calle 20 # 15-30, Sincelejo")
   self.txt_telefono.setPlaceholderText("Ej. +57 300 123 4567")

   form.addRow("Dirección Empresa *:", self.txt_direccion)
   form.addRow("Teléfono Empresa *:", self.txt_telefono)

   self.registerField("pref_direccion*", self.txt_direccion)
   self.registerField("pref_telefono*", self.txt_telefono)
   ```

2. **Actualizar el guardado en `SetupWizard._save_configuration`:**
   ```python
   app_config = {
       "production_mode": "true",
       "setup_completed": "true",
       "company_name": self.field("pref_empresa"),
       "company_address": self.field("pref_direccion"),
       "company_phone": self.field("pref_telefono"),
       "currency_symbol": self.field("pref_moneda"),
   }
   guardar_configuracion("app", app_config)
   ```

---

## Paso 4: Ejecutar todas las pruebas y verificar no regresión
Correremos la suite completa de pruebas unitarias:
```bash
pytest
```
