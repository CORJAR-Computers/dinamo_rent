"""
exceptions.py — Excepciones personalizadas de Dinamo Rent ERP

Usar excepciones tipadas en lugar de cadenas de error permite:
- Manejo diferenciado en la capa de presentación
- Logs automáticos con contexto
- Mensajes de usuario claros y uniformes
"""


class DinamoBaseError(Exception):
    """Clase base para todas las excepciones de la aplicación."""

    mensaje_usuario: str = "Ocurrió un error inesperado."

    def __init__(self, detalle: str = "", mensaje_usuario: str = ""):
        super().__init__(detalle or self.mensaje_usuario)
        if mensaje_usuario:
            self.mensaje_usuario = mensaje_usuario
        self.detalle = detalle

    def __str__(self) -> str:
        return self.detalle or self.mensaje_usuario


# ─── Base de datos ────────────────────────────────────────────────────────────


class DatabaseError(DinamoBaseError):
    mensaje_usuario = "Error al acceder a la base de datos."


class RegistroNoEncontrado(DatabaseError):
    mensaje_usuario = "El registro solicitado no existe."


class DuplicadoError(DatabaseError):
    mensaje_usuario = "Ya existe un registro con esos datos."


# ─── Validación ───────────────────────────────────────────────────────────────


class ValidacionError(DinamoBaseError):
    """Se lanza cuando los datos de entrada no cumplen las reglas de negocio."""

    mensaje_usuario = "Los datos ingresados no son válidos."


class CampoRequerido(ValidacionError):
    def __init__(self, campo: str):
        super().__init__(
            detalle=f"El campo '{campo}' es obligatorio.",
            mensaje_usuario=f"El campo '{campo}' es obligatorio.",
        )


class FechaInvalida(ValidacionError):
    mensaje_usuario = "La fecha ingresada no es válida."


class PlacaInvalida(ValidacionError):
    mensaje_usuario = "La placa ingresada no tiene un formato válido."


class RangoInvalido(ValidacionError):
    """Cuando un valor numérico está fuera del rango permitido."""

    def __init__(self, campo: str, minimo, maximo):
        super().__init__(
            detalle=f"'{campo}' debe estar entre {minimo} y {maximo}.",
            mensaje_usuario=f"'{campo}' debe estar entre {minimo} y {maximo}.",
        )


# ─── Negocio ──────────────────────────────────────────────────────────────────


class NegocioError(DinamoBaseError):
    """Reglas de negocio violadas (no es un error técnico)."""

    mensaje_usuario = "La operación no puede realizarse."


class VehiculoNoDisponible(NegocioError):
    def __init__(self, placa: str):
        super().__init__(
            detalle=f"El vehículo {placa} no está disponible para renta.",
            mensaje_usuario=f"El vehículo {placa} no está disponible en este momento.",
        )


class RentaYaCerrada(NegocioError):
    mensaje_usuario = "Esta renta ya fue finalizada y no puede modificarse."


class ClienteEnListaNegra(NegocioError):
    mensaje_usuario = "Este cliente está en lista negra y no puede rentar."


# ─── Seguridad ────────────────────────────────────────────────────────────────


class SeguridadError(DinamoBaseError):
    mensaje_usuario = "Acceso denegado."


class CredencialesInvalidas(SeguridadError):
    mensaje_usuario = "Usuario o contraseña incorrectos."


class SesionExpirada(SeguridadError):
    mensaje_usuario = "Tu sesión ha expirado. Por favor inicia sesión nuevamente."


class PermisoInsuficiente(SeguridadError):
    mensaje_usuario = "No tienes permisos para realizar esta acción."


class CuentaBloqueadaError(SeguridadError):
    mensaje_usuario = (
        "Tu cuenta ha sido bloqueada por múltiples intentos fallidos. Contacta al administrador."
    )


class RateLimitExceededError(SeguridadError):
    mensaje_usuario = (
        "Demasiados intentos de inicio de sesión. Por favor espera antes de intentar nuevamente."
    )


class InputSanitizationError(SeguridadError):
    mensaje_usuario = "Los datos contienen caracteres no permitidos."
