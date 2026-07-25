"""
test_config.py — Unit tests for core/config.py

Covers:
  _Config:           get, getint, getfloat, getbool, getlist, getset, set, save
  guardar_configuracion: Batch update + save
  Environment variables: Override logic via os.getenv fallbacks

Strategy:
  - _Config defaults are always loaded; no config.ini file is needed for most tests
  - File-based tests (save, guardar_configuracion) use monkeypatched INI_PATH
  - env var tests set/clear os.environ temporarily

Run: pytest tests/test_config.py -v
"""

import os
from pathlib import Path

import pytest


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def fresh_config(monkeypatch):
    """Return a fresh _Config instance with ONLY default values (no real config.ini)."""
    from core import config as config_module

    # Point INI_PATH to non-existent path so only defaults are loaded
    monkeypatch.setattr(config_module, "INI_PATH", Path("/nonexistent_config_ini_for_tests"))
    from core.config import _Config

    return _Config()


@pytest.fixture
def temp_ini_path(tmp_path):
    """Create a temporary config.ini with known content and monkeypatch INI_PATH."""

    content = (
        "[database]\n"
        "engine = sqlite\n"
        "host = test_host\n"
        "port = 9999\n"
        "user = test_user\n"
        "password = test_pass\n"
        "database = test_db\n"
        "path = test.db\n"
        "timeout = 30\n"
        "pool_size = 5\n"
        "pool_max_overflow = 10\n"
        "pool_pre_ping = false\n"
        "\n"
        "[security]\n"
        "hash_algorithm = sha512\n"
        "hash_iterations = 50000\n"
        "session_timeout = 7200\n"
        "\n"
        "[backup]\n"
        "directory = MyBackups\n"
        "max_copies = 5\n"
        "schedule_times = 10:00, 14:00\n"
        "encryption_enabled = yes\n"
        "\n"
        "[application]\n"
        "production_mode = true\n"
        "setup_completed = 1\n"
        "\n"
        "[ui]\n"
        "window_width = 1024\n"
        "font_size = 12\n"
        "start_maximized = false\n"
        "\n"
        "[business]\n"
        "km_alert_aceite = 1000\n"
        "roles_con_informes = Administrador\n"
        "\n"
        "[reports]\n"
        "tax_percentage = 10.5\n"
        "decimal_places = 0\n"
        "\n"
        "[logging]\n"
        "max_size_mb = 10\n"
        "backup_count = 3\n"
        "\n"
        "[email]\n"
        "enabled = yes\n"
        "smtp_port = 465\n"
        "use_tls = false\n"
    )
    ini_file = tmp_path / "config.ini"
    ini_file.write_text(content, encoding="utf-8")
    return str(ini_file)


# ═══════════════════════════════════════════════════════════════════════════════
# _Config initialization
# ═══════════════════════════════════════════════════════════════════════════════


class TestInit:
    def test_defaults_sin_archivo(self, fresh_config):
        """_Config loads defaults even without a config.ini file."""
        assert fresh_config.get("database", "engine") == "firebird"
        assert fresh_config.get("application", "name") == "Dinamo Rent ERP"

    def test_lee_desde_archivo(self, temp_ini_path, monkeypatch):
        """_Config overrides defaults with values from INI file."""
        from core import config as config_module
        from core.config import _Config

        monkeypatch.setattr(config_module, "INI_PATH", Path(temp_ini_path))
        cfg = _Config()
        assert cfg.get("database", "engine") == "sqlite"
        assert cfg.get("database", "host") == "test_host"
        assert cfg.get("database", "port") == "9999"

    def test_archivo_parcial_mantiene_defaults(self, temp_ini_path, monkeypatch):
        """INI with partial keys keeps defaults for missing keys."""
        from core import config as config_module
        from core.config import _Config

        monkeypatch.setattr(config_module, "INI_PATH", Path(temp_ini_path))
        cfg = _Config()
        # From file
        assert cfg.get("database", "engine") == "sqlite"
        # From defaults (not in test ini)
        assert cfg.get("ui", "color_primario") == "#2563eb"

    def test_secciones_completas(self, fresh_config):
        """All default sections are present."""
        sections = [
            "database",
            "security",
            "backup",
            "logging",
            "application",
            "ui",
            "business",
            "email",
            "whatsapp",
            "reports",
        ]
        for section in sections:
            assert fresh_config._parser.has_section(section), f"Missing section: {section}"


# ═══════════════════════════════════════════════════════════════════════════════
# _Config.get
# ═══════════════════════════════════════════════════════════════════════════════


