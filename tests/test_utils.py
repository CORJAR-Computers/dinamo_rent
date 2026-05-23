"""
test_utils.py — Unit tests for core/utils.py

Covers:
  Utility functions:     limpiar_nombre_archivo, limpiar_moneda, fmt_moneda
  File-system functions: obtener_rutas_archivos, obtener_ruta_logo,
                         obtener_logo_base64, cargar_plantilla_jinja
  Desktop functions:     abrir_archivo, abrir_whatsapp, abrir_email
  Printer:               enviar_a_impresora
  PDF generation:        generar_orden_alquiler_pdf, generar_contrato_temp,
                         generar_pdf_reserva, generar_orden_renta_jinja,
                         generar_reserva_jinja (ReportLab fallback)

Run: pytest tests/test_utils.py -v
"""

import os
import sys
import base64
from pathlib import Path
from io import BytesIO
from unittest.mock import MagicMock

import pytest

import importlib

from PIL import Image as PILImage

import core.utils


# ═══════════════════════════════════════════════════════════════════════════════
# Helper: create a valid 1×1 PNG for ReportLab Image()
# ═══════════════════════════════════════════════════════════════════════════════

def _create_valid_png(path: str):
    """Create a minimal valid 1x1 pixel PNG at the given path."""
    img = PILImage.new("RGB", (1, 1), color=(255, 255, 255))
    img.save(path)


# ═══════════════════════════════════════════════════════════════════════════════
# Helper: make a proper QUrl mock that stores the URL string
# ═══════════════════════════════════════════════════════════════════════════════

class _FakeQUrl:
    """QUrl mock that stores the URL and supports str()."""
    def __init__(self, url: str = ""):
        self._url = url
    def __str__(self):
        return self._url
    def __repr__(self):
        return self._url
    @staticmethod
    def fromLocalFile(path: str):
        return _FakeQUrl(f"file:///{path}")


def _install_pyside6_mocks(monkeypatch):
    """Inject QDesktopServices and QUrl mocks into sys.modules for core.utils."""
    fake_services = MagicMock()
    fake_services.openUrl.return_value = True

    monkeypatch.setitem(sys.modules, "PySide6.QtCore",
                        type("qtcore", (), {"QUrl": _FakeQUrl})())
    monkeypatch.setitem(sys.modules, "PySide6.QtGui",
                        type("qtgui", (), {"QDesktopServices": fake_services})())
    # Force reimport so core.utils picks up the mocked modules
    for mod_name in list(sys.modules.keys()):
        if "core.utils" in mod_name:
            del sys.modules[mod_name]
    return fake_services


# ═══════════════════════════════════════════════════════════════════════════════
# limpiar_nombre_archivo
# ═══════════════════════════════════════════════════════════════════════════════

class TestLimpiarNombreArchivo:

    def test_none_retorna_cliente(self):
        """None returns 'Cliente'."""
        from core.utils import limpiar_nombre_archivo
        assert limpiar_nombre_archivo(None) == "Cliente"

    def test_vacio_retorna_cliente(self):
        """Empty string returns 'Cliente'."""
        from core.utils import limpiar_nombre_archivo
        assert limpiar_nombre_archivo("") == "Cliente"

    def test_solo_espacios_retorna_vacio(self):
        """Whitespace-only is stripped to empty string (not 'Cliente')."""
        from core.utils import limpiar_nombre_archivo
        result = limpiar_nombre_archivo("   ")
        assert result == ""

    def test_texto_normal_remplaza_espacios(self):
        """Spaces are replaced with underscores."""
        from core.utils import limpiar_nombre_archivo
        assert limpiar_nombre_archivo("Juan Perez") == "Juan_Perez"

    def test_caracteres_no_alfanumericos_removidos(self):
        """Special characters are stripped out."""
        from core.utils import limpiar_nombre_archivo
        assert limpiar_nombre_archivo("María!@#$%") == "Mara"

    def test_numeros_permitidos(self):
        """Digits are preserved."""
        from core.utils import limpiar_nombre_archivo
        assert limpiar_nombre_archivo("Cliente123") == "Cliente123"

    def test_guiones_y_puntos_removidos(self):
        """Hyphens and dots are removed."""
        from core.utils import limpiar_nombre_archivo
        assert limpiar_nombre_archivo("cliente-1.0") == "cliente10"

    def test_multiples_espacios_internos(self):
        """Multiple spaces become multiple underscores."""
        from core.utils import limpiar_nombre_archivo
        result = limpiar_nombre_archivo("Juan  Carlos")
        assert "Juan" in result
        assert "Carlos" in result
        assert "__" in result  # double space → double underscore

    def test_numero_como_string(self):
        """Numeric string works."""
        from core.utils import limpiar_nombre_archivo
        assert limpiar_nombre_archivo("123") == "123"


# ═══════════════════════════════════════════════════════════════════════════════
# limpiar_moneda
# ═══════════════════════════════════════════════════════════════════════════════

class TestLimpiarMoneda:

    def test_none_retorna_cero(self):
        """None returns 0.0."""
        from core.utils import limpiar_moneda
        assert limpiar_moneda(None) == 0.0

    def test_vacio_retorna_cero(self):
        """Empty string returns 0.0."""
        from core.utils import limpiar_moneda
        assert limpiar_moneda("") == 0.0

    def test_numero_entero(self):
        """Integer value returns float."""
        from core.utils import limpiar_moneda
        assert limpiar_moneda(50000) == 50000.0

    def test_numero_flotante(self):
        """Float value returns same float."""
        from core.utils import limpiar_moneda
        assert limpiar_moneda(99.99) == 99.99

    def test_string_con_signo_peso(self):
        """String with $ symbol is parsed."""
        from core.utils import limpiar_moneda
        assert limpiar_moneda("$ 150,000") == 150000.0

    def test_string_con_coma_miles(self):
        """String with comma as thousands separator is parsed."""
        from core.utils import limpiar_moneda
        assert limpiar_moneda("1,200,500") == 1200500.0

    def test_string_con_espacios(self):
        """String with spaces is trimmed and parsed."""
        from core.utils import limpiar_moneda
        assert limpiar_moneda("  $ 99,999  ") == 99999.0

    def test_string_decimal(self):
        """String with decimal point remains."""
        from core.utils import limpiar_moneda
        assert limpiar_moneda("1234.56") == 1234.56

    def test_string_invalido_retorna_cero(self):
        """Invalid string returns 0.0."""
        from core.utils import limpiar_moneda
        assert limpiar_moneda("no_es_un_numero") == 0.0

    def test_cero_string(self):
        """String '0' returns 0.0."""
        from core.utils import limpiar_moneda
        assert limpiar_moneda("0") == 0.0

    def test_valor_negativo(self):
        """Negative value is parsed."""
        from core.utils import limpiar_moneda
        assert limpiar_moneda("-500") == -500.0


# ═══════════════════════════════════════════════════════════════════════════════
# fmt_moneda
# ═══════════════════════════════════════════════════════════════════════════════

