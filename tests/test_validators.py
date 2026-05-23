"""
test_validators.py — Unit tests for core/validators.py

Covers all 12 functions:
  sanitize_for_sql, validate_no_xss, requerir, sanitizar, solo_numeros,
  validar_placa, parsear_fecha, validar_rango_fechas, validar_positivo,
  validar_rango, validar_email, validar_documento

Run: pytest tests/test_validators.py -v
"""

import pytest
from datetime import date
from decimal import Decimal

from core.validators import (
    sanitize_for_sql,
    validate_no_xss,
    requerir,
    sanitizar,
    solo_numeros,
    validar_placa,
    parsear_fecha,
    validar_rango_fechas,
    validar_positivo,
    validar_rango,
    validar_email,
    validar_documento,
)
from core.exceptions import (
    CampoRequerido,
    PlacaInvalida,
    FechaInvalida,
    RangoInvalido,
    ValidacionError,
    InputSanitizationError,
)


# ═══════════════════════════════════════════════════════════════════════════════
# sanitize_for_sql
# ═══════════════════════════════════════════════════════════════════════════════

class TestSanitizeForSql:

    def test_cadena_limpia_no_cambia(self):
        """Sanitizes a clean string without changes."""
        assert sanitize_for_sql("Hola mundo") == "Hola mundo"

    def test_escapa_comilla_simple(self):
        """Single quotes are escaped (doubled)."""
        assert sanitize_for_sql("O'Brien") == "O''Brien"

    def test_elimina_caracteres_control(self):
        """Control characters are removed."""
        assert sanitize_for_sql("Hola\x00Mundo\x1F") == "HolaMundo"

    def test_strip_trim(self):
        """Whitespace is stripped."""
        assert sanitize_for_sql("  texto  ") == "texto"

    def test_vacio_retorna_vacio(self):
        """Empty string returns empty string."""
        assert sanitize_for_sql("") == ""

    def test_none_retorna_vacio(self):
        """None returns empty string."""
        assert sanitize_for_sql(None) == ""

    def test_sql_injection_clasico(self):
        """Classic SQL injection attempt is sanitized."""
        result = sanitize_for_sql("' OR '1'='1")
        assert result == "'' OR ''1''=''1"

    def test_multiples_comillas(self):
        """Multiple single quotes are all escaped."""
        assert sanitize_for_sql("a'b'c") == "a''b''c"


# ═══════════════════════════════════════════════════════════════════════════════
# validate_no_xss
# ═══════════════════════════════════════════════════════════════════════════════

class TestValidateNoXss:

    def test_cadena_limpia_pasa(self):
        """Clean string passes validation unchanged."""
        assert validate_no_xss("Hola mundo") == "Hola mundo"

    def test_strip_trim(self):
        """Whitespace is stripped."""
        assert validate_no_xss("  texto  ") == "texto"

    def test_vacio_retorna_vacio(self):
        """Empty string returns empty string."""
        assert validate_no_xss("") == ""

    def test_none_retorna_vacio(self):
        """None returns empty string."""
        assert validate_no_xss(None) == ""

    def test_trunca_si_excede_max_length(self):
        """String is truncated to max_length."""
        assert validate_no_xss("X" * 1000, max_length=10) == "X" * 10

    def test_rechaza_script_tag(self):
        """<script> tag raises InputSanitizationError."""
        with pytest.raises(InputSanitizationError, match="XSS|script"):
            validate_no_xss("<script>alert('xss')</script>")

    def test_rechaza_javascript_protocol(self):
        """javascript: protocol raises InputSanitizationError."""
        with pytest.raises(InputSanitizationError, match="XSS|javascript"):
            validate_no_xss("javascript:alert(1)")

    def test_rechaza_onclick_handler(self):
        """onclick= handler raises InputSanitizationError."""
        with pytest.raises(InputSanitizationError, match="XSS|on"):
            validate_no_xss("<div onclick='evil()'>")

    def test_rechaza_iframe(self):
        """<iframe> tag raises InputSanitizationError."""
        with pytest.raises(InputSanitizationError, match="XSS|iframe"):
            validate_no_xss("<iframe src='http://evil.com'>")

    def test_rechaza_eval(self):
        """eval() call raises InputSanitizationError."""
        with pytest.raises(InputSanitizationError, match="XSS|eval"):
            validate_no_xss("eval(something)")

    def test_rechaza_document_access(self):
        """document. access raises InputSanitizationError."""
        with pytest.raises(InputSanitizationError, match="XSS|document"):
            validate_no_xss("document.cookie")

    def test_rechaza_window_access(self):
        """window. access raises InputSanitizationError."""
        with pytest.raises(InputSanitizationError, match="XSS|window"):
            validate_no_xss("window.location")

    def test_rechaza_form_tag(self):
        """<form> tag raises InputSanitizationError."""
        with pytest.raises(InputSanitizationError):
            validate_no_xss("<form action='http://evil.com'>")

    def test_rechaza_mixed_case_xss(self):
        """Mixed-case XSS patterns are still caught (case insensitive)."""
        with pytest.raises(InputSanitizationError):
            validate_no_xss("<ScRiPt>alert(1)</sCrIpT>")


