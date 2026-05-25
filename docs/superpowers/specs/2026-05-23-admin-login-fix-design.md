# Diseño: Solución al Inicio de Sesión de la Cuenta `admin`

**Fecha:** 2026-05-23  
**Autor:** Antigravity  
**Tema:** Corrección del inicio de sesión de la cuenta `admin` en modo de desarrollo  

---

## 1. Contexto y Causa Raíz

En el archivo `main_qt.py`, la función `inicializar_base_datos` inicializa la base de datos y crea el usuario `admin` si no existe en la tabla `usuarios`.

### El Problema
1. Al crear el usuario `admin`, el sistema genera una contraseña aleatoria y segura mediante `new_password = secrets.token_urlsafe(12)`.
2. Sin embargo, esta contraseña aleatoria **nunca se registra ni se imprime** en la consola ni en los logs. El log simplemente indica:
   ```python
   log.warning("Contraseña temporal generada (no almacenar, cambiarla en primer inicio)")
   ```
   sin revelar cuál es la contraseña generada.
3. Debido a esto, el usuario/desarrollador no tiene forma de conocer la contraseña y no puede iniciar sesión con la cuenta `admin`.
4. Adicionalmente, si el usuario `admin` ya existe en la base de datos (con una contraseña aleatoria olvidada de una ejecución anterior), ejecuciones consecutivas simplemente retornan sin actualizar la contraseña:
   ```python
   admin = session.query(Usuario).filter(Usuario.username == 'admin').first()
   if admin:
       return
   ```
   Esto hace que el usuario quede permanentemente bloqueado a menos que borre la base de datos.

---

## 2. Alternativas Propuestas

### Enfoque 1: Contraseña por defecto conocida en Modo Desarrollo (Recomendado)
Si la aplicación se ejecuta en modo de desarrollo (`PRODUCTION_MODE = False`):
* Establecer una contraseña por defecto predecible y que cumpla con los requisitos de seguridad (`core/security.py`), por ejemplo: `Admin123!`.
* Si el usuario `admin` ya existe, pero estamos en modo de desarrollo, actualizar automáticamente su contraseña a `Admin123!` para asegurar que el desarrollador pueda acceder sin tener que borrar su base de datos.
* Registrar un log claro indicando el estado del acceso de desarrollo.

* **Pros:** Experiencia fluida "out-of-the-box", corrige bases de datos existentes, seguro porque solo ocurre cuando `production_mode = false`.
* **Contras:** Ninguno significativo para desarrollo.

### Enfoque 2: Registrar la contraseña aleatoria en los logs
Mantener la contraseña aleatoria pero imprimirla explícitamente en el log para que el desarrollador la copie.
* **Pros:** Mayor aleatoriedad.
* **Contras:** Obliga al usuario a buscar en los logs cada vez que recree la BD; si ya existe el usuario `admin` con una contraseña anterior perdida, la aplicación no la actualizará y el usuario seguirá bloqueado hasta que elimine manualmente la base de datos `dinamo_rent_v3.db`.

---

## 3. Diseño Detallado (Enfoque 1)

Modificaremos la función `inicializar_base_datos` en `main_qt.py` para realizar las siguientes acciones en modo desarrollo (`not PRODUCTION_MODE`):

1. Definir una contraseña de desarrollo por defecto: `Admin123!` (cumple con tener >= 8 caracteres, 1 mayúscula, 1 minúscula, 1 número y 1 carácter especial).
2. Si el usuario `admin` **no existe**:
   * Crearlo con la contraseña por defecto `Admin123!`.
   * Loggear: `Usuario admin creado con la contraseña por defecto de desarrollo: Admin123!`.
3. Si el usuario `admin` **ya existe**:
   * Restablecer su contraseña a `Admin123!` y asegurarse de que esté activo (`activo=1`).
   * Loggear: `Usuario admin verificado. Contraseña restablecida a la contraseña por defecto de desarrollo: Admin123!`.

De esta forma, en cualquier base de datos de desarrollo, la contraseña para la cuenta `admin` siempre será **`Admin123!`**, eliminando cualquier tipo de bloqueo o confusión.

En modo de producción (`PRODUCTION_MODE = True`), el asistente de configuración inicial (`SetupWizard` en `views/setup_wizard.py`) continuará encargándose de solicitar al administrador su propia contraseña segura al instalar el sistema.

---

## 4. Plan de Verificación

1. **Prueba Unitaria / Integración:** Ejecutar `pytest` para asegurar que ningún cambio rompa las pruebas existentes.
2. **Verificación Manual:** Iniciar la aplicación y confirmar en los logs que el usuario `admin` se ha configurado/restablecido con la contraseña `Admin123!`.