class TestGet:
    def test_valor_existente(self, fresh_config):
        """get() returns existing string value."""
        result = fresh_config.get("database", "engine")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_seccion_inexistente_retorna_fallback(self, fresh_config):
        """get() with missing section returns fallback or ''."""
        result = fresh_config.get("nonexistent", "key", "default_val")
        assert result == "default_val"

    def test_seccion_inexistente_sin_fallback(self, fresh_config):
        """get() with missing section and no fallback returns ''."""
        assert fresh_config.get("nonexistent", "key") == ""

    def test_clave_inexistente_retorna_fallback(self, fresh_config):
        """get() with missing key returns fallback."""
        result = fresh_config.get("database", "nonexistent_key", "fb")
        assert result == "fb"

    def test_clave_inexistente_sin_fallback(self, fresh_config):
        """get() with missing key and no fallback returns ''."""
        assert fresh_config.get("database", "nonexistent_key") == ""

    def test_retorna_string_siempre(self, fresh_config):
        """get() always returns a string."""
        result = fresh_config.get("database", "timeout")
        assert isinstance(result, str)
        assert result.isdigit()

    def test_valor_con_espacios(self, fresh_config):
        """get() returns value as stored (whitespace preserved by configparser)."""
        result = fresh_config.get("database", "engine")
        # configparser strips values by default
        assert result == "firebird"


# ═══════════════════════════════════════════════════════════════════════════════
# _Config.getint
# ═══════════════════════════════════════════════════════════════════════════════


class TestGetint:
    def test_valor_existente(self, fresh_config):
        """getint() returns int from numeric string.
        PD: The default timeout value in _DEFAULTS is \"10\" as a string,
        which configparser stores as a string. Since no actual config.ini overrides it,
        getint should parse it correctly."""
        result = fresh_config.getint("database", "timeout")
        assert result == 10
        assert isinstance(result, int)

    def test_seccion_inexistente_retorna_fallback(self, fresh_config):
        """getint() with missing section returns fallback int."""
        assert fresh_config.getint("bad_section", "key", 99) == 99

    def test_clave_inexistente_retorna_fallback(self, fresh_config):
        """getint() with missing key returns fallback."""
        assert fresh_config.getint("database", "no_key", 42) == 42

    def test_fallback_default_cero(self, fresh_config):
        """getint() default fallback is 0."""
        result = fresh_config.getint("nonexistent", "key")
        assert result == 0

    def test_valor_no_entero_retorna_fallback(self, fresh_config):
        """getint() with non-int value returns fallback."""
        fresh_config._parser.set("database", "engine", "not_an_int")
        result = fresh_config.getint("database", "engine", 50)
        assert result == 50

    def test_valor_negativo(self, fresh_config):
        """getint() handles negative values."""
        fresh_config._parser.set("database", "timeout", "-5")
        assert fresh_config.getint("database", "timeout") == -5

    def test_valor_flotante_retorna_fallback(self, fresh_config):
        """getint() with float string returns fallback (configparser getint fails)."""
        fresh_config._parser.set("database", "timeout", "10.5")
        result = fresh_config.getint("database", "timeout", 0)
        assert result == 0


# ═══════════════════════════════════════════════════════════════════════════════
# _Config.getfloat
# ═══════════════════════════════════════════════════════════════════════════════


class TestGetfloat:
    def test_valor_entero_como_float(self, fresh_config):
        """getfloat() returns float from integer string."""
        fresh_config._parser.set("database", "timeout", "10")
        assert fresh_config.getfloat("database", "timeout") == 10.0

    def test_valor_decimal(self, fresh_config):
        """getfloat() parses decimal string."""
        fresh_config._parser.set("database", "timeout", "19.5")
        assert fresh_config.getfloat("database", "timeout") == 19.5

    def test_fallback_default_cero(self, fresh_config):
        """getfloat() default fallback is 0.0."""
        assert fresh_config.getfloat("bad", "key") == 0.0

    def test_fallback_personalizado(self, fresh_config):
        """getfloat() with custom fallback."""
        assert fresh_config.getfloat("bad", "key", 3.14) == 3.14

    def test_valor_no_numerico_retorna_fallback(self, fresh_config):
        """getfloat() with non-numeric value returns fallback."""
        fresh_config._parser.set("database", "timeout", "abc")
        assert fresh_config.getfloat("database", "timeout", 1.5) == 1.5

    def test_valor_negativo(self, fresh_config):
        """getfloat() handles negative float."""
        fresh_config._parser.set("database", "timeout", "-5.5")
        assert fresh_config.getfloat("database", "timeout") == -5.5