# ═══════════════════════════════════════════════════════════════════════════════
# requerir
# ═══════════════════════════════════════════════════════════════════════════════

class TestRequerir:

    def test_valor_valido_retorna_str(self):
        """Valid value is returned as stripped string."""
        assert requerir("  texto  ", "nombre") == "texto"

    def test_valor_numerico_retorna_str(self):
        """Numeric value is returned as string."""
        assert requerir(123, "edad") == "123"

    def test_valor_decimal_retorna_str(self):
        """Decimal value is returned as string."""
        assert requerir(Decimal("99.99"), "precio") == "99.99"

    def test_none_lanza_campo_requerido(self):
        """None raises CampoRequerido."""
        with pytest.raises(CampoRequerido, match="nombre"):
            requerir(None, "nombre")

    def test_str_vacio_lanza_campo_requerido(self):
        """Empty string raises CampoRequerido."""
        with pytest.raises(CampoRequerido, match="correo"):
            requerir("", "correo")

    def test_whitespace_lanza_campo_requerido(self):
        """Whitespace-only string raises CampoRequerido."""
        with pytest.raises(CampoRequerido, match="  campo  "):
            requerir("   ", "  campo  ")

    def test_mensaje_incluye_nombre_campo(self):
        """Error message includes the field name."""
        with pytest.raises(CampoRequerido) as excinfo:
            requerir(None, "Placa del Vehículo")
        assert "Placa del Vehículo" in str(excinfo.value)


# ═══════════════════════════════════════════════════════════════════════════════
# sanitizar
# ═══════════════════════════════════════════════════════════════════════════════

class TestSanitizar:

    def test_texto_limpio(self):
        """sanitizar() cleans and trims text."""
        assert sanitizar("  Hola  ") == "Hola"

    def test_trunca_a_max_len(self):
        """sanitizar() truncates to max_len."""
        assert sanitizar("X" * 300, max_len=5) == "X" * 5

    def test_none_retorna_vacio(self):
        """None returns empty string."""
        assert sanitizar(None) == ""

    def test_vacio_retorna_vacio(self):
        """Empty string returns empty string."""
        assert sanitizar("") == ""

    def test_whitespace_vacio_retorna_vacio(self):
        """Whitespace-only returns empty string."""
        assert sanitizar("   ") == ""

    def test_max_len_default_255(self):
        """Default max_len is 255."""
        larga = "A" * 500
        assert len(sanitizar(larga)) == 255

    def test_numeros_convertidos_a_str(self):
        """Numbers are converted to string."""
        assert sanitizar(12345) == "12345"

    def test_decimal_convertido_a_str(self):
        """Decimal is converted to string."""
        assert sanitizar(Decimal("45.67")) == "45.67"


# ═══════════════════════════════════════════════════════════════════════════════
# solo_numeros
# ═══════════════════════════════════════════════════════════════════════════════

class TestSoloNumeros:

    def test_solo_digitos_retorna_igual(self):
        """solo_numeros() returns digits unchanged."""
        assert solo_numeros("12345", "documento") == "12345"

    def test_elimina_no_digitos(self):
        """Non-digit characters are removed."""
        assert solo_numeros("ABC123-xyz", "codigo") == "123"

    def test_vacio_lanza_error(self):
        """Empty result raises ValidacionError."""
        with pytest.raises(ValidacionError, match="solo números"):
            solo_numeros("ABC", "codigo")

    def test_mensaje_incluye_nombre_campo(self):
        """Error message includes the field name."""
        with pytest.raises(ValidacionError) as excinfo:
            solo_numeros("sin-numeros", "teléfono")
        assert "teléfono" in str(excinfo.value)

    def test_espacios_eliminados(self):
        """Spaces are removed before checking."""
        assert solo_numeros("12 34 5", "doc") == "12345"

    def test_none_tratado_como_vacio(self):
        """None is treated as empty and raises error."""
        with pytest.raises(ValidacionError):
            solo_numeros(None, "campo")

    def test_decimal_string_con_punto(self):
        """Decimal point is removed (not a digit)."""
        assert solo_numeros("123.45", "monto") == "12345"