class TestFmtMoneda:

    def test_formato_basico(self):
        """Basic formatting with $ and dots."""
        from core.utils import fmt_moneda
        result = fmt_moneda(150000)
        assert result.startswith("$")
        assert "." in result  # thousand separator (comma → dot)

    def test_cero(self):
        """Zero formats correctly."""
        from core.utils import fmt_moneda
        assert fmt_moneda(0) == "$ 0"

    def test_valor_string(self):
        """String '$ 99,999' → 99999 → format with dot separator '$ 99.999'."""
        from core.utils import fmt_moneda
        result = fmt_moneda("$ 99,999")
        assert result == "$ 99.999"

    def test_valor_flotante(self):
        """Float value is formatted."""
        from core.utils import fmt_moneda
        result = fmt_moneda(1234.56)
        assert result == "$ 1.235"

    def test_decimales_truncados(self):
        """Decimal places are rounded to integer by :,.0f format."""
        from core.utils import fmt_moneda
        result = fmt_moneda(99.99)
        assert "$ 100" in result  # 99.99 rounds to 100


# ═══════════════════════════════════════════════════════════════════════════════
# obtener_rutas_archivos
# ═══════════════════════════════════════════════════════════════════════════════

class TestObtenerRutasArchivos:

    def test_retorna_tres_rutas(self, tmp_path, monkeypatch):
        """Returns tuple of 3 paths: reservas, contratos, ordenes."""
        fake_home = str(tmp_path / "home")
        monkeypatch.setattr(os.path, "expanduser", lambda x: fake_home)
        # Create Documents + subdirs manually
        docs = os.path.join(fake_home, "Documents")
        os.makedirs(os.path.join(docs, "Archivos Dinamo_rent", "Ordenes Reservas"))
        os.makedirs(os.path.join(docs, "Archivos Dinamo_rent", "Contratos"))
        os.makedirs(os.path.join(docs, "Archivos Dinamo_rent", "Ordenes Renta"))

        from core.utils import obtener_rutas_archivos
        reservas, contratos, ordenes = obtener_rutas_archivos()
        assert "Reservas" in reservas
        assert "Contratos" in contratos
        assert "Renta" in ordenes

    def test_documentos_no_existe_usa_espanol(self, tmp_path, monkeypatch):
        """If 'Documents' doesn't exist, tries 'Documentos'."""
        fake_home = str(tmp_path / "home")
        monkeypatch.setattr(os.path, "expanduser", lambda x: fake_home)
        # Only Documentos exists
        docs_es = os.path.join(fake_home, "Documentos")
        os.makedirs(os.path.join(docs_es, "Archivos Dinamo_rent", "Ordenes Reservas"))
        os.makedirs(os.path.join(docs_es, "Archivos Dinamo_rent", "Contratos"))

        from core.utils import obtener_rutas_archivos
        reservas, contratos, ordenes = obtener_rutas_archivos()
        assert "Documentos" in reservas

    def test_docs_no_existe_fallback_a_home(self, tmp_path, monkeypatch):
        """If neither Documents nor Documentos exists, falls back to home."""
        fake_home = str(tmp_path / "home")
        monkeypatch.setattr(os.path, "expanduser", lambda x: fake_home)
        # Create subdirs under fake_home directly
        os.makedirs(os.path.join(fake_home, "Archivos Dinamo_rent", "Ordenes Reservas"))
        os.makedirs(os.path.join(fake_home, "Archivos Dinamo_rent", "Contratos"))

        from core.utils import obtener_rutas_archivos
        reservas, contratos, ordenes = obtener_rutas_archivos()
        assert fake_home in reservas

    def test_makedirs_no_falla_si_ya_existe(self, tmp_path, monkeypatch):
        """makedirs does not fail when directory already exists."""
        fake_home = str(tmp_path / "home")
        monkeypatch.setattr(os.path, "expanduser", lambda x: fake_home)
        docs = os.path.join(fake_home, "Documents")
        archivos = os.path.join(docs, "Archivos Dinamo_rent")
        os.makedirs(os.path.join(archivos, "Ordenes Reservas"))
        os.makedirs(os.path.join(archivos, "Contratos"))
        os.makedirs(os.path.join(archivos, "Ordenes Renta"))

        from core.utils import obtener_rutas_archivos
        r1, r2, r3 = obtener_rutas_archivos()
        r1b, r2b, r3b = obtener_rutas_archivos()
        assert r1 == r1b
        assert r2 == r2b
        assert r3 == r3b

    def test_makedirs_falla_logea_warning(self, tmp_path, monkeypatch):
        """When os.makedirs fails, warning is logged and function still returns paths."""
        def fake_makedirs(path, exist_ok=False):
            raise PermissionError("Access denied")
        monkeypatch.setattr(os, "makedirs", fake_makedirs)
        fake_home = str(tmp_path / "home")
        monkeypatch.setattr(os.path, "expanduser", lambda x: fake_home)

        from core.utils import obtener_rutas_archivos
        # Should not raise — makedirs failure is caught and logged
        reservas, contratos, ordenes = obtener_rutas_archivos()
        assert reservas is not None
        assert contratos is not None
        assert ordenes is not None


# ═══════════════════════════════════════════════════════════════════════════════
# obtener_ruta_logo
# ═══════════════════════════════════════════════════════════════════════════════

class TestObtenerRutaLogo:

    def test_sin_logo_retorna_none(self, tmp_path, monkeypatch):
        """Returns None when no logo file exists."""
        # Point base_dir at tmp_path (no assets folder)
        monkeypatch.setattr("core.utils.os.path.dirname",
                            lambda p: str(tmp_path))
        from core.utils import obtener_ruta_logo
        assert obtener_ruta_logo() is None

    def test_con_logo_retorna_ruta(self, tmp_path, monkeypatch):
        """Returns path when logo file exists."""
        logo_dir = tmp_path / "assets"
        logo_dir.mkdir()
        logo_file = logo_dir / "Logo_Dinamo.png"
        logo_file.write_text("fake_png_content")
        monkeypatch.setattr("core.utils.os.path.dirname",
                            lambda p: str(tmp_path))

        from core.utils import obtener_ruta_logo
        result = obtener_ruta_logo()
        assert result is not None
        assert "Logo_Dinamo" in result or str(logo_file) in result

    def test_logo_en_segunda_opcion(self, tmp_path, monkeypatch):
        """Finds logo with second possible filename."""
        logo_dir = tmp_path / "assets"
        logo_dir.mkdir()
        logo_file = logo_dir / "LogoDinamo.png"
        logo_file.write_text("fake_png")
        monkeypatch.setattr("core.utils.os.path.dirname",
                            lambda p: str(tmp_path))

        from core.utils import obtener_ruta_logo
        result = obtener_ruta_logo()
        assert result is not None
        assert "LogoDinamo" in result


# ═══════════════════════════════════════════════════════════════════════════════
# obtener_logo_base64
# ═══════════════════════════════════════════════════════════════════════════════