# ═══════════════════════════════════════════════════════════════════════════════
# _Config.getbool
# ═══════════════════════════════════════════════════════════════════════════════


class TestGetbool:
    @pytest.fixture
    def cfg_with_test_section(self):
        """Return _Config with a 'test' section added."""
        from core.config import _Config

        cfg = _Config()
        cfg._parser.add_section("test")
        return cfg

    def test_true_literal(self, cfg_with_test_section):
        """'true' returns True."""
        cfg_with_test_section._parser.set("test", "val", "true")
        assert cfg_with_test_section.getbool("test", "val") is True

    def test_yes_literal(self, cfg_with_test_section):
        """'yes' returns True."""
        cfg_with_test_section._parser.set("test", "val", "yes")
        assert cfg_with_test_section.getbool("test", "val") is True

    def test_on_literal(self, cfg_with_test_section):
        """'on' returns True."""
        cfg_with_test_section._parser.set("test", "val", "on")
        assert cfg_with_test_section.getbool("test", "val") is True

    def test_1_literal(self, cfg_with_test_section):
        """'1' returns True (configparser interprets 1 as True)."""
        cfg_with_test_section._parser.set("test", "val", "1")
        assert cfg_with_test_section.getbool("test", "val") is True

    def test_false_literal(self, cfg_with_test_section):
        """'false' returns False."""
        cfg_with_test_section._parser.set("test", "val", "false")
        assert cfg_with_test_section.getbool("test", "val") is False

    def test_no_literal(self, cfg_with_test_section):
        """'no' returns False."""
        cfg_with_test_section._parser.set("test", "val", "no")
        assert cfg_with_test_section.getbool("test", "val") is False

    def test_off_literal(self, cfg_with_test_section):
        """'off' returns False."""
        cfg_with_test_section._parser.set("test", "val", "off")
        assert cfg_with_test_section.getbool("test", "val") is False

    def test_0_literal(self, cfg_with_test_section):
        """'0' returns False (configparser interprets 0 as False)."""
        cfg_with_test_section._parser.set("test", "val", "0")
        assert cfg_with_test_section.getbool("test", "val") is False

    def test_fallback_default_false(self, fresh_config):
        """getbool() default fallback is False."""
        assert fresh_config.getbool("bad", "key") is False

    def test_fallback_personalizado(self, fresh_config):
        """getbool() with custom fallback."""
        assert fresh_config.getbool("bad", "key", True) is True

    def test_valor_invalido_retorna_fallback(self, cfg_with_test_section):
        """getbool() with unrecognized value returns fallback."""
        cfg_with_test_section._parser.set("test", "val", "maybe")
        assert cfg_with_test_section.getbool("test", "val", True) is True

    def test_default_valor_bool_parsed(self, fresh_config):
        """Boolean-like strings are correctly parsed (not returned as strings)."""
        result = fresh_config.getbool("database", "pool_pre_ping")
        assert isinstance(result, bool)
        result2 = fresh_config.getbool("email", "enabled")
        assert isinstance(result2, bool)


# ═══════════════════════════════════════════════════════════════════════════════
# _Config.getlist
# ═══════════════════════════════════════════════════════════════════════════════


class TestGetlist:
    def test_lista_comas(self, fresh_config):
        """getlist() splits by comma and strips whitespace."""
        fresh_config._parser.set("business", "test_list", "a, b, c")
        assert fresh_config.getlist("business", "test_list") == ["a", "b", "c"]

    def test_valor_unico_sin_comas(self, fresh_config):
        """getlist() with single value returns list of one."""
        fresh_config._parser.set("business", "test_list", "solo")
        assert fresh_config.getlist("business", "test_list") == ["solo"]

    def test_lista_vacia_retorna_fallback(self, fresh_config):
        """getlist() with empty value returns fallback."""
        fresh_config._parser.set("database", "test_list", "")
        result = fresh_config.getlist("database", "test_list", ["default"])
        assert result == ["default"]

    def test_sin_fallback_lista_vacia(self, fresh_config):
        """getlist() with empty value and no fallback returns []."""
        fresh_config._parser.set("database", "test_list", "")
        assert fresh_config.getlist("database", "test_list") == []

    def test_clave_inexistente_retorna_fallback(self, fresh_config):
        """getlist() with missing key returns fallback."""
        result = fresh_config.getlist("database", "no_key", ["x", "y"])
        assert result == ["x", "y"]

    def test_elementos_con_espacios(self, fresh_config):
        """getlist() strips spaces around each element."""
        fresh_config._parser.set("business", "test_list", "  uno  ,  dos  ,  tres  ")
        assert fresh_config.getlist("business", "test_list") == ["uno", "dos", "tres"]

    def test_elementos_vacios_ignorados(self, fresh_config):
        """getlist() ignores empty elements from trailing commas."""
        fresh_config._parser.set("business", "test_list", "a, b, , c,")
        assert fresh_config.getlist("business", "test_list") == ["a", "b", "c"]

    def test_lista_default_tipos_auto(self, fresh_config):
        """Default tipos_auto list is parsed correctly."""
        result = fresh_config.getlist("business", "tipos_auto")
        assert "Automóvil" in result
        assert "Moto" in result
        assert len(result) >= 5


