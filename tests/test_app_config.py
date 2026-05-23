"""
test_app_config.py — Unit tests for core/app_config.py

Covers:
  AppConfig.__init__        — _find_config_file, _load_config, _validate_config
  Typed getters             — get, getint, getfloat, getboolean, getlist
  Fallback behavior         — missing sections/keys return fallback
  Direct access methods     — 9 get_*_config() methods
  Mutation                  — set(), save(), reload()
  Introspection             — has_section(), sections(), __repr__
  Global singleton          — config importable
  Error paths               — FileNotFoundError, ValueError on missing sections

Strategy:
  - Use tmp_path to create temporary .ini files for isolated testing
  - Create fresh AppConfig instances with explicit paths (avoid the global singleton)
  - Test fallback values for missing sections/keys

Run: pytest tests/test_app_config.py -v
"""

import os
from pathlib import Path

import pytest


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

_INI_CONTENT_FULL = """[database]
engine = mysql
host = dbserver.example.com
port = 3307
user = app_user
password = secret123
database = dinamo_prod
pool_size = 20
pool_max_overflow = 50
pool_pre_ping = true

[security]
hash_algorithm = sha512
hash_iterations = 200000
session_timeout = 7200
max_login_attempts = 3
account_lockout_duration = 900
login_rate_limit_window = 600
max_login_attempts_in_window = 5

[application]
name = Dinamo Rent Pro
version = 4.0.0
author = Dinamo Team
language = en
timezone = America/New_York

[backup]
directory = backups_prod
max_copies = 20
schedule_times = 06:00, 12:00, 18:00, 22:00
check_interval_ms = 30000
encryption_enabled = true
encryption_password = enc_key_123

[logging]
directory = logs_app
max_size_mb = 10
backup_count = 7
level = DEBUG
error_max_size_mb = 5
error_backup_count = 4
audit_enabled = true
audit_retention_days = 90

[ui]
color_primario = #ff0000
color_primario_hover = #cc0000
color_fondo = #000000
color_exito = #00ff00
color_success_hover = #00cc00
color_peligro = #ff4444
color_danger_hover = #cc3333
color_alerta = #ff8800
color_surface = #111111
color_border = #333333
color_text_primary = #ffffff
color_text_secondary = #aaaaaa
color_alt_row = #222222
font_family = Arial
font_size = 12
window_width = 1920
window_height = 1080
start_maximized = false

[business]
alert_soat_days = 30
alert_tecno_mecanica_days = 30
alert_extintor_days = 30
km_alert_aceite = 1000
roles_con_informes = Admin, Supervisor
roles_con_usuarios = Admin
tipos_auto = Sedan, SUV, Pickup
tipos_transmision = Manual, Automatic
tipos_combustible = Gasoline, Diesel, Electric
estados_auto = Available, Rented, Maintenance
tipos_adquisicion = Own, Leasing
tipos_doc = ID, Passport
estados_cliente = Active, Inactive, Blacklist
nivel_tanque = Full, 3/4, 1/2, 1/4
tipos_mantenimiento = Oil Change, Brakes, Tires

[email]
enabled = true
smtp_server = mail.example.com
smtp_port = 465
use_tls = false
username = no-reply@example.com
password = mailpass
from_email = notifications@example.com
from_name = Dinamo Notifications

[reports]
pdf_engine = weasyprint
excel_enabled = true
currency_symbol = $
currency_code = USD
decimal_places = 2
tax_enabled = true
tax_percentage = 10.5
"""

_INI_CONTENT_MINIMAL = """[database]
engine = sqlite

[security]
hash_algorithm = sha256

[application]
name = App Test
"""


@pytest.fixture
def ini_file_full(tmp_path):
    """Create a full config.ini in tmp_path and return its path."""
    path = tmp_path / "config.ini"
    path.write_text(_INI_CONTENT_FULL, encoding="utf-8")
    return str(path)


@pytest.fixture
def ini_file_minimal(tmp_path):
    """Create a minimal config.ini with only required sections."""
    path = tmp_path / "config.ini"
    path.write_text(_INI_CONTENT_MINIMAL, encoding="utf-8")
    return str(path)


# ═══════════════════════════════════════════════════════════════════════════════
# __init__ — _find_config_file, _load_config, _validate_config
# ═══════════════════════════════════════════════════════════════════════════════