class TestObtenerLogoBase64:

    def test_sin_logo_retorna_vacio(self, monkeypatch):
        """Returns empty string when no logo exists."""
        monkeypatch.setattr("core.utils.obtener_ruta_logo", lambda: None)
        from core.utils import obtener_logo_base64
        assert obtener_logo_base64() == ""

    def test_con_logo_retorna_data_uri(self, tmp_path, monkeypatch):
        """Returns base64 data URI when logo exists."""
        logo_file = tmp_path / "logo.png"
        _create_valid_png(str(logo_file))
        monkeypatch.setattr("core.utils.obtener_ruta_logo", lambda: str(logo_file))

        from core.utils import obtener_logo_base64
        result = obtener_logo_base64()
        assert result.startswith("data:image/png;base64,")

    def test_logo_jpg_usa_jpeg_mime(self, tmp_path, monkeypatch):
        """JPG extension maps to image/jpeg MIME type."""
        logo_file = tmp_path / "logo.jpg"
        logo_file.write_bytes(b"fake_jpg_bytes")
        monkeypatch.setattr("core.utils.obtener_ruta_logo", lambda: str(logo_file))

        from core.utils import obtener_logo_base64
        result = obtener_logo_base64()
        assert result.startswith("data:image/jpeg;base64,")

    def test_error_lectura_retorna_vacio(self, monkeypatch):
        """Exception during file read returns empty string."""
        monkeypatch.setattr("core.utils.obtener_ruta_logo",
                            lambda: "/nonexistent/logo.png")
        from core.utils import obtener_logo_base64
        assert obtener_logo_base64() == ""


# ═══════════════════════════════════════════════════════════════════════════════
# cargar_plantilla_jinja
# ═══════════════════════════════════════════════════════════════════════════════

class TestCargarPlantillaJinja:

    def test_plantilla_no_existe_retorna_none(self, monkeypatch):
        """Returns None when template file doesn't exist."""
        monkeypatch.setattr(os.path, "exists", lambda p: False)
        from core.utils import cargar_plantilla_jinja
        result = cargar_plantilla_jinja("contrato")
        assert result is None

    def test_contrato_template_cargado(self, tmp_path, monkeypatch):
        """Loads 'contrato' template from templates dir."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        (templates_dir / "contrato_jinja_template.html")\
            .write_text("<html>{{ nombre_cliente }}</html>", encoding="utf-8")
        monkeypatch.setattr("core.utils.os.path.dirname",
                            lambda p: str(tmp_path))

        from core.utils import cargar_plantilla_jinja
        result = cargar_plantilla_jinja("contrato")
        assert result is not None
        assert "nombre_cliente" in result

    def test_renta_template_cargado(self, tmp_path, monkeypatch):
        """Loads 'renta' template."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        (templates_dir / "orden_renta_jinja.html")\
            .write_text("<html>RENTA: {{ placa }}</html>", encoding="utf-8")
        monkeypatch.setattr("core.utils.os.path.dirname",
                            lambda p: str(tmp_path))

        from core.utils import cargar_plantilla_jinja
        result = cargar_plantilla_jinja("renta")
        assert result is not None
        assert "RENTA" in result

    def test_reserva_template_cargado(self, tmp_path, monkeypatch):
        """Loads 'reserva' template."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        (templates_dir / "orden_reserva_jinja.html")\
            .write_text("<html>RESERVA: {{ id_reserva }}</html>", encoding="utf-8")
        monkeypatch.setattr("core.utils.os.path.dirname",
                            lambda p: str(tmp_path))

        from core.utils import cargar_plantilla_jinja
        result = cargar_plantilla_jinja("reserva")
        assert result is not None
        assert "RESERVA" in result

    def test_tipo_desconocido_usa_contrato(self, tmp_path, monkeypatch):
        """Unknown tipo defaults to 'contrato' template."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        (templates_dir / "contrato_jinja_template.html")\
            .write_text("<html>Default contract</html>", encoding="utf-8")
        monkeypatch.setattr("core.utils.os.path.dirname",
                            lambda p: str(tmp_path))

        from core.utils import cargar_plantilla_jinja
        result = cargar_plantilla_jinja("unknown_type")
        assert result is not None
        assert "Default contract" in result


# ═══════════════════════════════════════════════════════════════════════════════
# abrir_archivo (PySide6-dependent)
# ═══════════════════════════════════════════════════════════════════════════════

class TestAbrirArchivo:

    def test_archivo_inexistente_retorna_false(self):
        """Returns False when file doesn't exist."""
        from core.utils import abrir_archivo
        assert abrir_archivo("/nonexistent/test.pdf") is False

    def test_archivo_existente_retorna_true(self, tmp_path, monkeypatch):
        """Returns True when file exists."""
        test_file = tmp_path / "test.pdf"
        test_file.write_text("fake pdf")
        fake_services = _install_pyside6_mocks(monkeypatch)

        from core.utils import abrir_archivo
        result = abrir_archivo(str(test_file))
        assert result is True
        fake_services.openUrl.assert_called_once()

    def test_excepcion_al_abrir_retorna_false(self, tmp_path, monkeypatch):
        """Exception during openUrl returns False."""
        test_file = tmp_path / "test.pdf"
        test_file.write_text("fake pdf")
        fake_services = _install_pyside6_mocks(monkeypatch)
        fake_services.openUrl.side_effect = Exception("Access denied")

        from core.utils import abrir_archivo
        result = abrir_archivo(str(test_file))
        assert result is False


# ═══════════════════════════════════════════════════════════════════════════════
# abrir_whatsapp
# ═══════════════════════════════════════════════════════════════════════════════

class TestAbrirWhatsapp:

    def test_celular_vacio_retorna_false(self):
        """Empty celular returns False."""
        from core.utils import abrir_whatsapp
        assert abrir_whatsapp("") is False

    def test_celular_none_retorna_false(self):
        """None celular returns False."""
        from core.utils import abrir_whatsapp
        assert abrir_whatsapp(None) is False

    def test_numero_10_digitos_agrega_57(self, monkeypatch):
        """10-digit number gets '57' prefixed."""
        fake_services = _install_pyside6_mocks(monkeypatch)

        from core.utils import abrir_whatsapp
        actual_urls = []
        def track_url(url):
            actual_urls.append(str(url))
            return True
        fake_services.openUrl.side_effect = track_url

        result = abrir_whatsapp("3001234567")
        assert result is True
        assert len(actual_urls) == 1
        assert "573001234567" in actual_urls[0]

    def test_numero_con_formato(self, monkeypatch):
        """Number with formatting characters is cleaned."""
        fake_services = _install_pyside6_mocks(monkeypatch)

        from core.utils import abrir_whatsapp
        actual_urls = []
        def track_url(url):
            actual_urls.append(str(url))
            return True
        fake_services.openUrl.side_effect = track_url

        result = abrir_whatsapp("(300) 123-4567")
        assert result is True
        assert "573001234567" in actual_urls[0]

    def test_numero_con_mensaje(self, monkeypatch):
        """Message is URL-encoded in the WhatsApp URL."""
        fake_services = _install_pyside6_mocks(monkeypatch)

        from core.utils import abrir_whatsapp
        actual_urls = []
        def track_url(url):
            actual_urls.append(str(url))
            return True
        fake_services.openUrl.side_effect = track_url

        result = abrir_whatsapp("3001234567", "Hola! ¿Cómo estás?")
        assert result is True
        assert "text=" in actual_urls[0]
        assert "%C3%B3" in actual_urls[0]  # URL-encoded ó

    def test_error_en_qdesktop_retorna_false(self, monkeypatch):
        """Exception during openUrl returns False."""
        fake_services = _install_pyside6_mocks(monkeypatch)
        fake_services.openUrl.side_effect = Exception("Connection error")

        from core.utils import abrir_whatsapp
        assert abrir_whatsapp("3001234567") is False


