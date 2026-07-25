"""
test_logger.py — Unit tests for core/logger.py

Covers:
  _setup_root_logger (singleton, handlers, levels)
  get_logger (naming, propagation, setup trigger)
  get_audit_logger (audit logger, TimedRotatingFileHandler, no propagation)
  Log file output (messages appear in files)
  Log level filtering (DEBUG vs WARNING+)
  Rotation handler configuration (maxBytes, backupCount)

Strategy:
  - Each test class monkeypatches LOGS_DIR to an isolated tmp_path
  - Each test class resets _configured = False before its tests
  - A finalizer cleans up handlers from the root logger after each class
  - Tests avoid using real log files or depending on prior logger state

Run: pytest tests/test_logger.py -v
"""

import logging
import logging.handlers

import pytest


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════


def _cleanup_root_handlers():
    """Remove all handlers from the Dinamo Rent root logger and reset flag."""
    import core.logger as log_mod

    log_mod._configured = False
    root = logging.getLogger(log_mod.APP_NAME)
    for h in list(root.handlers):
        root.removeHandler(h)
        h.close()
    # Also clean up audit logger if it exists
    audit = logging.getLogger(f"{log_mod.APP_NAME}.audit")
    for h in list(audit.handlers):
        audit.removeHandler(h)
        h.close()


def _count_root_handlers():
    """Return the number of handlers on the app root logger."""
    import core.logger as log_mod

    root = logging.getLogger(log_mod.APP_NAME)
    return len(root.handlers)


@pytest.fixture(autouse=True)
def _global_logger_cleanup():
    """Ensure logger state is reset between test classes."""
    yield
    _cleanup_root_handlers()


# ═══════════════════════════════════════════════════════════════════════════════
# _setup_root_logger
# ═══════════════════════════════════════════════════════════════════════════════


class TestSetupRootLogger:
    """_setup_root_logger singleton and handler configuration."""

    @pytest.fixture(autouse=True)
    def _setup(self, monkeypatch, tmp_path):
        """Isolate logs to a temp directory before each test."""
        import core.logger as log_mod

        monkeypatch.setattr(log_mod, "LOGS_DIR", tmp_path)
        monkeypatch.setattr(log_mod, "_configured", False)
        _cleanup_root_handlers()

    def test_configura_una_sola_vez(self):
        """Calling _setup_root_logger twice adds handlers only once."""
        from core.logger import _setup_root_logger

        _setup_root_logger()
        first_handlers = _count_root_handlers()
        _setup_root_logger()
        assert _count_root_handlers() == first_handlers, "Second call should not add more handlers"

    def test_crea_tres_handlers(self):
        """_setup_root_logger creates dinamo_rent.log, errores.log, and StreamHandler."""
        from core.logger import _setup_root_logger

        _setup_root_logger()
        root = logging.getLogger("Dinamo Rent ERP")
        handler_types = [type(h).__name__ for h in root.handlers]
        # SafeRotatingFileHandler is a custom subclass that wraps RotatingFileHandler
        # with PermissionError handling for Windows multi-process log rotation
        assert any("RotatingFileHandler" in t for t in handler_types), (
            f"No RotatingFileHandler subclass found in {handler_types}"
        )
        assert "StreamHandler" in handler_types
        assert len(root.handlers) == 3

    def test_handler_levels(self):
        """File handler DEBUG, error handler WARNING, StreamHandler INFO."""
        from core.logger import _setup_root_logger

        _setup_root_logger()
        root = logging.getLogger("Dinamo Rent ERP")
        levels = {}
        for h in root.handlers:
            if isinstance(h, logging.handlers.RotatingFileHandler):
                if h.level == logging.WARNING:
                    levels["error_handler"] = h.level
                elif h.level == logging.DEBUG:
                    levels["file_handler"] = h.level
            elif isinstance(h, logging.StreamHandler):
                levels["stream_handler"] = h.level
        assert levels.get("file_handler") == logging.DEBUG
        assert levels.get("error_handler") == logging.WARNING
        assert levels.get("stream_handler") == logging.INFO

    def test_root_logger_level_debug(self):
        """Root logger is set to DEBUG."""
        from core.logger import _setup_root_logger, APP_NAME

        _setup_root_logger()
        root = logging.getLogger(APP_NAME)
        assert root.level == logging.DEBUG

    def test_file_handler_formato_detalle(self):
        """File handler has detailed format with timestamp."""
        from core.logger import _setup_root_logger

        _setup_root_logger()
        root = logging.getLogger("Dinamo Rent ERP")
        file_handlers = [
            h
            for h in root.handlers
            if isinstance(h, logging.handlers.RotatingFileHandler) and h.level == logging.DEBUG
        ]
        assert len(file_handlers) == 1
        fmt = file_handlers[0].formatter
        assert "%(asctime)s" in fmt._fmt
        assert "%(levelname)" in fmt._fmt
        assert "%(message)s" in fmt._fmt