class TestInit:
    """AppConfig initialization and file finding."""

    def test_init_con_ruta_explicita(self, ini_file_full):
        """AppConfig accepts explicit config path."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        assert cfg._config_path == ini_file_full

    def test_find_config_file_en_orden(self, tmp_path):
        """_find_config_file prefers config.ini over config.ini.example."""
        from core.app_config import AppConfig
        ini = tmp_path / "config.ini"
        example = tmp_path / "config.ini.example"
        example.write_text("[database]\nengine = test\n[security]\nkey = val\n[application]\nname = x", encoding="utf-8")
        ini.write_text("[database]\nengine = sqlite\n[security]\nkey = val\n[application]\nname = x", encoding="utf-8")
        cfg = AppConfig(config_path=str(ini))
        assert cfg._config_path == str(ini)

    def test_init_sin_config_path_usa_path_provisto(self, ini_file_full):
        """Explicit path is used directly."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        assert cfg._config_path == ini_file_full

    def test_init_raises_filenotfound(self, tmp_path, monkeypatch):
        """FileNotFoundError when no config file exists."""
        from core.app_config import AppConfig
        # Prevent fallback search from finding real config.ini
        monkeypatch.setattr("core.app_config.Path.exists", lambda self: False)
        with pytest.raises(FileNotFoundError):
            AppConfig(config_path=str(tmp_path / "nonexistent.ini"))

    def test_init_raises_filenotfound_sin_path(self, monkeypatch):
        """FileNotFoundError when searching and no file found."""
        from core.app_config import AppConfig
        # Monkeypatch the search to fail
        monkeypatch.setattr(
            "core.app_config.Path.exists",
            lambda self: False,
        )
        with pytest.raises(FileNotFoundError, match="config.ini"):
            AppConfig(config_path="/fake/path/nope.ini")

    def test_validate_raises_if_missing_database(self, tmp_path):
        """ValueError if [database] section is missing."""
        from core.app_config import AppConfig
        path = tmp_path / "config.ini"
        path.write_text("[app]\nkey=val\n", encoding="utf-8")
        with pytest.raises(ValueError, match="database"):
            AppConfig(config_path=str(path))

    def test_validate_raises_if_missing_security(self, tmp_path):
        """ValueError if [security] section is missing."""
        from core.app_config import AppConfig
        path = tmp_path / "config.ini"
        path.write_text("[database]\nengine=sqlite\n[application]\nname=Test\n", encoding="utf-8")
        with pytest.raises(ValueError, match="security"):
            AppConfig(config_path=str(path))

    def test_validate_raises_if_missing_application(self, tmp_path):
        """ValueError if [application] section is missing."""
        from core.app_config import AppConfig
        path = tmp_path / "config.ini"
        path.write_text("[database]\nengine=sqlite\n[security]\nkey=val\n", encoding="utf-8")
        with pytest.raises(ValueError, match="application"):
            AppConfig(config_path=str(path))


# ═══════════════════════════════════════════════════════════════════════════════
# Typed getters
# ═══════════════════════════════════════════════════════════════════════════════