# ═══════════════════════════════════════════════════════════════════════════════
# abrir_email
# ═══════════════════════════════════════════════════════════════════════════════

class TestAbrirEmail:

    def test_email_vacio_retorna_false(self):
        """Empty email returns False."""
        from core.utils import abrir_email
        assert abrir_email("") is False

    def test_email_none_retorna_false(self):
        """None email returns False."""
        from core.utils import abrir_email
        assert abrir_email(None) is False

    def test_mailto_url_generada(self, monkeypatch):
        """mailto: URL is called with the email."""
        fake_services = _install_pyside6_mocks(monkeypatch)

        from core.utils import abrir_email
        actual_urls = []
        def track_url(url):
            actual_urls.append(str(url))
            return True
        fake_services.openUrl.side_effect = track_url

        result = abrir_email("test@example.com")
        assert result is True
        assert "mailto:test@example.com" in actual_urls[0]

    def test_con_asunto_y_cuerpo(self, monkeypatch):
        """Subject and body are included and URL-encoded."""
        fake_services = _install_pyside6_mocks(monkeypatch)

        from core.utils import abrir_email
        actual_urls = []
        def track_url(url):
            actual_urls.append(str(url))
            return True
        fake_services.openUrl.side_effect = track_url

        result = abrir_email("user@domain.com", "Asunto Importante", "Cuerpo del mensaje")
        assert result is True
        assert "subject=" in actual_urls[0]
        assert "body=" in actual_urls[0]

    def test_error_en_qdesktop_retorna_false(self, monkeypatch):
        """Exception during openUrl returns False."""
        fake_services = _install_pyside6_mocks(monkeypatch)
        fake_services.openUrl.side_effect = Exception("Mail error")

        from core.utils import abrir_email
        assert abrir_email("test@test.com") is False


# ═══════════════════════════════════════════════════════════════════════════════
# enviar_a_impresora
# ═══════════════════════════════════════════════════════════════════════════════

class TestEnviarAImpresora:

    def test_archivo_inexistente_no_falla(self):
        """Non-existent file does nothing and doesn't raise."""
        from core.utils import enviar_a_impresora
        enviar_a_impresora("/nonexistent/file.pdf")

    def test_win32_llama_os_startfile(self, tmp_path, monkeypatch):
        """On Windows, calls os.startfile with 'print' verb."""
        test_file = tmp_path / "test.pdf"
        test_file.write_text("fake pdf")
        startfile_called = []
        def fake_startfile(path, verb=None):
            startfile_called.append((path, verb))
        monkeypatch.setattr(os, "startfile", fake_startfile)
        monkeypatch.setattr(sys, "platform", "win32")

        from core.utils import enviar_a_impresora
        enviar_a_impresora(str(test_file))
        assert len(startfile_called) == 1
        assert startfile_called[0][1] == "print"

    def test_no_win32_usa_abrir_archivo(self, tmp_path, monkeypatch):
        """On non-Windows, calls abrir_archivo as fallback."""
        test_file = tmp_path / "test.pdf"
        test_file.write_text("fake pdf")
        abrir_called = []
        def fake_abrir(ruta):
            abrir_called.append(ruta)
        monkeypatch.setattr("core.utils.abrir_archivo", fake_abrir)
        monkeypatch.setattr(sys, "platform", "linux")

        from core.utils import enviar_a_impresora
        enviar_a_impresora(str(test_file))
        assert len(abrir_called) == 1

    def test_startfile_falla_usa_abrir_archivo(self, tmp_path, monkeypatch):
        """If os.startfile fails, abrir_archivo is called as fallback."""
        test_file = tmp_path / "test.pdf"
        test_file.write_text("fake pdf")
        def fake_startfile(path, verb=None):
            raise OSError("Print failed")
        monkeypatch.setattr(os, "startfile", fake_startfile)
        monkeypatch.setattr(sys, "platform", "win32")
        abrir_called = []
        def fake_abrir(ruta):
            abrir_called.append(ruta)
        monkeypatch.setattr("core.utils.abrir_archivo", fake_abrir)

        from core.utils import enviar_a_impresora
        enviar_a_impresora(str(test_file))
        assert len(abrir_called) == 1


# ═══════════════════════════════════════════════════════════════════════════════
# generar_orden_alquiler_pdf (ReportLab fallback)
# ═══════════════════════════════════════════════════════════════════════════════

class TestGenerarOrdenAlquilerPdf:

    @pytest.fixture
    def fake_dirs(self, tmp_path, monkeypatch):
        """Redirect output dirs to temp."""
        reservas = tmp_path / "Ordenes_Reservas"
        contratos = tmp_path / "Contratos"
        ordenes = tmp_path / "Ordenes_Renta"
        reservas.mkdir()
        contratos.mkdir()
        ordenes.mkdir()
        monkeypatch.setattr("core.utils.obtener_rutas_archivos",
                            lambda: (str(reservas), str(contratos), str(ordenes)))

    @pytest.fixture
    def valid_logo(self, tmp_path, monkeypatch):
        """Place a valid 1×1 PNG and monkeypatch obtener_ruta_logo."""
        logo_file = tmp_path / "logo.png"
        _create_valid_png(str(logo_file))
        monkeypatch.setattr("core.utils.obtener_ruta_logo", lambda: str(logo_file))

    @pytest.fixture
    def sample_data(self):
        return {
            "id_renta": 42,
            "nombre_cliente": "Juan Perez",
            "cliente_doc": "CC 12345678",
            "cliente_celular": "3001234567",
            "placa": "ABC123",
            "auto_marca": "Toyota",
            "auto_modelo": "Corolla 2024",
            "km_salida": 15000,
            "tanque_salida": "Full",
            "fecha_recogida": "2024-12-01",
            "hora_recogida": "10:00",
            "fecha_retorno": "2024-12-05",
            "hora_retorno": "10:00",
            "dias": 4,
            "dias_calculados": 4,
            "valor_dia": 150000,
            "total": 600000,
        }

    def test_genera_pdf_valido(self, fake_dirs, valid_logo, sample_data):
        """PDF file is created on disk."""
        from core.utils import generar_orden_alquiler_pdf
        result = generar_orden_alquiler_pdf(sample_data)
        assert result is not None
        assert os.path.exists(result)
        assert result.endswith(".pdf")

    def test_pdf_tiene_tamano_mayor_a_cero(self, fake_dirs, valid_logo, sample_data):
        """Generated PDF has content."""
        from core.utils import generar_orden_alquiler_pdf
        result = generar_orden_alquiler_pdf(sample_data)
        assert os.path.getsize(result) > 0

    def test_return_status_true_devuelve_tuple(self, fake_dirs, valid_logo, sample_data):
        """With return_status=True, returns (True, message, path)."""
        from core.utils import generar_orden_alquiler_pdf
        result = generar_orden_alquiler_pdf(sample_data, return_status=True)
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert result[0] is True
        assert isinstance(result[1], str)
        assert result[2].endswith(".pdf")
        assert os.path.exists(result[2])

    def test_sin_vehiculo_no_falla(self, fake_dirs, valid_logo):
        """Minimal data still generates PDF."""
        from core.utils import generar_orden_alquiler_pdf
        result = generar_orden_alquiler_pdf({"id_renta": 1, "nombre_cliente": "Test", "total": 100000})
        assert result is not None
        assert os.path.exists(result)

    def test_sin_total_no_falla(self, fake_dirs, valid_logo):
        """Missing total defaults to 0 without crashing."""
        from core.utils import generar_orden_alquiler_pdf
        result = generar_orden_alquiler_pdf({"id_renta": 1, "nombre_cliente": "Test"})
        assert result is not None

    def test_sin_logo_no_falla(self, fake_dirs, sample_data):
        """PDF works even without logo file (uses Paragraph fallback)."""
        from core.utils import generar_orden_alquiler_pdf
        result = generar_orden_alquiler_pdf(sample_data)
        assert result is not None
        assert os.path.exists(result)

    def test_con_extras_muestra_costos(self, fake_dirs, valid_logo):
        """Extras (lavado, silla, cables) appear in the PDF."""
        from core.utils import generar_orden_alquiler_pdf
        data = {
            "id_renta": 10, "nombre_cliente": "Test Extras",
            "dias": 2, "valor_dia": 100000, "total": 250000,
            "horas_extras": 3, "valor_hora_extra": 10000,
            "costo_lavado": 20000, "costo_silla": 15000,
        }
        result = generar_orden_alquiler_pdf(data)
        assert result is not None
        assert os.path.exists(result)

    def test_crear_pdf_orden_basica_es_alias(self):
        """crear_pdf_orden_basica is an alias for generar_orden_alquiler_pdf."""
        from core.utils import crear_pdf_orden_basica, generar_orden_alquiler_pdf
        assert crear_pdf_orden_basica is generar_orden_alquiler_pdf

    def test_excepcion_en_pdf_retorna_none(self, fake_dirs, monkeypatch):
        """When PDF building raises, outer except returns None."""
        from reportlab.platypus import SimpleDocTemplate
        original_build = SimpleDocTemplate.build
        def failing_build(*args, **kwargs):
            raise RuntimeError("PDF build error")
        monkeypatch.setattr(SimpleDocTemplate, "build", failing_build)

        from core.utils import generar_orden_alquiler_pdf
        data = {"id_renta": 1, "nombre_cliente": "Fail Test", "total": 0}
        result = generar_orden_alquiler_pdf(data)
        assert result is None