# ═══════════════════════════════════════════════════════════════════════════════
# validar_placa
# ═══════════════════════════════════════════════════════════════════════════════

class TestValidarPlaca:

    def test_placa_valida_retorna_mayusculas(self):
        """Valid plate returns uppercase normalized string."""
        assert validar_placa("abc123") == "ABC123"

    def test_placa_con_guion(self):
        """Plate with dash is normalized (dash removed)."""
        assert validar_placa("ABC-123") == "ABC123"

    def test_placa_con_espacios(self):
        """Plate with spaces is normalized."""
        assert validar_placa("ABC 123") == "ABC123"

    def test_placa_minima_3_caracteres(self):
        """3-character plate (min length) is valid."""
        assert validar_placa("A12") == "A12"

    def test_placa_maxima_8_caracteres(self):
        """8-character plate (max length) is valid."""
        assert validar_placa("ABCD1234") == "ABCD1234"

    def test_placa_vacia_lanza_error(self):
        """Empty string raises PlacaInvalida."""
        with pytest.raises(PlacaInvalida, match="vacía"):
            validar_placa("")

    def test_placa_none_lanza_error(self):
        """None raises PlacaInvalida."""
        with pytest.raises(PlacaInvalida, match="vacía"):
            validar_placa(None)

    def test_placa_demasiado_corta(self):
        """Less than 3 chars raises PlacaInvalida."""
        with pytest.raises(PlacaInvalida, match="inválida"):
            validar_placa("AB")

    def test_placa_demasiado_larga(self):
        """More than 8 chars raises PlacaInvalida."""
        with pytest.raises(PlacaInvalida, match="inválida"):
            validar_placa("ABCDEF123")

    def test_placa_con_caracteres_especiales(self):
        """Special characters raise PlacaInvalida."""
        with pytest.raises(PlacaInvalida, match="inválida"):
            validar_placa("ABC*12")

    def test_placa_con_minusculas(self):
        """Lowercase letters are uppercased."""
        assert validar_placa("xyz987") == "XYZ987"


# ═══════════════════════════════════════════════════════════════════════════════
# parsear_fecha
# ═══════════════════════════════════════════════════════════════════════════════

class TestParsearFecha:

    def test_fecha_valida_retorna_date(self):
        """Valid date string returns date object."""
        result = parsear_fecha("2024-12-25", "navidad")
        assert isinstance(result, date)
        assert result.year == 2024
        assert result.month == 12
        assert result.day == 25

    def test_fecha_con_hora(self):
        """Date with time component is parsed (time truncated)."""
        result = parsear_fecha("2024-01-15 14:30:00")
        assert result == date(2024, 1, 15)

    def test_formato_invalido_lanza_error(self):
        """Invalid format raises FechaInvalida."""
        with pytest.raises(FechaInvalida, match="fecha"):
            parsear_fecha("25-12-2024", "inicio")

    def test_cadena_no_fecha_lanza_error(self):
        """Non-date string raises FechaInvalida."""
        with pytest.raises(FechaInvalida, match="fecha"):
            parsear_fecha("no-es-fecha", "test")

    def test_mes_invalido_lanza_error(self):
        """Invalid month raises FechaInvalida."""
        with pytest.raises(FechaInvalida, match="fecha"):
            parsear_fecha("2024-13-01")

    def test_dia_invalido_lanza_error(self):
        """Invalid day raises FechaInvalida."""
        with pytest.raises(FechaInvalida, match="fecha"):
            parsear_fecha("2024-02-30")

    def test_none_lanza_error(self):
        """None raises FechaInvalida."""
        with pytest.raises(FechaInvalida, match="fecha"):
            parsear_fecha(None, "campo")

    def test_fecha_bisiesta(self):
        """Feb 29 in leap year is valid."""
        result = parsear_fecha("2024-02-29")
        assert result == date(2024, 2, 29)

    def test_mensaje_incluye_nombre_campo(self):
        """Error message includes the field name."""
        with pytest.raises(FechaInvalida) as excinfo:
            parsear_fecha("invalida", "fecha_nacimiento")
        assert "fecha_nacimiento" in str(excinfo.value)


