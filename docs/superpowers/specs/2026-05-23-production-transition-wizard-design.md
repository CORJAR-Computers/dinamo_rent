# Diseño: Transición a Producción y Ajustes de Seguridad en Desarrollo

**Fecha:** 2026-05-23  
**Autor:** Antigravity  
**Tema:** Simplificar seguridad en desarrollo y capturar datos de empresa en la transición a producción  

---

## 1. Contexto y Requerimientos

### 1.1. Seguridad en Fase de Desarrollo
Actualmente, el sistema marca al usuario `admin` de desarrollo (`PRODUCTION_MODE = False`) con `debe_cambiar_password = 1`. Esto obliga al desarrollador a cambiar la contraseña obligatoriamente al iniciar sesión, lo cual resulta molesto y obstaculiza las fases rápidas de prueba y desarrollo.
**Solución:** Desactivar este flag (`debe_cambiar_password = 0`) para el usuario `admin` en modo desarrollo.

### 1.2. Transición a Producción
Cuando el sistema pasa a producción (`production_mode = true` en `config.ini` y `setup_completed = false`), el ERP inicia en modo "Setup Requerido" y lanza el `SetupWizard` (`views/setup_wizard.py`).
El usuario solicita que en esta fase de transición, el formulario de configuración inicial capture:
1. **Datos de la Empresa:** Nombre de la empresa.
2. **Dirección de la Empresa.**
3. **Números de Teléfono de la Empresa.**
4. **Usuario Administrador Principal:** Nombre, Usuario, Contraseña (sin usar valores de desarrollo).

---

## 2. Alternativas Propuestas

### Enfoque 1: Expandir el asistente `SetupWizard` existente (Recomendado)
El asistente de configuración inicial (`SetupWizard`) ya está diseñado para ejecutarse exactamente en el evento de transición a producción.
* **Modificación:** Añadir los campos de **Dirección** y **Teléfono** directamente a la página `PreferencesSetupPage` del asistente.
* **Modificación de Desarrollo:** Establecer `debe_cambiar_password = 0` para el usuario `admin` en `main_qt.py` cuando se está en desarrollo.

* **Pros:** Reutiliza de forma limpia la arquitectura del asistente actual, mantiene la interfaz homogénea y profesional de PySide6, y guarda la configuración de manera centralizada.
* **Contras:** Ninguno.

### Enfoque 2: Crear un nuevo diálogo emergente "First Login"
Crear una ventana o diálogo completamente nuevo para recopilar la información cuando el administrador inicia sesión por primera vez en producción.
* **Pros:** Independiente del asistente de configuración.
* **Contras:** Duplica lógica y campos que ya se solicitan en el asistente de instalación inicial, aumentando la complejidad del código innecesariamente (violando DRY).

---

## 3. Diseño Detallado (Enfoque 1)

### 3.1. main_qt.py (Ajuste de Desarrollo)
En `inicializar_base_datos`, cuando `PRODUCTION_MODE` es `False`, el usuario `admin` se creará o actualizará con:
* `debe_cambiar_password = 0`

### 3.2. views/setup_wizard.py (Captura de Datos de Empresa)
Modificaremos `PreferencesSetupPage` para añadir campos de texto de dirección y teléfono:

1. **Campos nuevos:**
   ```python
   self.txt_direccion = QLineEdit()
   self.txt_telefono = QLineEdit()
   ```
2. **Estilo y placeholder:**
   ```python
   input_field(self.txt_direccion)
   input_field(self.txt_telefono)
   self.txt_direccion.setPlaceholderText("Ej. Calle 20 # 15-30, Sincelejo")
   self.txt_telefono.setPlaceholderText("Ej. +57 300 123 4567")
   ```
3. **Formulario:**
   ```python
   form.addRow("Dirección Empresa *:", self.txt_direccion)
   form.addRow("Teléfono Empresa *:", self.txt_telefono)
   ```
4. **Registro de campos obligatorios (con asterisco):**
   ```python
   self.registerField("pref_direccion*", self.txt_direccion)
   self.registerField("pref_telefono*", self.txt_telefono)
   ```
5. **Guardado en `_save_configuration`:**
   ```python
   app_config = {
       "production_mode": "true",
       "setup_completed": "true",
       "company_name": self.field("pref_empresa"),
       "company_address": self.field("pref_direccion"),
       "company_phone": self.field("pref_telefono"),
       "currency_symbol": self.field("pref_moneda")
   }
   guardar_configuracion("app", app_config)
   ```

---

## 4. Plan de Verificación

1. **Pruebas Unitarias:**
   * Adaptar `tests/test_admin_init.py` para asegurar que el flag `debe_cambiar_password` es `False` en desarrollo.
   * Ejecutar la suite de pruebas unitarias.
2. **Verificación Manual:**
   * Arrancar el sistema en desarrollo y validar que se puede iniciar sesión con `admin` / `Admin123!` sin que aparezca la ventana de cambio de contraseña obligatoria.
   * Modificar `config.ini` para simular la transición a producción (`setup_completed = false`, `production_mode = true`) y verificar que el asistente de configuración solicita y guarda la dirección, teléfono, datos de la empresa y cuenta de administrador correctamente.