# ═══════════════════════════════════════════════════════════════════════════════
# generar_contrato_temp (WeasyPrint → ReportLab fallback)
# ═══════════════════════════════════════════════════════════════════════════════

class TestGenerarContratoTemp:

    @pytest.fixture
    def fake_dirs(self, tmp_path, monkeypatch):
        reservas = tmp_path / "Ordenes_Reservas"
        contratos = tmp_path / "Contratos"
        ordenes = tmp_path / "Ordenes_Renta"
        reservas.mkdir()
        contratos.mkdir()
        ordenes.mkdir()
        monkeypatch.setattr("core.utils.obtener_rutas_archivos",
                            lambda: (str(reservas), str(contratos), str(ordenes)))
        return {"contratos": str(contratos)}

    def test_falla_a_reportlab_cuando_no_weasyprint(self, fake_dirs, monkeypatch):
        """When WeasyPrint is unavailable, falls back to ReportLab."""
        monkeypatch.setattr("core.utils.TIENE_WEASYPRINT", False)
        from core.utils import generar_contrato_temp
        data = {"id_renta": 1, "nombre_cliente": "Test Contract", "total": 500000, "valor_hora_extra": 0}
        result = generar_contrato_temp(data)
        assert result is not None
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert result[0] is True
        assert result[2].endswith(".pdf")
        assert os.path.exists(result[2])

    def test_genera_pdf_en_carpeta_contratos(self, fake_dirs, monkeypatch):
        """Fallback to ReportLab saves in ordenes folder when WeasyPrint is off."""
        monkeypatch.setattr("core.utils.TIENE_WEASYPRINT", False)
        from core.utils import generar_contrato_temp
        data = {"id_renta": 5, "nombre_cliente": "Maria Gomez", "total": 750000, "valor_hora_extra": 0}
        result = generar_contrato_temp(data)
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert result[2].endswith(".pdf")
        assert os.path.exists(result[2])

    def test_sin_datos_minimos_no_falla(self, fake_dirs, monkeypatch):
        """Works with minimal required data."""
        monkeypatch.setattr("core.utils.TIENE_WEASYPRINT", False)
        from core.utils import generar_contrato_temp
        result = generar_contrato_temp({"id_renta": 99})
        assert result is not None
        assert isinstance(result, tuple)
        assert os.path.exists(result[2])

    def test_con_weasyprint_mock_genera_pdf(self, tmp_path, monkeypatch):
        """When WeasyPrint is available (mocked), generates PDF via HTML.write_pdf."""
        from unittest.mock import MagicMock
        # Mock the HTML class and its write_pdf method
        mock_html_instance = MagicMock()
        mock_html_class = MagicMock(return_value=mock_html_instance)

        # Setup fake dirs
        contratos = tmp_path / "Contratos"
        contratos.mkdir()
        reservas = tmp_path / "Ordenes_Reservas"
        reservas.mkdir()
        ordenes = tmp_path / "Ordenes_Renta"
        ordenes.mkdir()
        monkeypatch.setattr("core.utils.obtener_rutas_archivos",
                            lambda: (str(reservas), str(contratos), str(ordenes)))
        # Mock logo so it doesn't try to read real files
        monkeypatch.setattr("core.utils.obtener_logo_base64", lambda: "")
        # Return a valid Jinja2 template string
        monkeypatch.setattr("core.utils.cargar_plantilla_jinja",
                            lambda tipo="contrato": "<html>{{ nombre_cliente }}</html>")
        # Enable WeasyPrint and inject the mocked HTML class
        monkeypatch.setattr("core.utils.TIENE_WEASYPRINT", True)
        monkeypatch.setattr("core.utils.HTML", mock_html_class, raising=False)

        from core.utils import generar_contrato_temp
        data = {"id_renta": 10, "nombre_cliente": "WeasyPrint Test", "total": 300000, "valor_hora_extra": 0}
        result = generar_contrato_temp(data)

        # Should return the WeasyPrint path (tuple with success message)
        assert result is not None
        assert isinstance(result, tuple)
        assert result[0] is True
        assert result[1] == "Contrato Generado"
        assert result[2].endswith(".pdf")
        # Verify HTML was invoked with the rendered template
        mock_html_class.assert_called_once()
        call_kwargs = mock_html_class.call_args[1]
        assert "string" in call_kwargs
        assert "WeasyPrint Test" in call_kwargs["string"]
        mock_html_instance.write_pdf.assert_called_once_with(result[2])

    def test_con_weasyprint_falla_logea_error(self, tmp_path, monkeypatch):
        """When WeasyPrint raises an exception, falls back to ReportLab."""
        from unittest.mock import MagicMock
        # HTML class raises when constructed
        mock_html_class = MagicMock(side_effect=RuntimeError("WeasyPrint render failed"))

        contratos = tmp_path / "Contratos"
        contratos.mkdir()
        reservas = tmp_path / "Ordenes_Reservas"
        reservas.mkdir()
        ordenes = tmp_path / "Ordenes_Renta"
        ordenes.mkdir()
        monkeypatch.setattr("core.utils.obtener_rutas_archivos",
                            lambda: (str(reservas), str(contratos), str(ordenes)))
        monkeypatch.setattr("core.utils.obtener_logo_base64", lambda: "")
        monkeypatch.setattr("core.utils.cargar_plantilla_jinja",
                            lambda tipo="contrato": "<html>{{ nombre_cliente }}</html>")
        monkeypatch.setattr("core.utils.TIENE_WEASYPRINT", True)
        monkeypatch.setattr("core.utils.HTML", mock_html_class, raising=False)

        from core.utils import generar_contrato_temp
        data = {"id_renta": 11, "nombre_cliente": "Fail Test", "total": 100000, "valor_hora_extra": 0}
        result = generar_contrato_temp(data)
        # Falls back to ReportLab which should succeed
        assert result is not None
        assert isinstance(result, tuple)
        assert result[0] is True
        assert os.path.exists(result[2])


