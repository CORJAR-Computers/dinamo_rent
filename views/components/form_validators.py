"""
FormValidator — Sistema de validación de formularios con feedback visual en tiempo real.

Uso básico:
    validator = FormValidator()
    validator.add_field(self.txt_nombre, [Required(), MinLength(3)])
    validator.add_field(self.txt_email, [Required(), Email()])

    if validator.validate_all():
        # todos los campos válidos, proceder
        ...

    # Para limpiar errores visuales:
    validator.clear_all()

Los errores se limpian automáticamente cuando el usuario empieza a escribir.
"""

import re
from typing import List, Optional, Callable

from PySide6.QtWidgets import QWidget, QLabel, QLineEdit, QComboBox

# ─── Reglas de validación ─────────────────────────────────────────────────────


class ValidationRule:
    """Regla base. Sobrescribir validate() y obtener mensaje de error."""

    def validate(self, value: str) -> bool:
        raise NotImplementedError

    def error_message(self, field_name: str = "") -> str:
        raise NotImplementedError


class Required(ValidationRule):
    """El campo no puede estar vacío."""

    def validate(self, value: str) -> bool:
        return bool(value and value.strip())

    def error_message(self, field_name: str = "") -> str:
        return f"{field_name} es obligatorio".strip() or "Campo obligatorio"


class Email(ValidationRule):
    """Formato de email válido."""

    _PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    def validate(self, value: str) -> bool:
        if not value:
            return True  # permitir vacío (combinar con Required si se requiere)
        return bool(self._PATTERN.match(value.strip()))

    def error_message(self, field_name: str = "") -> str:
        return f"{field_name} no es un email válido".strip() or "Email inválido"


class Numeric(ValidationRule):
    """Debe ser un número válido (entero o decimal)."""

    def validate(self, value: str) -> bool:
        if not value:
            return True
        try:
            float(value.replace(",", "."))
            return True
        except ValueError:
            return False

    def error_message(self, field_name: str = "") -> str:
        return f"{field_name} debe ser un número".strip() or "Debe ser numérico"


class Integer(ValidationRule):
    """Debe ser un número entero."""

    def validate(self, value: str) -> bool:
        if not value:
            return True
        try:
            int(value)
            return True
        except ValueError:
            return False

    def error_message(self, field_name: str = "") -> str:
        return f"{field_name} debe ser un número entero".strip() or "Debe ser entero"


class MinLength(ValidationRule):
    """Longitud mínima del texto."""

    def __init__(self, min_len: int):
        self.min_len = min_len

    def validate(self, value: str) -> bool:
        if not value:
            return True
        return len(value.strip()) >= self.min_len

    def error_message(self, field_name: str = "") -> str:
        return f"{field_name} debe tener al menos {self.min_len} caracteres"


class MaxLength(ValidationRule):
    """Longitud máxima del texto."""

    def __init__(self, max_len: int):
        self.max_len = max_len

    def validate(self, value: str) -> bool:
        if not value:
            return True
        return len(value.strip()) <= self.max_len

    def error_message(self, field_name: str = "") -> str:
        return f"{field_name} no debe exceder {self.max_len} caracteres"


class Regex(ValidationRule):
    """Patrón regex personalizado."""

    def __init__(self, pattern: str, msg: str = "Formato inválido"):
        self._pattern = re.compile(pattern)
        self._msg = msg

    def validate(self, value: str) -> bool:
        if not value:
            return True
        return bool(self._pattern.match(value.strip()))

    def error_message(self, field_name: str = "") -> str:
        return f"{field_name}: {self._msg}" if field_name else self._msg


class MinValue(ValidationRule):
    """Valor numérico mínimo."""

    def __init__(self, min_val: float):
        self.min_val = min_val

    def validate(self, value: str) -> bool:
        if not value:
            return True
        try:
            return float(value.replace(",", ".")) >= self.min_val
        except ValueError:
            return False

    def error_message(self, field_name: str = "") -> str:
        return f"{field_name} debe ser mayor o igual a {self.min_val}"


class MaxValue(ValidationRule):
    """Valor numérico máximo."""

    def __init__(self, max_val: float):
        self.max_val = max_val

    def validate(self, value: str) -> bool:
        if not value:
            return True
        try:
            return float(value.replace(",", ".")) <= self.max_val
        except ValueError:
            return False

    def error_message(self, field_name: str = "") -> str:
        return f"{field_name} debe ser menor o igual a {self.max_val}"


class Phone(ValidationRule):
    """Formato de teléfono/celular colombiano (7-10 dígitos, opcional +57)."""

    _PATTERN = re.compile(r"^(\+?57)?\d{7,10}$")

    def validate(self, value: str) -> bool:
        if not value:
            return True
        return bool(self._PATTERN.match(value.strip().replace(" ", "").replace("-", "")))

    def error_message(self, field_name: str = "") -> str:
        return f"{field_name} debe ser un teléfono válido (7-10 dígitos)"


class Custom(ValidationRule):
    """Regla personalizada con función lambda."""

    def __init__(self, fn: Callable[[str], bool], msg: str = "Valor inválido"):
        self._fn = fn
        self._msg = msg

    def validate(self, value: str) -> bool:
        if not value:
            return True
        return self._fn(value.strip())

    def error_message(self, field_name: str = "") -> str:
        return f"{field_name}: {self._msg}" if field_name else self._msg


# ─── Tipo de widget admitido ──────────────────────────────────────────────────


def _get_widget_value(widget: QWidget) -> str:
    """Obtiene el valor actual del widget según su tipo."""
    if isinstance(widget, QLineEdit):
        return widget.text()
    if isinstance(widget, QComboBox):
        return widget.currentText()
    # Para widgets con propiedad 'text' (QLabel, QPushButton, etc.)
    text = widget.property("text")
    if text is not None:
        return str(text)
    return ""