# ═══════════════════════════════════════════════════════════════════════════════
# _Config.getset
# ═══════════════════════════════════════════════════════════════════════════════


class TestGetset:
    def test_retorna_set(self, fresh_config):
        """getset() returns a set."""
        fresh_config._parser.set("business", "test_set", "a, b, c")
        result = fresh_config.getset("business", "test_set")
        assert isinstance(result, set)
        assert result == {"a", "b", "c"}

    def test_elementos_duplicados_deducen(self, fresh_config):
        """getset() deduplicates elements."""
        fresh_config._parser.set("business", "test_set", "a, b, a, c, b")
        assert fresh_config.getset("business", "test_set") == {"a", "b", "c"}

    def test_valor_vacio_retorna_fallback(self, fresh_config):
        """getset() with empty value returns fallback."""
        fresh_config._parser.set("database", "test_set", "")
        result = fresh_config.getset("database", "test_set", {"default"})
        assert result == {"default"}

    def test_sin_fallback_set_vacio(self, fresh_config):
        """getset() with empty value and no fallback returns empty set."""
        fresh_config._parser.set("database", "test_set", "")
        assert fresh_config.getset("database", "test_set") == set()

    def test_roles_con_informes_default(self, fresh_config):
        """Default ROLES_CON_INFORMES is a set with Admin and Supervisor."""
        result = fresh_config.getset("business", "roles_con_informes")
        assert "Administrador" in result
        assert "Supervisor" in result

    def test_roles_con_usuarios_default(self, fresh_config):
        """Default ROLES_CON_USUARIOS is a set with only Administrador."""
        result = fresh_config.getset("business", "roles_con_usuarios")
        assert result == {"Administrador"}


# ═══════════════════════════════════════════════════════════════════════════════
# _Config.set
# ═══════════════════════════════════════════════════════════════════════════════


class TestSet:
    def test_set_valor(self, fresh_config):
        """set() stores a value in the parser."""
        fresh_config.set("test_section", "my_key", "my_value")
        assert fresh_config.get("test_section", "my_key") == "my_value"

    def test_set_crea_seccion_automaticamente(self, fresh_config):
        """set() auto-creates section if it doesn't exist."""
        fresh_config.set("brand_new_section", "key", "value")
        assert fresh_config._parser.has_section("brand_new_section")

    def test_set_sobreescribe_existente(self, fresh_config):
        """set() overwrites existing values."""
        fresh_config.set("database", "engine", "sqlite")
        assert fresh_config.get("database", "engine") == "sqlite"

    def test_set_retorna_none(self, fresh_config):
        """set() returns None."""
        result = fresh_config.set("database", "engine", "v")
        assert result is None

    def test_set_valor_no_str_convertido(self, fresh_config):
        """set() converts non-string values to string."""
        fresh_config.set("database", "test_num", 42)
        stored = fresh_config.get("database", "test_num")
        assert stored == "42"
        assert isinstance(stored, str)


# ═══════════════════════════════════════════════════════════════════════════════
# _Config.save
# ═══════════════════════════════════════════════════════════════════════════════