# ═══════════════════════════════════════════════════════════════════════════════
# get_logger
# ═══════════════════════════════════════════════════════════════════════════════


class TestGetLogger:
    """get_logger returns properly configured loggers."""

    @pytest.fixture(autouse=True)
    def _setup(self, monkeypatch, tmp_path):
        """Isolate logs and reset state before each test."""
        import core.logger as log_mod

        monkeypatch.setattr(log_mod, "LOGS_DIR", tmp_path)
        monkeypatch.setattr(log_mod, "_configured", False)
        _cleanup_root_handlers()

    def test_retorna_logger_con_nombre(self):
        """get_logger('test') returns a logger with name 'Dinamo Rent ERP.test'."""
        from core.logger import get_logger, APP_NAME

        log = get_logger("test_nombre")
        assert log.name == f"{APP_NAME}.test_nombre"

    def test_triggers_setup_root(self):
        """Calling get_logger triggers _setup_root_logger (handlers created)."""
        from core.logger import get_logger

        assert _count_root_handlers() == 0
        get_logger("trigger_test")
        assert _count_root_handlers() > 0

    def test_logger_propaga_al_root(self):
        """Child logger propagates messages to root handlers."""
        from core.logger import get_logger

        log = get_logger("propagate")
        assert log.propagate is True

    def test_get_logger_es_callable(self):
        """get_logger is a function that returns a Logger instance."""
        from core.logger import get_logger

        log = get_logger("callable_test")
        assert isinstance(log, logging.Logger)

    def test_logger_hereda_nivel_del_root(self):
        """Logger level is NOTSET (inherits from root)."""
        from core.logger import get_logger

        log = get_logger("level_test")
        assert log.level == logging.NOTSET


# ═══════════════════════════════════════════════════════════════════════════════
# get_audit_logger
# ═══════════════════════════════════════════════════════════════════════════════


