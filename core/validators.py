"""
validators.py — Validadores de datos reutilizables

Todas las validaciones de negocio en un lugar. La capa de servicios
llama a estos validadores antes de persistir cualquier dato.
"""

import re
from datetime import date, datetime
from typing import Any

from core.exceptions import (
    CampoRequerido,
    PlacaInvalida,
    FechaInvalida,
    RangoInvalido,
    ValidacionError,
    InputSanitizationError,
)


# ─── Seguridad - Sanitización ─────────────────────────────────────────────────


def sanitize_for_sql(value: str) -> str:
    """
    Sanitiza valores para prevenir inyección SQL básica.
    Aunque SQLAlchemy ya protege, esta es una capa adicional.
    """
    if not value:
        return ""

    # Escapar comillas simples (principal vector SQL injection)
    value = value.replace("'", "''")

    # Eliminar caracteres de control
    value = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", value)

    return value.strip()


def validate_no_xss(value: str, max_length: int = 500) -> str:
    """
    Valida que el valor no contenga scripts o HTML peligroso.
    """
    if not value:
        return ""

    if len(value) > max_length:
        value = value[:max_length]

    # Patrones peligrosos XSS
    dangerous_patterns = [
        r"<script",
        r"javascript:",
        r"on\w+\s*=",  # onclick=, onload=, etc
        r"<iframe",
        r"<object",
        r"<embed",
        r"<form",
        r"eval\s*\(",
        r"document\.",
        r"window\.",
    ]

    value_lower = value.lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, value_lower, re.IGNORECASE):
            raise InputSanitizationError(
                detalle=f"Patrón XSS detectado: {pattern}",
                mensaje_usuario="El texto contiene caracteres no permitidos.",
            )

    return value.strip()


# ─── Texto ────────────────────────────────────────────────────────────────────


def requerir(valor: Any, campo: str) -> str:
    """Verifica que el campo no esté vacío. Retorna el valor limpio."""
    if valor is None or str(valor).strip() == "":
        raise CampoRequerido(campo)
    return str(valor).strip()


def sanitizar(texto: Any, max_len: int = 255) -> str:
    """Limpia y trunca texto de entrada."""
    if texto is None:
        return ""
    return str(texto).strip()[:max_len]


def solo_numeros(texto: str, campo: str = "campo") -> str:
    """Verifica que el texto contenga solo dígitos."""
    limpio = re.sub(r"\D", "", str(texto))
    if not limpio:
        raise ValidacionError(
            detalle=f"'{campo}' debe contener solo números.",
            mensaje_usuario=f"'{campo}' debe contener solo números.",
        )
    return limpio


# ─── Placa ────────────────────────────────────────────────────────────────────

_PATRON_PLACA = re.compile(r"^[A-Z0-9]{3,8}$")


def validar_placa(placa: str) -> str:
    """Normaliza y valida una placa colombiana (ej: ABC123)."""
    if not placa:
        raise PlacaInvalida(detalle="La placa no puede estar vacía.")
    normalizada = placa.upper().replace("-", "").replace(" ", "")
    if not _PATRON_PLACA.match(normalizada):
        raise PlacaInvalida(
            detalle=f"Placa '{placa}' inválida. Formato esperado: ABC123.",
        )
    return normalizada


# ─── Fechas ───────────────────────────────────────────────────────────────────


def parsear_fecha(valor: str, campo: str = "fecha") -> date:
    """Parsea una fecha en formato YYYY-MM-DD."""
    try:
        return datetime.strptime(str(valor)[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise FechaInvalida(
            detalle=f"'{campo}' no es una fecha válida: {valor!r}",
            mensaje_usuario=f"La {campo} ingresada no tiene un formato válido (YYYY-MM-DD).",
        )


def validar_rango_fechas(inicio: date, fin: date) -> None:
    """La fecha de inicio debe ser anterior o igual a la de fin."""
    if inicio > fin:
        raise ValidacionError(
            detalle=f"Fecha inicio {inicio} > fecha fin {fin}.",
            mensaje_usuario="La fecha de inicio no puede ser posterior a la fecha de fin.",
        )


# ─── Numéricos ────────────────────────────────────────────────────────────────


def validar_positivo(valor: float, campo: str) -> float:
    """El valor debe ser >= 0."""
    v = float(valor)
    if v < 0:
        raise RangoInvalido(campo, 0, "∞")
    return v


def validar_rango(valor: float, campo: str, minimo: float, maximo: float) -> float:
    """El valor debe estar dentro del rango dado."""
    v = float(valor)
    if not (minimo <= v <= maximo):
        raise RangoInvalido(campo, minimo, maximo)
    return v


# ─── Email ────────────────────────────────────────────────────────────────────

_PATRON_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validar_email(email: str) -> str:
    """Valida formato básico de email. Acepta vacío (campo opcional)."""
    limpio = email.strip()
    if limpio and not _PATRON_EMAIL.match(limpio):
        raise ValidacionError(
            detalle=f"Email inválido: {limpio!r}",
            mensaje_usuario="El correo electrónico no tiene un formato válido.",
        )
    return limpio


# ─── Documento de identidad ───────────────────────────────────────────────────


def validar_documento(no_doc: str, tipo_doc: str = "Cédula") -> str:
    """Valida que el número de documento no esté vacío."""
    limpio = str(no_doc).strip()
    if not limpio:
        raise CampoRequerido("Número de documento")
    if tipo_doc in ("Cédula", "NIT") and not re.match(r"^\d{6,15}$", limpio):
        raise ValidacionError(
            detalle=f"Documento tipo '{tipo_doc}' inválido: {limpio!r}",
            mensaje_usuario=f"El {tipo_doc} debe contener entre 6 y 15 dígitos.",
        )
    return limpio