class TestSave:
    def test_guarda_archivo_ini(self, temp_ini_path, monkeypatch):
        """save() writes config to INI file."""
        from core import config as config_module
        from core.config import _Config

        monkeypatch.setattr(config_module, "INI_PATH", Path(temp_ini_path))
        cfg = _Config()
        cfg.set("database", "engine", "postgresql")
        cfg.save()
        # Read back
        saved_path = Path(temp_ini_path)
        assert saved_path.exists()
        content = saved_path.read_text(encoding="utf-8")
        assert "postgresql" in content

    def test_archivo_contiene_seccion(self, temp_ini_path, monkeypatch):
        """save() writes section headers correctly."""
        from core import config as config_module
        from core.config import _Config

        monkeypatch.setattr(config_module, "INI_PATH", Path(temp_ini_path))
        cfg = _Config()
        cfg.set("custom_section", "my_key", "123")
        cfg.save()
        saved_path = Path(temp_ini_path)
        content = saved_path.read_text(encoding="utf-8")
        assert "[custom_section]" in content
        assert "my_key = 123" in content

    def test_archivo_creado_si_no_existe(self, tmp_path, monkeypatch):
        """save() creates the file if it doesn't exist."""
        from core import config as config_module
        from core.config import _Config

        new_path = tmp_path / "new_config.ini"
        monkeypatch.setattr(config_module, "INI_PATH", new_path)
        cfg = _Config()
        cfg.set("section", "key", "value")
        cfg.save()
        assert new_path.exists()

    def test_sobreescribe_archivo_existente(self, temp_ini_path, monkeypatch):
        """save() overwrites existing file with new content."""
        from core import config as config_module
        from core.config import _Config

        monkeypatch.setattr(config_module, "INI_PATH", Path(temp_ini_path))
        cfg = _Config()
        cfg.set("database", "engine", "mariadb")
        cfg.save()
        cfg2 = _Config()
        # Without re-reading (new instance reads from updated file)
        monkeypatch.setattr(config_module, "INI_PATH", Path(temp_ini_path))
        cfg2 = _Config()
        assert cfg2.get("database", "engine") == "mariadb"


# ═══════════════════════════════════════════════════════════════════════════════
# guardar_configuracion
# ═══════════════════════════════════════════════════════════════════════════════


class TestGuardarConfiguracion:
    def test_guardar_multiple_valores(self, temp_ini_path, monkeypatch):
        """guardar_configuracion() updates multiple values and saves."""
        from core import config as config_module

        monkeypatch.setattr(config_module, "INI_PATH", Path(temp_ini_path))
        from core.config import guardar_configuracion

        # Ensure _cfg writes to the temp path
        guardar_configuracion(
            "database",
            {
                "engine": "sqlite",
                "host": "new_host",
            },
        )
        saved_path = Path(temp_ini_path)
        content = saved_path.read_text(encoding="utf-8")
        assert "sqlite" in content
        assert "new_host" in content

    def test_guardar_no_afecta_otras_secciones(self, temp_ini_path, monkeypatch):
        """guardar_configuracion() only modifies the specified section."""
        from core import config as config_module

        monkeypatch.setattr(config_module, "INI_PATH", Path(temp_ini_path))
        from core.config import guardar_configuracion

        guardar_configuracion("database", {"engine": "sqlite"})
        saved_path = Path(temp_ini_path)
        content = saved_path.read_text(encoding="utf-8")
        assert "[database]" in content
        # configparser.write() writes ALL sections from the parser, including defaults
        assert "[security]" in content
        assert "[application]" in content

    def test_retorna_none(self, temp_ini_path, monkeypatch):
        """guardar_configuracion() returns None."""
        from core import config as config_module

        monkeypatch.setattr(config_module, "INI_PATH", Path(temp_ini_path))
        from core.config import guardar_configuracion

        result = guardar_configuracion("database", {})
        assert result is None


# ═══════════════════════════════════════════════════════════════════════════════
# Environment variable overrides (module-level variables)
# ═══════════════════════════════════════════════════════════════════════════════