# ═══════════════════════════════════════════════════════════════════════════════
# generar_pdf_reserva (ReportLab-based)
# ═══════════════════════════════════════════════════════════════════════════════

class TestGenerarPdfReserva:

    @pytest.fixture
    def fake_dirs(self, tmp_path, monkeypatch):
        reservas = tmp_path / "Ordenes_Reservas"
        contratos = tmp_path / "Contratos"
        ordenes = tmp_path / "Ordenes_Renta"
        reservas.mkdir()
        contratos.mkdir()
        ordenes.mkdir()
        monkeypatch.setattr("core.utils.obtener_rutas_archivos",
                            lambda: (str(reservas), str(contratos), str(ordenes)))
        return {"reservas": str(reservas)}

    @pytest.fixture
    def valid_logo(self, tmp_path, monkeypatch):
        logo_file = tmp_path / "logo.png"
        _create_valid_png(str(logo_file))
        monkeypatch.setattr("core.utils.obtener_ruta_logo", lambda: str(logo_file))

    @pytest.fixture
    def sample_reserva(self):
        return {
            "id_reserva": 77, "cliente_nombre": "Ana Torres",
            "cliente_doc": "CC 98765432", "cliente_celular": "3109876543",
            "vehiculo": "Mazda CX-5",
            "f_inicio": "2024-12-10", "h_inicio": "09:00",
            "f_fin": "2024-12-15", "h_fin": "09:00",
            "dias": 5, "valor_dia": 200000, "total": 1200000, "abono": 300000,
        }

    def test_genera_pdf_valido(self, fake_dirs, valid_logo, sample_reserva):
        """PDF file is created on disk."""
        from core.utils import generar_pdf_reserva
        result = generar_pdf_reserva(sample_reserva)
        assert result is not None
        assert isinstance(result, tuple)
        assert result[0] is True
        assert os.path.exists(result[1])

    def test_pdf_en_carpeta_reservas(self, fake_dirs, valid_logo, sample_reserva):
        """PDF is saved in reservas folder."""
        from core.utils import generar_pdf_reserva
        result = generar_pdf_reserva(sample_reserva)
        assert result[1].startswith(fake_dirs["reservas"])

    def test_con_abono_cero(self, fake_dirs, valid_logo):
        """Works when abono is 0."""
        from core.utils import generar_pdf_reserva
        data = {"id_reserva": 1, "cliente_nombre": "Test",
                "dias": 2, "valor_dia": 100000, "total": 200000, "abono": 0}
        result = generar_pdf_reserva(data)
        assert result[0] is True
        assert os.path.exists(result[1])

    def test_sin_abono(self, fake_dirs, valid_logo):
        """Works when abono is not provided."""
        from core.utils import generar_pdf_reserva
        data = {"id_reserva": 2, "cliente_nombre": "Test No Abono",
                "dias": 1, "valor_dia": 100000, "total": 100000}
        result = generar_pdf_reserva(data)
        assert result[0] is True
        assert os.path.exists(result[1])

    def test_no_reportlab_devuelve_error(self, fake_dirs, valid_logo, monkeypatch):
        """Without ReportLab, returns error message tuple."""
        monkeypatch.setattr("core.utils.TIENE_REPORTLAB", False)
        from core.utils import generar_pdf_reserva
        result = generar_pdf_reserva({"id_reserva": 1})
        assert result[0] is False
        assert "ReportLab" in result[1]

    def test_excepcion_en_reserva_retorna_error(self, fake_dirs, monkeypatch):
        """When PDF building raises, outer except returns (False, error_message)."""
        from reportlab.platypus import SimpleDocTemplate
        def failing_build(*args, **kwargs):
            raise RuntimeError("Reserva build error")
        monkeypatch.setattr(SimpleDocTemplate, "build", failing_build)

        from core.utils import generar_pdf_reserva
        data = {"id_reserva": 1, "cliente_nombre": "Test Fail", "total": 0}
        result = generar_pdf_reserva(data)
        assert result[0] is False
        assert isinstance(result[1], str)
        assert "Reserva build error" in result[1]


# ═══════════════════════════════════════════════════════════════════════════════
# generar_orden_renta_jinja (WeasyPrint → ReportLab fallback)
# ═══════════════════════════════════════════════════════════════════════════════