class TestGetAuditLogger:
    """get_audit_logger returns specialized audit logger."""

    @pytest.fixture(autouse=True)
    def _setup(self, monkeypatch, tmp_path):
        """Isolate logs and reset state before each test."""
        import core.logger as log_mod

        monkeypatch.setattr(log_mod, "LOGS_DIR", tmp_path)
        monkeypatch.setattr(log_mod, "_configured", False)
        _cleanup_root_handlers()
        # Also clean audit logger
        audit = logging.getLogger(f"{log_mod.APP_NAME}.audit")
        for h in list(audit.handlers):
            audit.removeHandler(h)
            h.close()

    def test_retorna_logger_audit(self):
        """get_audit_logger() returns a logger named 'Dinamo Rent ERP.audit'."""
        from core.logger import get_audit_logger, APP_NAME

        audit = get_audit_logger()
        assert audit.name == f"{APP_NAME}.audit"

    def test_tiene_timed_rotating_handler(self):
        """Audit logger uses TimedRotatingFileHandler."""
        from core.logger import get_audit_logger

        audit = get_audit_logger()
        handler_types = [type(h).__name__ for h in audit.handlers]
        assert "TimedRotatingFileHandler" in handler_types

    def test_handler_level_info(self):
        """Audit handler is set to INFO level."""
        from core.logger import get_audit_logger

        audit = get_audit_logger()
        assert len(audit.handlers) == 1
        assert audit.handlers[0].level == logging.INFO

    def test_no_propaga(self):
        """Audit logger has propagate=False to avoid duplicate log entries."""
        from core.logger import get_audit_logger

        audit = get_audit_logger()
        assert audit.propagate is False

    def test_handler_timed_config(self):
        """TimedRotatingFileHandler configured at midnight with 30 backups."""
        from core.logger import get_audit_logger

        audit = get_audit_logger()
        handler = audit.handlers[0]
        assert isinstance(handler, logging.handlers.TimedRotatingFileHandler)
        assert handler.when.lower() == "midnight"
        assert handler.backupCount == 30

    def test_formato_tiene_asctime_y_audit(self):
        """Audit format includes timestamp and AUDIT marker."""
        from core.logger import get_audit_logger

        audit = get_audit_logger()
        handler = audit.handlers[0]
        assert "%(asctime)s" in handler.formatter._fmt
        assert "AUDIT" in handler.formatter._fmt

    def test_es_singleton_no_duplica_handlers(self):
        """Calling get_audit_logger multiple times doesn't duplicate handlers."""
        from core.logger import get_audit_logger

        a1 = get_audit_logger()
        count = len(a1.handlers)
        a2 = get_audit_logger()
        assert len(a2.handlers) == count


# ═══════════════════════════════════════════════════════════════════════════════
# Log file output
# ═══════════════════════════════════════════════════════════════════════════════


class TestLogFileOutput:
    """Messages are actually written to the correct log files."""

    @pytest.fixture(autouse=True)
    def _setup(self, monkeypatch, tmp_path):
        """Isolate logs to a temp directory and setup fresh loggers."""
        import core.logger as log_mod

        monkeypatch.setattr(log_mod, "LOGS_DIR", tmp_path)
        monkeypatch.setattr(log_mod, "_configured", False)
        _cleanup_root_handlers()
        self.logs_dir = tmp_path

    def test_info_se_escribe_en_dinamo_log(self):
        """INFO message appears in dinamo_rent.log."""
        from core.logger import get_logger

        log = get_logger("test_file_output")
        log.info("Mensaje de prueba INFO")
        log_file = self.logs_dir / "dinamo_rent.log"
        assert log_file.exists()
        content = log_file.read_text(encoding="utf-8")
        assert "Mensaje de prueba INFO" in content

    def test_error_se_escribe_en_ambos_archivos(self):
        """ERROR message appears in both dinamo_rent.log and errores.log."""
        from core.logger import get_logger

        log = get_logger("test_dual_output")
        log.error("Mensaje de prueba ERROR")
        dinamo_file = self.logs_dir / "dinamo_rent.log"
        error_file = self.logs_dir / "errores.log"
        assert dinamo_file.exists()
        assert error_file.exists()
        dinamo_content = dinamo_file.read_text(encoding="utf-8")
        error_content = error_file.read_text(encoding="utf-8")
        assert "Mensaje de prueba ERROR" in dinamo_content
        assert "Mensaje de prueba ERROR" in error_content

    def test_debug_no_aparece_en_errores(self):
        """DEBUG message appears in dinamo_rent.log but NOT in errores.log."""
        from core.logger import get_logger

        log = get_logger("test_level_filter")
        log.debug("Mensaje solo DEBUG")
        dinamo_file = self.logs_dir / "dinamo_rent.log"
        error_file = self.logs_dir / "errores.log"
        dinamo_content = dinamo_file.read_text(encoding="utf-8")
        assert "Mensaje solo DEBUG" in dinamo_content
        if error_file.exists():
            error_content = error_file.read_text(encoding="utf-8")
            assert "Mensaje solo DEBUG" not in error_content

    def test_warning_aparece_en_errores(self):
        """WARNING message appears in errores.log."""
        from core.logger import get_logger

        log = get_logger("test_warning")
        log.warning("Mensaje de advertencia")
        error_file = self.logs_dir / "errores.log"
        assert error_file.exists()
        content = error_file.read_text(encoding="utf-8")
        assert "Mensaje de advertencia" in content

    def test_audit_escribe_en_audit_log(self):
        """Audit logger writes to audit.log."""
        from core.logger import get_audit_logger

        audit = get_audit_logger()
        audit.info("Accion de auditoria")
        audit_file = self.logs_dir / "audit.log"
        assert audit_file.exists()
        content = audit_file.read_text(encoding="utf-8")
        assert "Accion de auditoria" in content

    def test_audit_log_tiene_marcador_AUDIT(self):
        """Audit log lines contain the AUDIT marker."""
        from core.logger import get_audit_logger

        audit = get_audit_logger()
        audit.info("Verificar marcador")
        audit_file = self.logs_dir / "audit.log"
        content = audit_file.read_text(encoding="utf-8")
        assert "AUDIT" in content

    def test_multiples_mensajes_se_acumulan(self):
        """Multiple log messages accumulate in the file."""
        from core.logger import get_logger

        log = get_logger("test_accumulate")
        for i in range(5):
            log.info("Mensaje número %d", i + 1)
        log_file = self.logs_dir / "dinamo_rent.log"
        content = log_file.read_text(encoding="utf-8")
        for i in range(5):
            assert f"Mensaje número {i + 1}" in content

    def test_nombre_del_logger_aparece_en_linea(self):
        """Each log line contains the logger name."""
        from core.logger import get_logger

        log = get_logger("MiModulo")
        log.info("Log con nombre")
        log_file = self.logs_dir / "dinamo_rent.log"
        content = log_file.read_text(encoding="utf-8")
        assert "Dinamo Rent ERP.MiModulo" in content