def _connect_change_signal(widget: QWidget, callback: Callable) -> None:
    """Conecta la señal de cambio según el tipo de widget."""
    if isinstance(widget, QLineEdit):
        widget.textChanged.connect(callback)
    elif isinstance(widget, QComboBox):
        widget.currentTextChanged.connect(callback)


# ─── FieldValidator ───────────────────────────────────────────────────────────


class FieldValidator:
    """Valida un campo individual con feedback visual.

    Args:
        widget: QLineEdit, QComboBox u otro widget con texto.
        rules: Lista de reglas ValidationRule.
        field_name: Nombre mostrado en mensajes de error.
        error_label: QLabel opcional para mostrar el mensaje de error inline.
    """

    def __init__(
        self,
        widget: QWidget,
        rules: List[ValidationRule],
        field_name: str = "",
        error_label: Optional[QLabel] = None,
    ):
        self.widget = widget
        self.rules = rules
        self.field_name = field_name
        self.error_label = error_label
        self._has_error = False
        self._custom_validator: Optional[Callable[[], bool]] = None

        # Auto-limpiar error cuando el usuario escribe
        _connect_change_signal(widget, self._on_change)

        if error_label:
            error_label.setStyleSheet(
                "QLabel { color: #dc2626; font-size: 9pt; padding: 2px 0 0 0; }"
            )
            error_label.hide()

    def _on_change(self, _value: str) -> None:
        """Limpia el error visual cuando el usuario modifica el campo."""
        if self._has_error:
            self.clear_error()

    def set_custom_validator(self, fn: Callable[[], bool]) -> None:
        """Establece un validador personalizado que se ejecuta además de las reglas."""
        self._custom_validator = fn

    def validate(self) -> bool:
        """Ejecuta todas las reglas. Retorna True si todas pasan."""
        value = _get_widget_value(self.widget)

        for rule in self.rules:
            if not rule.validate(value):
                self._show_error(rule.error_message(self.field_name))
                return False

        # Validador personalizado
        if self._custom_validator and not self._custom_validator():
            self._show_error("Valor inválido")
            return False

        self._show_success()
        return True

    def _show_error(self, msg: str) -> None:
        self._has_error = True
        setattr(self.widget, "_field_error", True)
        if isinstance(self.widget, (QLineEdit, QComboBox)):
            self.widget.setProperty("validation_state", "error")
            self.widget.style().unpolish(self.widget)
            self.widget.style().polish(self.widget)
        if self.error_label:
            self.error_label.setText(msg)
            self.error_label.show()

    def _show_success(self) -> None:
        self._has_error = False
        setattr(self.widget, "_field_error", False)
        if isinstance(self.widget, (QLineEdit, QComboBox)):
            self.widget.setProperty("validation_state", "success")
            self.widget.style().unpolish(self.widget)
            self.widget.style().polish(self.widget)
        if self.error_label:
            self.error_label.hide()

    def clear_error(self) -> None:
        """Restaura el estilo original del campo."""
        self._has_error = False
        setattr(self.widget, "_field_error", False)
        if isinstance(self.widget, (QLineEdit, QComboBox)):
            self.widget.setProperty("validation_state", None)
            self.widget.style().unpolish(self.widget)
            self.widget.style().polish(self.widget)
        if self.error_label:
            self.error_label.hide()

    @property
    def has_error(self) -> bool:
        return self._has_error


# ─── FormValidator ────────────────────────────────────────────────────────────


class FormValidator:
    """Gestiona la validación de múltiples campos en un formulario.

    Uso:
        fv = FormValidator()
        fv.add_field(self.txt_nombre, [Required(), MinLength(3)], "Nombre")
        fv.add_field(self.txt_email, [Required(), Email()], "Email",
                     error_label=self.lbl_error_email)

        if fv.validate_all():
            guardar()
        else:
            # El primer campo con error recibe el foco
            fv.focus_first_error()
    """

    def __init__(self):
        self._fields: List[FieldValidator] = []

    def add_field(
        self,
        widget: QWidget,
        rules: List[ValidationRule],
        field_name: str = "",
        error_label: Optional[QLabel] = None,
    ) -> FieldValidator:
        """Agrega un campo al formulario para validación."""
        fv = FieldValidator(widget, rules, field_name, error_label)
        self._fields.append(fv)
        return fv

    def validate_all(self) -> bool:
        """Valida todos los campos. Retorna True si todos pasan."""
        all_valid = True
        for fv in self._fields:
            if not fv.validate():
                all_valid = False
        return all_valid

    def clear_all(self) -> None:
        """Limpia errores visuales de todos los campos."""
        for fv in self._fields:
            fv.clear_error()

    def focus_first_error(self) -> bool:
        """Pone el foco en el primer campo con error. Retorna True si encontró uno."""
        for fv in self._fields:
            if fv.has_error:
                fv.widget.setFocus()
                return True
        return False

    @property
    def fields(self) -> List[FieldValidator]:
        return self._fields

    def get_field(self, widget: QWidget) -> Optional[FieldValidator]:
        """Obtiene el FieldValidator para un widget específico."""
        for fv in self._fields:
            if fv.widget is widget:
                return fv
        return None


# ─── Helper para crear label de error inline ──────────────────────────────────


def make_error_label() -> QLabel:
    """Crea un QLabel listo para usar como error label inline."""
    lbl = QLabel()
    lbl.setWordWrap(True)
    lbl.setStyleSheet("QLabel { color: #dc2626; font-size: 9pt; padding: 2px 0 0 0; }")
    lbl.hide()
    return lbl