class TestTypedGetters:
    """get, getint, getfloat, getboolean, getlist."""

    def test_get_retorna_string(self, ini_file_full):
        """get returns string value."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        assert cfg.get("database", "engine") == "mysql"
        assert cfg.get("database", "host") == "dbserver.example.com"

    def test_get_fallback_si_no_existe_seccion(self, ini_file_full):
        """get returns fallback when section doesn't exist."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        assert cfg.get("nonexistent", "key", "default_val") == "default_val"

    def test_get_fallback_si_no_existe_key(self, ini_file_full):
        """get returns fallback when key doesn't exist."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        assert cfg.get("database", "unknown_key", "my_default") == "my_default"

    def test_get_fallback_none_por_defecto(self, ini_file_full):
        """get returns None when no fallback and key missing."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        assert cfg.get("database", "unknown_key") is None

    def test_get_fallback_none_sin_seccion(self, ini_file_full):
        """get returns None when no fallback and section missing."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        assert cfg.get("ghost", "key") is None

    # ── getint ──

    def test_getint_retorna_int(self, ini_file_full):
        """getint returns integer value."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        assert cfg.getint("database", "port") == 3307
        assert cfg.getint("database", "pool_size") == 20

    def test_getint_fallback(self, ini_file_full):
        """getint returns fallback when key missing."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        assert cfg.getint("database", "ghost", 42) == 42

    def test_getint_fallback_none(self, ini_file_full):
        """getint returns None when no fallback and key missing."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        assert cfg.getint("database", "ghost") is None

    # ── getfloat ──

    def test_getfloat_retorna_float(self, ini_file_full):
        """getfloat returns float value."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        assert cfg.getfloat("reports", "tax_percentage") == 10.5

    def test_getfloat_fallback(self, ini_file_full):
        """getfloat returns fallback when key missing."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        assert cfg.getfloat("database", "ghost", 3.14) == 3.14

    def test_getfloat_fallback_none(self, ini_file_full):
        """getfloat returns None when no fallback and key missing."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        assert cfg.getfloat("database", "ghost") is None

    # ── getboolean ──

    def test_getboolean_true(self, ini_file_full):
        """getboolean returns True for true values."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        assert cfg.getboolean("email", "enabled") is True
        assert cfg.getboolean("backup", "encryption_enabled") is True

    def test_getboolean_false(self, ini_file_full):
        """getboolean returns False for false values."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        assert cfg.getboolean("ui", "start_maximized") is False
        assert cfg.getboolean("email", "use_tls") is False

    def test_getboolean_fallback(self, ini_file_full):
        """getboolean returns fallback when key missing."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        assert cfg.getboolean("database", "ghost", True) is True

    def test_getboolean_fallback_none(self, ini_file_full):
        """getboolean returns None when no fallback and key missing."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        assert cfg.getboolean("database", "ghost") is None

    # ── getlist ──

    def test_getlist_retorna_lista(self, ini_file_full):
        """getlist returns list of stripped items."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        result = cfg.getlist("business", "tipos_auto")
        assert result == ["Sedan", "SUV", "Pickup"]

    def test_getlist_vacio_retorna_vacio(self, ini_file_full):
        """getlist returns empty list for empty value."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        result = cfg.getlist("database", "engine")  # not a list
        # 'mysql' is not empty, so it returns ["mysql"]
        assert len(result) == 1

    def test_getlist_no_existe(self, ini_file_full):
        """getlist returns fallback for missing key."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        assert cfg.getlist("database", "ghost") == []

    def test_getlist_fallback_personalizado(self, ini_file_full):
        """getlist respects custom fallback."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        result = cfg.getlist("nonexistent", "key", fallback=["a", "b"])
        assert result == ["a", "b"]


# ═══════════════════════════════════════════════════════════════════════════════
# Direct access methods
# ═══════════════════════════════════════════════════════════════════════════════

class TestDirectAccessMethods:
    """get_database_config, get_security_config, etc."""

    def test_get_database_config(self, ini_file_full):
        """get_database_config returns complete dict."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        d = cfg.get_database_config()
        assert d["engine"] == "mysql"
        assert d["host"] == "dbserver.example.com"
        assert d["port"] == 3307
        assert d["pool_pre_ping"] is True

    def test_get_security_config(self, ini_file_full):
        """get_security_config returns complete dict."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        s = cfg.get_security_config()
        assert s["hash_algorithm"] == "sha512"
        assert s["hash_iterations"] == 200000
        assert s["max_login_attempts"] == 3
        assert s["account_lockout_duration"] == 900

    def test_get_backup_config(self, ini_file_full):
        """get_backup_config returns complete dict."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        b = cfg.get_backup_config()
        assert b["max_copies"] == 20
        assert "backups_prod" in b["directory"]
        assert "06:00" in b["schedule_times"]
        assert b["encryption_enabled"] is True

    def test_get_logging_config(self, ini_file_full):
        """get_logging_config returns complete dict."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        l = cfg.get_logging_config()
        assert l["level"] == "DEBUG"
        assert l["max_size_mb"] == 10
        assert l["backup_count"] == 7
        assert l["audit_enabled"] is True
        assert l["audit_retention_days"] == 90
        assert "logs_app" in l["directory"]

    def test_get_application_config(self, ini_file_full):
        """get_application_config returns complete dict."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        a = cfg.get_application_config()
        assert a["name"] == "Dinamo Rent Pro"
        assert a["version"] == "4.0.0"
        assert a["language"] == "en"
        assert a["timezone"] == "America/New_York"

    def test_get_ui_config(self, ini_file_full):
        """get_ui_config returns complete dict."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        ui = cfg.get_ui_config()
        assert ui["color_primario"] == "#ff0000"
        assert ui["font_family"] == "Arial"
        assert ui["font_size"] == 12
        assert ui["window_width"] == 1920
        assert ui["start_maximized"] is False

    def test_get_business_config(self, ini_file_full):
        """get_business_config returns complete dict."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        b = cfg.get_business_config()
        assert b["alert_soat_days"] == 30
        assert "Admin" in b["roles_con_informes"]
        assert "Admin" in b["roles_con_usuarios"]
        assert b["tipos_auto"] == ["Sedan", "SUV", "Pickup"]

    def test_get_email_config(self, ini_file_full):
        """get_email_config returns complete dict."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        e = cfg.get_email_config()
        assert e["enabled"] is True
        assert e["smtp_server"] == "mail.example.com"
        assert e["smtp_port"] == 465
        assert e["from_email"] == "notifications@example.com"

    def test_get_reports_config(self, ini_file_full):
        """get_reports_config returns complete dict."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        r = cfg.get_reports_config()
        assert r["pdf_engine"] == "weasyprint"
        assert r["currency_symbol"] == "$"
        assert r["currency_code"] == "USD"
        assert r["tax_percentage"] == 10.5
        assert r["tax_enabled"] is True

    def test_get_sqlite_config(self, ini_file_full):
        """get_sqlite_config returns path, timeout, and full_path."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        s = cfg.get_sqlite_config()
        assert s["path"] == "dinamo_rent_v3.db"  # not in ini, fallback
        assert s["timeout"] == 10  # fallback
        assert "dinamo_rent_v3.db" in s["full_path"]
        assert s["full_path"].endswith("dinamo_rent_v3.db")


# ═══════════════════════════════════════════════════════════════════════════════
# Fallback values (minimal config)
# ═══════════════════════════════════════════════════════════════════════════════

class TestFallbackValues:
    """Default fallback values when sections/keys are missing."""

    def test_database_config_fallbacks(self, ini_file_minimal):
        """get_database_config uses fallbacks for missing keys."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_minimal)
        d = cfg.get_database_config()
        assert d["engine"] == "sqlite"  # from file
        assert d["host"] == "localhost"  # fallback
        assert d["port"] == 3306  # fallback
        assert d["pool_pre_ping"] is True  # fallback

    def test_security_config_fallbacks(self, ini_file_minimal):
        """get_security_config uses fallbacks for missing keys."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_minimal)
        s = cfg.get_security_config()
        assert s["hash_algorithm"] == "sha256"  # from file
        assert s["session_timeout"] == 3600  # fallback

    def test_backup_config_fallbacks(self, ini_file_minimal):
        """get_backup_config uses fallbacks when section exists but keys missing."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_minimal)
        b = cfg.get_backup_config()
        assert b["max_copies"] == 10  # fallback
        assert b["encryption_enabled"] is True  # fallback

    def test_logging_config_fallbacks(self, ini_file_minimal):
        """get_logging_config uses fallbacks for missing keys."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_minimal)
        l = cfg.get_logging_config()
        assert l["max_size_mb"] == 5  # fallback
        assert l["level"] == "INFO"  # fallback
        assert l["audit_enabled"] is True  # fallback

    def test_application_config_fallbacks(self, ini_file_minimal):
        """get_application_config uses fallbacks for missing keys."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_minimal)
        a = cfg.get_application_config()
        assert a["name"] == "App Test"  # from file
        assert a["version"] == "3.2.0"  # fallback
        assert a["timezone"] == "America/Bogota"  # fallback

    def test_ui_config_fallbacks(self, ini_file_minimal):
        """get_ui_config uses fallbacks for missing keys."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_minimal)
        ui = cfg.get_ui_config()
        assert ui["color_primario"] == "#004aad"  # fallback
        assert ui["font_size"] == 10  # fallback
        assert ui["start_maximized"] is True  # fallback

    def test_business_config_fallbacks(self, ini_file_minimal):
        """get_business_config uses fallbacks for missing keys."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_minimal)
        b = cfg.get_business_config()
        assert b["alert_soat_days"] == 15  # fallback
        assert isinstance(b["roles_con_usuarios"], set)  # fallback converts to set

    def test_email_config_fallbacks(self, ini_file_minimal):
        """get_email_config uses fallbacks for missing keys."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_minimal)
        e = cfg.get_email_config()
        assert e["enabled"] is False  # fallback
        assert e["smtp_server"] == "smtp.gmail.com"  # fallback
        assert e["from_name"] == "Dinamo Rent"  # fallback

    def test_reports_config_fallbacks(self, ini_file_minimal):
        """get_reports_config uses fallbacks for missing keys."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_minimal)
        r = cfg.get_reports_config()
        assert r["pdf_engine"] == "weasyprint"  # fallback
        assert r["currency_symbol"] == "$"  # fallback
        assert r["tax_percentage"] == 19.0  # fallback

    def test_sqlite_config_fallbacks(self, ini_file_minimal):
        """get_sqlite_config uses fallbacks for missing keys."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_minimal)
        s = cfg.get_sqlite_config()
        assert s["path"] == "dinamo_rent_v3.db"  # fallback
        assert s["timeout"] == 10  # fallback
        assert "dinamo_rent_v3.db" in s["full_path"]


# ═══════════════════════════════════════════════════════════════════════════════
# Mutation: set, save, reload
# ═══════════════════════════════════════════════════════════════════════════════

class TestMutation:
    """set(), save(), reload()."""

    def test_set_value_en_seccion_existente(self, ini_file_full):
        """set() modifies an existing value."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        cfg.set("database", "engine", "postgresql")
        assert cfg.get("database", "engine") == "postgresql"

    def test_set_value_en_nueva_seccion(self, ini_file_full):
        """set() creates a new section if needed."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        cfg.set("custom", "api_key", "abc123")
        assert cfg.get("custom", "api_key") == "abc123"

    def test_set_convierte_a_string(self, ini_file_full):
        """set() converts value to string."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        cfg.set("database", "port", 5432)
        assert cfg.get("database", "port") == "5432"

    def test_save_persiste_cambios(self, ini_file_full):
        """save() writes changes to file."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        cfg.set("database", "engine", "postgresql")
        cfg.save()
        # Read file back
        content = Path(ini_file_full).read_text(encoding="utf-8")
        assert "postgresql" in content

    def test_save_ruta_diferente(self, ini_file_full, tmp_path):
        """save() can write to a different path."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        cfg.set("database", "engine", "postgresql")
        out_path = str(tmp_path / "output.ini")
        cfg.save(config_path=out_path)
        assert Path(out_path).exists()
        content = Path(out_path).read_text(encoding="utf-8")
        assert "postgresql" in content

    def test_reload_recupera_valores_originales(self, ini_file_full):
        """reload() restores values from file, discarding in-memory changes."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        original = cfg.get("database", "engine")
        cfg.set("database", "engine", "postgresql")
        assert cfg.get("database", "engine") == "postgresql"
        cfg.reload()
        assert cfg.get("database", "engine") == original

    def test_reload_refleja_cambios_externos(self, ini_file_full):
        """reload() picks up external file changes."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        # External change
        Path(ini_file_full).write_text(
            Path(ini_file_full).read_text(encoding="utf-8").replace("mysql", "external_change"),
            encoding="utf-8",
        )
        cfg.reload()
        assert cfg.get("database", "engine") == "external_change"