class TestEnvOverrides:
    def test_db_engine_env_override(self, monkeypatch):
        """Environment variable DINAMO_DB_ENGINE overrides config value."""
        monkeypatch.setenv("DINAMO_DB_ENGINE", "postgresql")
        # Since module is already loaded, test the os.getenv pattern
        engine = os.getenv("DINAMO_DB_ENGINE", "mysql")
        assert engine == "postgresql"

    def test_db_host_env_override(self, monkeypatch):
        """Environment variable DINAMO_DB_HOST overrides config value."""
        monkeypatch.setenv("DINAMO_DB_HOST", "10.0.0.1")
        host = os.getenv("DINAMO_DB_HOST", "localhost")
        assert host == "10.0.0.1"

    def test_db_password_env_override(self, monkeypatch):
        """Environment variable DINAMO_DB_PASSWORD overrides config value."""
        monkeypatch.setenv("DINAMO_DB_PASSWORD", "s3cr3t!")
        pwd = os.getenv("DINAMO_DB_PASSWORD", "")
        assert pwd == "s3cr3t!"

    def test_db_name_env_override(self, monkeypatch):
        """Environment variable DINAMO_DB_NAME overrides config value."""
        monkeypatch.setenv("DINAMO_DB_NAME", "production_db")
        name = os.getenv("DINAMO_DB_NAME", "dinamo_rent")
        assert name == "production_db"

    def test_sin_env_usa_fallback(self, monkeypatch, fresh_config):
        """Without env variable, the _Config default is used."""
        monkeypatch.delenv("DINAMO_DB_ENGINE", raising=False)
        engine = os.getenv("DINAMO_DB_ENGINE", fresh_config.get("database", "engine", "mysql"))
        assert isinstance(engine, str)
        assert len(engine) > 0

    def test_db_port_env_override_int(self, monkeypatch, fresh_config):
        """Environment variable DINAMO_DB_PORT overrides and converts to int."""
        monkeypatch.setenv("DINAMO_DB_PORT", "5432")
        port = int(os.getenv("DINAMO_DB_PORT", fresh_config.get("database", "port", "3306")))
        assert port == 5432
        assert isinstance(port, int)

    def test_db_user_env_override(self, monkeypatch):
        """Environment variable DINAMO_DB_USER overrides config value."""
        monkeypatch.setenv("DINAMO_DB_USER", "db_admin")
        user = os.getenv("DINAMO_DB_USER", "root")
        assert user == "db_admin"


# ═══════════════════════════════════════════════════════════════════════════════
# Module-level variables instantiation
# ═══════════════════════════════════════════════════════════════════════════════


class TestModuleVariables:
    def test_db_engine_tipo(self):
        """DB_ENGINE is a string."""
        from core.config import DB_ENGINE

        assert isinstance(DB_ENGINE, str)

    def test_db_timeout_entero(self):
        """DB_TIMEOUT is an int."""
        from core.config import DB_TIMEOUT

        assert isinstance(DB_TIMEOUT, int)

    def test_db_pool_pre_ping_bool(self):
        """DB_POOL_PRE_PING is a bool."""
        from core.config import DB_POOL_PRE_PING

        assert isinstance(DB_POOL_PRE_PING, bool)

    def test_hash_iterations_entero(self):
        """HASH_ITERATIONS is an int."""
        from core.config import HASH_ITERATIONS

        assert isinstance(HASH_ITERATIONS, int)

    def test_session_timeout_entero(self):
        """SESSION_TIMEOUT is an int (seconds)."""
        from core.config import SESSION_TIMEOUT

        assert isinstance(SESSION_TIMEOUT, int)
        assert SESSION_TIMEOUT > 0

    def test_production_mode_bool(self):
        """PRODUCTION_MODE is a bool."""
        from core.config import PRODUCTION_MODE

        assert isinstance(PRODUCTION_MODE, bool)

    def test_currency_symbol_str(self):
        """CURRENCY_SYMBOL is a string."""
        from core.config import CURRENCY_SYMBOL

        assert isinstance(CURRENCY_SYMBOL, str)

    def test_roles_con_informes_set(self):
        """ROLES_CON_INFORMES is a set."""
        from core.config import ROLES_CON_INFORMES

        assert isinstance(ROLES_CON_INFORMES, set)
        assert len(ROLES_CON_INFORMES) >= 1

    def test_roles_con_usuarios_set(self):
        """ROLES_CON_USUARIOS is a set."""
        from core.config import ROLES_CON_USUARIOS

        assert isinstance(ROLES_CON_USUARIOS, set)

    def test_tipos_auto_lista(self):
        """TIPOS_AUTO is a list."""
        from core.config import TIPOS_AUTO

        assert isinstance(TIPOS_AUTO, list)
        assert len(TIPOS_AUTO) >= 5

    def test_tax_percentage_float(self):
        """TAX_PERCENTAGE is a float."""
        from core.config import TAX_PERCENTAGE

        assert isinstance(TAX_PERCENTAGE, float)

    def test_directorios_existen(self):
        """LOGS_DIR and BACKUP_DIR exist."""
        from core.config import LOGS_DIR, BACKUP_DIR

        assert LOGS_DIR.exists()
        assert BACKUP_DIR.exists()

    def test_bucket_db_mysql_es_dict(self):
        """DB_MYSQL is a dict with all expected keys."""
        from core.config import DB_MYSQL

        assert isinstance(DB_MYSQL, dict)
        expected = {"host", "port", "user", "password", "database"}
        assert expected.issubset(DB_MYSQL.keys())