# ═══════════════════════════════════════════════════════════════════════════════
# validar_rango_fechas
# ═══════════════════════════════════════════════════════════════════════════════

class TestValidarRangoFechas:

    def test_inicio_igual_fin(self):
        """Starting on the same day is valid."""
        # Should not raise
        validar_rango_fechas(date(2024, 1, 1), date(2024, 1, 1))

    def test_inicio_antes_fin(self):
        """Start before end is valid."""
        validar_rango_fechas(date(2024, 1, 1), date(2024, 1, 10))

    def test_inicio_despues_fin_lanza_error(self):
        """Start after end raises ValidacionError."""
        with pytest.raises(ValidacionError, match="inicio|posterior"):
            validar_rango_fechas(date(2024, 1, 10), date(2024, 1, 1))

    def test_mensaje_error_incluye_fechas(self):
        """Error message includes both dates."""
        with pytest.raises(ValidacionError) as excinfo:
            validar_rango_fechas(date(2024, 6, 1), date(2024, 5, 1))
        msg = str(excinfo.value)
        assert "2024-06-01" in msg
        assert "2024-05-01" in msg


# ═══════════════════════════════════════════════════════════════════════════════
# validar_positivo
# ═══════════════════════════════════════════════════════════════════════════════

class TestValidarPositivo:

    def test_cero_es_valido(self):
        """Zero is valid (>= 0)."""
        assert validar_positivo(0, "monto") == 0.0

    def test_positivo_retorna_float(self):
        """Positive value returns float."""
        assert validar_positivo(100, "precio") == 100.0

    def test_decimal_convertido_a_float(self):
        """Decimal input is converted to float."""
        assert validar_positivo(Decimal("50.5"), "monto") == 50.5

    def test_negativo_lanza_error(self):
        """Negative value raises RangoInvalido."""
        with pytest.raises(RangoInvalido, match="monto"):
            validar_positivo(-1, "monto")

    def test_string_numerico(self):
        """String numeric input is parsed."""
        assert validar_positivo("99.9", "valor") == 99.9

    def test_mensaje_incluye_campo(self):
        """Error message includes field name."""
        with pytest.raises(RangoInvalido) as excinfo:
            validar_positivo(-5, "descuento")
        assert "descuento" in str(excinfo.value)


# ═══════════════════════════════════════════════════════════════════════════════
# validar_rango
# ═══════════════════════════════════════════════════════════════════════════════

class TestValidarRango:

    def test_dentro_rango(self):
        """Value within range returns as float."""
        assert validar_rango(5, "nota", 1, 10) == 5.0

    def test_en_minimo(self):
        """Value at minimum is valid."""
        assert validar_rango(1, "nota", 1, 10) == 1.0

    def test_en_maximo(self):
        """Value at maximum is valid."""
        assert validar_rango(10, "nota", 1, 10) == 10.0

    def test_debajo_minimo_lanza_error(self):
        """Value below minimum raises RangoInvalido."""
        with pytest.raises(RangoInvalido, match="edad"):
            validar_rango(-1, "edad", 0, 150)

    def test_sobre_maximo_lanza_error(self):
        """Value above maximum raises RangoInvalido."""
        with pytest.raises(RangoInvalido, match="edad"):
            validar_rango(200, "edad", 0, 150)

    def test_mensaje_incluye_rango(self):
        """Error message includes minimum and maximum."""
        with pytest.raises(RangoInvalido) as excinfo:
            validar_rango(101, "porcentaje", 0, 100)
        assert "0" in str(excinfo.value) and "100" in str(excinfo.value)

    def test_string_numerico_parseado(self):
        """String numeric input is parsed."""
        assert validar_rango("50", "edad", 0, 150) == 50.0

    def test_rango_con_decimales(self):
        """Range with decimal values works."""
        assert validar_rango(Decimal("5.5"), "monto", Decimal("0"), Decimal("10")) == 5.5


# ═══════════════════════════════════════════════════════════════════════════════
# validar_email
# ═══════════════════════════════════════════════════════════════════════════════