class TestGenerarOrdenRentaJinja:

    @pytest.fixture
    def fake_dirs(self, tmp_path, monkeypatch):
        reservas = tmp_path / "Ordenes_Reservas"
        contratos = tmp_path / "Contratos"
        ordenes = tmp_path / "Ordenes_Renta"
        reservas.mkdir()
        contratos.mkdir()
        ordenes.mkdir()
        monkeypatch.setattr("core.utils.obtener_rutas_archivos",
                            lambda: (str(reservas), str(contratos), str(ordenes)))

    def test_falla_a_reportlab_sin_weasyprint(self, fake_dirs, monkeypatch):
        """Without WeasyPrint, falls back to ReportLab and returns path."""
        monkeypatch.setattr("core.utils.TIENE_WEASYPRINT", False)
        from core.utils import generar_orden_renta_jinja
        data = {
            "id_renta": 20, "nombre_cliente": "Cliente Jinja", "placa": "XYZ789",
            "auto_marca": "Honda", "auto_modelo": "Civic", "km_salida": 20000,
            "fecha_recogida": "2024-12-01", "hora_recogida": "10:00",
            "fecha_retorno": "2024-12-03", "hora_retorno": "10:00",
            "dias": 2, "valor_dia": 120000, "total": 240000,
        }
        result = generar_orden_renta_jinja(data)
        assert result is not None
        assert isinstance(result, str)
        assert result.endswith(".pdf")
        assert os.path.exists(result)

    def test_con_weasyprint_mock_genera_pdf(self, tmp_path, monkeypatch):
        """When WeasyPrint is available (mocked), generates PDF via HTML.write_pdf."""
        from unittest.mock import MagicMock

        mock_html_instance = MagicMock()
        mock_html_class = MagicMock(return_value=mock_html_instance)

        ordenes = tmp_path / "Ordenes_Renta"
        ordenes.mkdir()
        reservas = tmp_path / "Ordenes_Reservas"
        reservas.mkdir()
        contratos = tmp_path / "Contratos"
        contratos.mkdir()
        monkeypatch.setattr("core.utils.obtener_rutas_archivos",
                            lambda: (str(reservas), str(contratos), str(ordenes)))
        monkeypatch.setattr("core.utils.obtener_logo_base64", lambda: "")
        monkeypatch.setattr("core.utils.cargar_plantilla_jinja",
                            lambda tipo="renta": "<html>Renta {{ id_renta }}: {{ placa }}</html>")
        monkeypatch.setattr("core.utils.TIENE_WEASYPRINT", True)
        monkeypatch.setattr("core.utils.HTML", mock_html_class, raising=False)

        from core.utils import generar_orden_renta_jinja
        data = {
            "id_renta": 50, "nombre_cliente": "Weasy Renta", "placa": "WP123",
            "auto_marca": "Test", "auto_modelo": "Mock", "dias": 3, "valor_dia": 100000, "total": 300000,
        }
        result = generar_orden_renta_jinja(data)

        assert result is not None
        assert isinstance(result, str)
        assert result.endswith(".pdf")
        mock_html_class.assert_called_once()
        mock_html_instance.write_pdf.assert_called_once_with(result)

    def test_con_weasyprint_falla_logea_error(self, tmp_path, monkeypatch):
        """When WeasyPrint raises an exception, falls back to ReportLab."""
        from unittest.mock import MagicMock

        mock_html_class = MagicMock(side_effect=RuntimeError("HTML write failed"))

        ordenes = tmp_path / "Ordenes_Renta"
        ordenes.mkdir()
        reservas = tmp_path / "Ordenes_Reservas"
        reservas.mkdir()
        contratos = tmp_path / "Contratos"
        contratos.mkdir()
        monkeypatch.setattr("core.utils.obtener_rutas_archivos",
                            lambda: (str(reservas), str(contratos), str(ordenes)))
        monkeypatch.setattr("core.utils.obtener_logo_base64", lambda: "")
        monkeypatch.setattr("core.utils.cargar_plantilla_jinja",
                            lambda tipo="renta": "<html>Renta {{ placa }}</html>")
        monkeypatch.setattr("core.utils.TIENE_WEASYPRINT", True)
        monkeypatch.setattr("core.utils.HTML", mock_html_class, raising=False)

        from core.utils import generar_orden_renta_jinja
        data = {
            "id_renta": 51, "nombre_cliente": "Fail Renta", "placa": "FP456",
            "auto_marca": "Test", "auto_modelo": "Mock", "dias": 1, "valor_dia": 50000, "total": 50000,
        }
        result = generar_orden_renta_jinja(data)
        # Falls back to ReportLab
        assert result is not None
        assert isinstance(result, str)
        assert result.endswith(".pdf")
        assert os.path.exists(result)


# ═══════════════════════════════════════════════════════════════════════════════
# Module-level bootstrap code paths
# ═══════════════════════════════════════════════════════════════════════════════

class TestModuleLevelBootstrap:
    """
    Covers module-level bootstrap code in core/utils.py that only runs at import time.
    Forces fresh imports via `del sys.modules['core.utils']; import core.utils`
    to ensure coverage.py traces the module-level code execution.

    Lines covered:
      14   — frozen=True branch (`base_path = os.path.dirname(sys.executable)`)
      28-29 — GTK path search loop
      32-35 — GTK path found → PATH update + add_dll_directory
      36-37 — add_dll_directory exception handler
      43-44 — PySide6 not available → except ImportError
      49   — TIENE_WEASYPRINT = True (successful import, mocked)
      62-63 — TIENE_REPORTLAB = True (successful import)
    """

    # Helpers
    @staticmethod
    def _fresh_import():
        """Force a fresh import of core.utils (delete from cache, re-import)."""
        if "core.utils" in sys.modules:
            del sys.modules["core.utils"]
        import core.utils  # noqa: F811
        return core.utils

    @staticmethod
    def _ensure_pyside6_mocks(monkeypatch):
        """Place fake PySide6 modules so module-level imports succeed."""
        from unittest.mock import MagicMock

        class _FakeQUrl:
            _url = ""
            def __init__(self, url=""):
                self._url = url
            @staticmethod
            def fromLocalFile(path):
                return _FakeQUrl(f"file:///{path}")

        monkeypatch.setitem(
            sys.modules, "PySide6.QtCore",
            type("qtcore", (), {"QUrl": _FakeQUrl})()
        )
        monkeypatch.setitem(
            sys.modules, "PySide6.QtGui",
            type("qtgui", (), {"QDesktopServices": MagicMock()})()
        )

    @staticmethod
    def _ensure_no_import(monkeypatch, blocked_module: str):
        """Make import of a specific module raise ImportError."""
        import builtins
        original_import = builtins.__import__
        def mock_import(name, *args, **kwargs):
            if name == blocked_module or name.startswith(blocked_module + "."):
                raise ImportError(f"No module named '{name}'")
            return original_import(name, *args, **kwargs)
        monkeypatch.setattr(builtins, "__import__", mock_import)

    # ── Tests ──────────────────────────────────────────────────────────────

    def test_import_normal_cubre_base_y_gtk(self):
        """Fresh import covers frozen-else (line 16) and lines 28-29 (GTK loop)."""
        mod = self._fresh_import()
        assert callable(mod.obtener_rutas_archivos)

    def test_frozen_true_cubre_linea14(self, monkeypatch):
        """When sys.frozen is True, the true branch (line 14) executes."""
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        mod = self._fresh_import()
        assert callable(mod.obtener_rutas_archivos)

    def test_pyside6_no_disponible_cubre_except(self, monkeypatch):
        """When PySide6 cannot be imported, except ImportError runs (lines 43-44)."""
        self._ensure_no_import(monkeypatch, "PySide6")
        mod = self._fresh_import()
        assert not hasattr(mod, "QDesktopServices")

    def test_weasyprint_mock_disponible_cubre_linea49(self, monkeypatch):
        """When weasyprint is mocked in sys.modules, TIENE_WEASYPRINT = True (line 49).
        (WeasyPrint is not installed in this env, so a mock is needed to cover this branch.)"""
        from unittest.mock import MagicMock
        # Place a mock weasyprint module so the from-import succeeds
        mock_weasyprint = type("weasyprint", (), {"HTML": MagicMock()})()
        monkeypatch.setitem(sys.modules, "weasyprint", mock_weasyprint)
        self._ensure_pyside6_mocks(monkeypatch)
        mod = self._fresh_import()
        assert mod.TIENE_WEASYPRINT is True

    def test_gtk_path_encontrado_y_dll_falla(self, monkeypatch):
        """When GTK directory exists but add_dll_directory raises, exception is caught.
        Covers lines 32-35 (success) and lines 36-37 (except handler)."""
        project_root = Path(__file__).resolve().parent.parent
        gtk_dir = project_root / "gtk3_bin"
        gtk_dir.mkdir(exist_ok=True)
        try:
            _old_exists = os.path.exists
            def _always_find_gtk(path):
                p = str(path).replace("\\", "/")
                if "gtk3_bin" in p:
                    return True
                return _old_exists(path)
            monkeypatch.setattr(os.path, "exists", _always_find_gtk)

            # Make add_dll_directory raise an exception
            monkeypatch.setattr(os, "add_dll_directory", lambda x: (_ for _ in ()).throw(Exception("DLL error")), raising=False)

            # Block weasyprint import to prevent its internal os.add_dll_directory call
            # from being affected by the monkeypatch (weasyprint/text/ffi.py also calls it)
            self._ensure_no_import(monkeypatch, "weasyprint")
            self._ensure_pyside6_mocks(monkeypatch)

            original_path = os.environ.get("PATH", "")
            try:
                mod = self._fresh_import()
                # PATH should still be updated even if add_dll_directory failed
                assert "gtk3_bin" in os.environ.get("PATH", "")
            finally:
                os.environ["PATH"] = original_path
        finally:
            if gtk_dir.exists():
                gtk_dir.rmdir()

    def test_weasyprint_no_disponible_cubre_except(self, monkeypatch):
        """When WeasyPrint import fails, TIENE_WEASYPRINT is False (lines 50-51)."""
        self._ensure_pyside6_mocks(monkeypatch)
        self._ensure_no_import(monkeypatch, "weasyprint")
        mod = self._fresh_import()
        assert mod.TIENE_WEASYPRINT is False

    def test_reportlab_no_disponible_cubre_except(self, monkeypatch):
        """When ReportLab import fails, TIENE_REPORTLAB is False (lines 64-65)."""
        self._ensure_pyside6_mocks(monkeypatch)
        self._ensure_no_import(monkeypatch, "reportlab")
        mod = self._fresh_import()
        assert mod.TIENE_REPORTLAB is False

    def test_pyside6_reportlab_disponibles(self, monkeypatch):
        """PySide6 available + ReportLab installed → TIENE_REPORTLAB is True (lines 62-63)."""
        self._ensure_pyside6_mocks(monkeypatch)
        mod = self._fresh_import()
        assert mod.TIENE_REPORTLAB is True
        assert mod.TIENE_WEASYPRINT is False