# ═══════════════════════════════════════════════════════════════════════════════
# Log level filtering (errores.log)
# ═══════════════════════════════════════════════════════════════════════════════


class TestLogLevelFiltering:
    """Verify log levels are properly filtered in errores.log."""

    @pytest.fixture(autouse=True)
    def _setup(self, monkeypatch, tmp_path):
        """Isolate logs and reset state."""
        import core.logger as log_mod

        monkeypatch.setattr(log_mod, "LOGS_DIR", tmp_path)
        monkeypatch.setattr(log_mod, "_configured", False)
        _cleanup_root_handlers()
        self.logs_dir = tmp_path

    def _read_error_log(self):
        ef = self.logs_dir / "errores.log"
        return ef.read_text(encoding="utf-8") if ef.exists() else ""

    def test_debug_no_aparece(self):
        """DEBUG messages do NOT appear in errores.log."""
        from core.logger import get_logger

        log = get_logger("level_debug")
        log.debug("debug_should_not_appear")
        content = self._read_error_log()
        assert "debug_should_not_appear" not in content

    def test_info_no_aparece(self):
        """INFO messages do NOT appear in errores.log."""
        from core.logger import get_logger

        log = get_logger("level_info")
        log.info("info_should_not_appear")
        content = self._read_error_log()
        assert "info_should_not_appear" not in content

    def test_warning_si_aparece(self):
        """WARNING messages appear in errores.log."""
        from core.logger import get_logger

        log = get_logger("level_warning")
        log.warning("warning_should_appear")
        content = self._read_error_log()
        assert "warning_should_appear" in content

    def test_error_si_aparece(self):
        """ERROR messages appear in errores.log."""
        from core.logger import get_logger

        log = get_logger("level_error")
        log.error("error_should_appear")
        content = self._read_error_log()
        assert "error_should_appear" in content

    def test_critical_si_aparece(self):
        """CRITICAL messages appear in errores.log."""
        from core.logger import get_logger

        log = get_logger("level_critical")
        log.critical("critical_should_appear")
        content = self._read_error_log()
        assert "critical_should_appear" in content