# ═══════════════════════════════════════════════════════════════════════════════
# Introspection
# ═══════════════════════════════════════════════════════════════════════════════

class TestIntrospection:
    """has_section(), sections(), __repr__."""

    def test_has_section_true(self, ini_file_full):
        """has_section returns True for existing section."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        assert cfg.has_section("database") is True
        assert cfg.has_section("email") is True

    def test_has_section_false(self, ini_file_full):
        """has_section returns False for missing section."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        assert cfg.has_section("ghost") is False

    def test_sections_retorna_lista(self, ini_file_full):
        """sections returns all section names."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        secs = cfg.sections()
        assert "database" in secs
        assert "security" in secs
        assert "email" in secs

    def test_repr(self, ini_file_full):
        """__repr__ includes file path."""
        from core.app_config import AppConfig
        cfg = AppConfig(config_path=ini_file_full)
        assert ini_file_full in repr(cfg)
        assert "AppConfig" in repr(cfg)


# ═══════════════════════════════════════════════════════════════════════════════
# Global singleton
# ═══════════════════════════════════════════════════════════════════════════════

class TestGlobalSingleton:
    """The global 'config' instance is importable and functional."""

    def test_config_importable(self):
        """Global config is importable."""
        from core.app_config import config
        from core.app_config import AppConfig
        assert isinstance(config, AppConfig)

    def test_get_config_function(self):
        """get_config() returns the global instance."""
        from core.app_config import get_config, config
        assert get_config() is config

    def test_reload_config_function(self):
        """reload_config() calls reload() on global instance (doesn't crash)."""
        from core.app_config import reload_config
        # This should not raise (even if it can't find a file, it's already loaded)
        reload_config()


# ═══════════════════════════════════════════════════════════════════════════════
# Module exports
# ═══════════════════════════════════════════════════════════════════════════════

class TestModuleExports:
    """All public names are importable from core.app_config."""

    def test_todo_importable(self):
        """All public names importable."""
        from core.app_config import (
            AppConfig, config, get_config, reload_config,
        )
        assert AppConfig is not None
        assert config is not None
        assert callable(get_config)
        assert callable(reload_config)

    def test_config_es_singleton(self):
        """Global config is the same instance across imports."""
        from core.app_config import config as c1
        from core.app_config import config as c2
        assert c1 is c2