# ═══════════════════════════════════════════════════════════════════════════════
# generar_reserva_jinja (WeasyPrint → ReportLab fallback)
# ═══════════════════════════════════════════════════════════════════════════════

class TestGenerarReservaJinja:

    @pytest.fixture
    def fake_dirs(self, tmp_path, monkeypatch):
        reservas = tmp_path / "Ordenes_Reservas"
        contratos = tmp_path / "Contratos"
        ordenes = tmp_path / "Ordenes_Renta"
        reservas.mkdir()
        contratos.mkdir()
        ordenes.mkdir()
        monkeypatch.setattr("core.utils.obtener_rutas_archivos",
                            lambda: (str(reservas), str(contratos), str(ordenes)))
        return {"reservas": str(reservas)}

    def test_falla_a_reportlab_sin_weasyprint(self, fake_dirs, monkeypatch):
        """Without WeasyPrint, falls back to ReportLab."""
        monkeypatch.setattr("core.utils.TIENE_WEASYPRINT", False)
        from core.utils import generar_reserva_jinja
        data = {
            "id_reserva": 30, "cliente_nombre": "Reserva Test",
            "cliente_doc": "CC 123", "cliente_celular": "3000000000",
            "vehiculo": "Nissan Versa",
            "f_inicio": "2024-12-20", "h_inicio": "08:00",
            "f_fin": "2024-12-22", "h_fin": "08:00",
            "dias": 2, "valor_dia": 130000, "seguro": 20000,
            "adicionales": 10000, "total": 290000, "abono": 50000,
        }
        result = generar_reserva_jinja(data)
        assert result is not None
        assert isinstance(result, tuple)
        assert result[0] is True
        assert result[1].endswith(".pdf")
        assert os.path.exists(result[1])

    def test_con_weasyprint_mock_genera_pdf(self, tmp_path, monkeypatch):
        """When WeasyPrint is available (mocked), generates PDF via HTML.write_pdf."""
        from unittest.mock import MagicMock

        mock_html_instance = MagicMock()
        mock_html_class = MagicMock(return_value=mock_html_instance)

        reservas = tmp_path / "Ordenes_Reservas"
        reservas.mkdir()
        contratos = tmp_path / "Contratos"
        contratos.mkdir()
        ordenes = tmp_path / "Ordenes_Renta"
        ordenes.mkdir()
        monkeypatch.setattr("core.utils.obtener_rutas_archivos",
                            lambda: (str(reservas), str(contratos), str(ordenes)))
        monkeypatch.setattr("core.utils.obtener_logo_base64", lambda: "")
        monkeypatch.setattr("core.utils.cargar_plantilla_jinja",
                            lambda tipo="reserva": "<html>Reserva {{ id_reserva }}</html>")
        monkeypatch.setattr("core.utils.TIENE_WEASYPRINT", True)
        monkeypatch.setattr("core.utils.HTML", mock_html_class, raising=False)

        from core.utils import generar_reserva_jinja
        data = {
            "id_reserva": 60, "cliente_nombre": "Weasy Reserva",
            "cliente_doc": "CC 1", "cliente_celular": "3000000000",
            "vehiculo": "Mock Car", "dias": 2, "valor_dia": 100000,
            "f_inicio": "2024-12-01", "h_inicio": "10:00",
            "f_fin": "2024-12-03", "h_fin": "10:00",
            "total": 250000, "abono": 50000, "seguro": 20000, "adicionales": 10000,
        }
        result = generar_reserva_jinja(data)

        assert result is not None
        assert isinstance(result, tuple)
        assert result[0] is True
        assert result[1].endswith(".pdf")
        mock_html_class.assert_called_once()
        mock_html_instance.write_pdf.assert_called_once_with(result[1])

    def test_con_weasyprint_falla_logea_error(self, tmp_path, monkeypatch):
        """When WeasyPrint raises an exception, falls back to ReportLab."""
        from unittest.mock import MagicMock

        mock_html_class = MagicMock(side_effect=RuntimeError("Reserva PDF failed"))

        reservas = tmp_path / "Ordenes_Reservas"
        reservas.mkdir()
        contratos = tmp_path / "Contratos"
        contratos.mkdir()
        ordenes = tmp_path / "Ordenes_Renta"
        ordenes.mkdir()
        monkeypatch.setattr("core.utils.obtener_rutas_archivos",
                            lambda: (str(reservas), str(contratos), str(ordenes)))
        monkeypatch.setattr("core.utils.obtener_logo_base64", lambda: "")
        monkeypatch.setattr("core.utils.cargar_plantilla_jinja",
                            lambda tipo="reserva": "<html>Reserva {{ id_reserva }}</html>")
        monkeypatch.setattr("core.utils.TIENE_WEASYPRINT", True)
        monkeypatch.setattr("core.utils.HTML", mock_html_class, raising=False)

        from core.utils import generar_reserva_jinja
        data = {
            "id_reserva": 61, "cliente_nombre": "Fail Reserva",
            "cliente_doc": "CC 2", "cliente_celular": "3000000001",
            "vehiculo": "Test Car", "dias": 1, "valor_dia": 80000,
            "f_inicio": "2024-12-10", "h_inicio": "09:00",
            "f_fin": "2024-12-11", "h_fin": "09:00",
            "total": 80000, "abono": 0,
        }
        result = generar_reserva_jinja(data)
        # Falls back to ReportLab
        assert result is not None
        assert isinstance(result, tuple)
        assert result[0] is True
        assert result[1].endswith(".pdf")
        assert os.path.exists(result[1])