# ═══════════════════════════════════════════════════════════════════════════════
# RotatingFileHandler configuration
# ═══════════════════════════════════════════════════════════════════════════════


class TestRotationConfig:
    """RotatingFileHandler parameters match expected values."""

    @pytest.fixture(autouse=True)
    def _setup(self, monkeypatch, tmp_path):
        """Isolate logs and reset state."""
        import core.logger as log_mod

        monkeypatch.setattr(log_mod, "LOGS_DIR", tmp_path)
        monkeypatch.setattr(log_mod, "_configured", False)
        _cleanup_root_handlers()

    def _get_handler(self, level, handler_type=logging.handlers.RotatingFileHandler):
        """Find a RotatingFileHandler by level."""
        root = logging.getLogger("Dinamo Rent ERP")
        for h in root.handlers:
            if isinstance(h, handler_type) and h.level == level:
                return h
        return None

    def test_dinamo_log_max_bytes(self):
        """dinamo_rent.log RotatingFileHandler maxBytes = 5 MB."""
        from core.logger import _setup_root_logger

        _setup_root_logger()
        handler = self._get_handler(logging.DEBUG)
        assert handler is not None
        assert handler.maxBytes == 5 * 1024 * 1024

    def test_dinamo_log_backup_count(self):
        """dinamo_rent.log RotatingFileHandler backupCount = 5."""
        from core.logger import _setup_root_logger

        _setup_root_logger()
        handler = self._get_handler(logging.DEBUG)
        assert handler is not None
        assert handler.backupCount == 5

    def test_errores_log_max_bytes(self):
        """errores.log RotatingFileHandler maxBytes = 2 MB."""
        from core.logger import _setup_root_logger

        _setup_root_logger()
        handler = self._get_handler(logging.WARNING)
        assert handler is not None
        assert handler.maxBytes == 2 * 1024 * 1024

    def test_errores_log_backup_count(self):
        """errores.log RotatingFileHandler backupCount = 3."""
        from core.logger import _setup_root_logger

        _setup_root_logger()
        handler = self._get_handler(logging.WARNING)
        assert handler is not None
        assert handler.backupCount == 3

    def test_audit_handler_timed_config(self):
        """Audit logger TimedRotatingFileHandler: midnight, 30 backups."""
        from core.logger import get_audit_logger

        audit = get_audit_logger()
        handler = audit.handlers[0]
        assert isinstance(handler, logging.handlers.TimedRotatingFileHandler)
        assert handler.when.lower() == "midnight"
        assert handler.backupCount == 30

    def test_encoding_utf8(self):
        """All file handlers use UTF-8 encoding."""
        from core.logger import _setup_root_logger

        _setup_root_logger()
        root = logging.getLogger("Dinamo Rent ERP")
        for h in root.handlers:
            if isinstance(h, logging.handlers.RotatingFileHandler):
                assert h.encoding == "utf-8"


# ═══════════════════════════════════════════════════════════════════════════════
# Module exports
# ═══════════════════════════════════════════════════════════════════════════════


class TestModuleExports:
    """Ensure all expected symbols are importable."""

    def test_get_logger_importable(self):
        from core.logger import get_logger

        assert callable(get_logger)

    def test_get_audit_logger_importable(self):
        from core.logger import get_audit_logger

        assert callable(get_audit_logger)

    def test_APP_NAME_importable(self):
        from core.logger import APP_NAME

        assert isinstance(APP_NAME, str)
        assert APP_NAME == "Dinamo Rent ERP"

    def test_LOGS_DIR_importable(self):
        from core.logger import LOGS_DIR
        from pathlib import Path

        assert isinstance(LOGS_DIR, Path)