class TestValidarEmail:

    def test_email_valido_retorna_limpio(self):
        """Valid email returns cleaned value."""
        assert validar_email("  user@example.com  ") == "user@example.com"

    def test_email_con_puntos(self):
        """Email with dots in local part is valid."""
        assert validar_email("user.name@domain.co") == "user.name@domain.co"

    def test_email_con_dominio_largo(self):
        """Email with long TLD is valid."""
        assert validar_email("user@example.info") == "user@example.info"

    def test_vacio_retorna_vacio(self):
        """Empty string returns empty (email is optional)."""
        assert validar_email("") == ""

    def test_sin_arroba_lanza_error(self):
        """Email without @ raises ValidacionError."""
        with pytest.raises(ValidacionError, match="Email|inválido"):
            validar_email("usuarioexample.com")

    def test_sin_dominio_lanza_error(self):
        """Email without domain raises ValidacionError."""
        with pytest.raises(ValidacionError, match="Email|inválido"):
            validar_email("usuario@")

    def test_sin_tld_lanza_error(self):
        """Email without TLD raises ValidacionError."""
        with pytest.raises(ValidacionError, match="Email|inválido"):
            validar_email("usuario@example")

    def test_espacios_internos_lanza_error(self):
        """Email with internal spaces raises ValidacionError."""
        with pytest.raises(ValidacionError, match="Email|inválido"):
            validar_email("user @example.com")

    def test_multiple_arroba_lanza_error(self):
        """Email with multiple @ raises ValidacionError."""
        with pytest.raises(ValidacionError, match="Email|inválido"):
            validar_email("user@domain@com")

    def test_unicode_email_valido(self):
        """Email with unicode in domain is valid (basic regex allows it)."""
        assert validar_email("user@münchen.de") == "user@münchen.de"


# ═══════════════════════════════════════════════════════════════════════════════
# validar_documento
# ═══════════════════════════════════════════════════════════════════════════════

class TestValidarDocumento:

    def test_cedula_valida(self):
        """Valid Cédula (numeric, 6-15 digits) returns cleaned value."""
        assert validar_documento("12345678", "Cédula") == "12345678"

    def test_nit_valido(self):
        """Valid NIT (numeric, 6-15 digits) returns cleaned value."""
        assert validar_documento("800198765", "NIT") == "800198765"

    def test_pasaporte_alfanumerico(self):
        """Pasaporte accepts alphanumeric values."""
        assert validar_documento("AB123456", "Pasaporte") == "AB123456"

    def test_cedula_extranjeria_alfanumerico(self):
        """Cédula de Extranjería accepts alphanumeric values."""
        assert validar_documento("CE123456", "Cédula Extranjería") == "CE123456"

    def test_licencia_usa_alfanumerico(self):
        """Licencia USA accepts alphanumeric values."""
        assert validar_documento("DL12345678", "Licencia USA") == "DL12345678"

    def test_vacio_lanza_error(self):
        """Empty string raises CampoRequerido."""
        with pytest.raises(CampoRequerido, match="documento"):
            validar_documento("", "Cédula")

    def test_none_lanza_error(self):
        """None raises error (str(None)='None' fails Cédula format)."""
        with pytest.raises((CampoRequerido, ValidacionError), match="documento|inválido|None"):
            validar_documento(None, "Cédula")

    def test_cedula_demasiado_corta(self):
        """Cédula with less than 6 digits raises ValidacionError."""
        with pytest.raises(ValidacionError, match="Cédula|Documento|inválido"):
            validar_documento("12345", "Cédula")

    def test_cedula_demasiado_larga(self):
        """Cédula with more than 15 digits raises ValidacionError."""
        with pytest.raises(ValidacionError, match="Cédula|Documento|inválido"):
            validar_documento("1234567890123456", "Cédula")

    def test_cedula_con_letras(self):
        """Cédula with letters raises ValidacionError."""
        with pytest.raises(ValidacionError, match="Cédula|Documento|inválido"):
            validar_documento("ABC12345", "Cédula")

    def test_nit_con_letras(self):
        """NIT with letters raises ValidacionError."""
        with pytest.raises(ValidacionError, match="NIT|inválido"):
            validar_documento("NIT12345", "NIT")

    def test_nit_en_minimo(self):
        """NIT with exactly 6 digits is valid."""
        assert validar_documento("123456", "NIT") == "123456"

    def test_cedula_en_maximo(self):
        """Cédula with exactly 15 digits is valid."""
        assert validar_documento("123456789012345", "Cédula") == "123456789012345"

    def test_whitespace_strip(self):
        """Whitespace is stripped."""
        assert validar_documento("  12345678  ", "Cédula") == "12345678"
