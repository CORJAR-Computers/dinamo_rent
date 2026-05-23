"""
test_security.py — Unit tests for core/security.py

Covers:
  IPRateLimiter       — rate limiting, block, remaining attempts, cleanup
  LoginAttemptTracker — failed attempts, lockout, rate limiting, reset, IP limiting
  SecurityManager     — hash/verify password, validate strength, sanitize input, token gen
  SessionManager      — create/get/destroy sessions, expiry, purge

Strategy:
  - Mock time.time() with a controllable fake clock for deterministic timing tests
  - Reset global state (login_tracker, SessionManager._sessions) between classes
  - Test edge cases: empty passwords, malformed hashes, expired sessions, blocked IPs

Run: pytest tests/test_security.py -v
"""

import time as time_module
import pytest


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def fake_time():
    """
    Returns a mutable list [current_time] so tests can advance the clock.
    Usage:
        ft = fake_time
        ft[0] += 10   # advance 10 seconds
    """
    clock = [1000.0]
    return clock


@pytest.fixture
def patch_time(monkeypatch, fake_time):
    """Monkeypatch time.time() to return fake_time[0]."""
    monkeypatch.setattr(time_module, "time", lambda: fake_time[0])
    return fake_time


# ═══════════════════════════════════════════════════════════════════════════════
# IPRateLimiter
# ═══════════════════════════════════════════════════════════════════════════════

class TestIPRateLimiter:
    """Rate limiting by IP address."""

    def test_record_request_incrementa(self, patch_time):
        """record_request returns increasing count."""
        from core.security import IPRateLimiter
        limiter = IPRateLimiter()
        assert limiter.record_request("192.168.1.1") == 1
        assert limiter.record_request("192.168.1.1") == 2
        assert limiter.record_request("10.0.0.1") == 1  # different IP

    def test_is_rate_limited_false_sin_intentos(self, patch_time):
        """IP with no attempts is not rate limited."""
        from core.security import IPRateLimiter
        limiter = IPRateLimiter()
        assert limiter.is_rate_limited("10.0.0.99") is False

    def test_block_ip_funciona(self, patch_time):
        """block_ip makes is_rate_limited return True."""
        from core.security import IPRateLimiter
        limiter = IPRateLimiter()
        limiter.block_ip("10.0.0.1", duration=60)
        assert limiter.is_rate_limited("10.0.0.1") is True

    def test_block_expira(self, patch_time):
        """Block expires after duration."""
        from core.security import IPRateLimiter
        limiter = IPRateLimiter()
        limiter.block_ip("10.0.0.1", duration=60)
        patch_time[0] += 61
        assert limiter.is_rate_limited("10.0.0.1") is False

    def test_remaining_attempts_init(self, patch_time):
        """Fresh IP has max attempts remaining."""
        from core.security import IPRateLimiter, IP_MAX_ATTEMPTS_IN_WINDOW
        limiter = IPRateLimiter()
        assert limiter.get_remaining_attempts("10.0.0.1") == IP_MAX_ATTEMPTS_IN_WINDOW

    def test_remaining_attempts_decrece(self, patch_time):
        """After recording, remaining attempts decrease."""
        from core.security import IPRateLimiter, IP_MAX_ATTEMPTS_IN_WINDOW
        limiter = IPRateLimiter()
        for _ in range(5):
            limiter.record_request("10.0.0.1")
        assert limiter.get_remaining_attempts("10.0.0.1") == IP_MAX_ATTEMPTS_IN_WINDOW - 5

    def test_clean_old_timestamps(self, patch_time):
        """Old timestamps are cleaned after the window."""
        from core.security import IPRateLimiter
        limiter = IPRateLimiter()
        limiter.record_request("10.0.0.1")
        patch_time[0] += 120  # past the 60s window
        limiter.record_request("10.0.0.1")  # triggers cleanup
        assert limiter.get_remaining_attempts("10.0.0.1") > 0  # only 1 recent

    def test_ips_independientes(self, patch_time):
        """Different IPs have independent rate limits."""
        from core.security import IPRateLimiter
        limiter = IPRateLimiter()
        limiter.block_ip("10.0.0.1")
        assert limiter.is_rate_limited("10.0.0.1") is True
        assert limiter.is_rate_limited("10.0.0.2") is False


# ═══════════════════════════════════════════════════════════════════════════════
# LoginAttemptTracker
# ═══════════════════════════════════════════════════════════════════════════════

class TestLoginAttemptTracker:
    """Tracks login attempts with lockout and IP rate limiting."""

    def test_record_failed_attempt_incrementa(self, patch_time):
        """record_failed_attempt returns increasing count."""
        from core.security import LoginAttemptTracker
        t = LoginAttemptTracker()
        assert t.record_failed_attempt("user1") == 1
        assert t.record_failed_attempt("user1") == 2
        assert t.record_failed_attempt("user2") == 1

    def test_is_locked_false_sin_intentos(self, patch_time):
        """User with no failed attempts is not locked."""
        from core.security import LoginAttemptTracker
        t = LoginAttemptTracker()
        assert t.is_locked("user1") is False

    def test_lock_account_bloquea(self, patch_time):
        """lock_account makes is_locked return True."""
        from core.security import LoginAttemptTracker
        t = LoginAttemptTracker()
        t.lock_account("user1")
        assert t.is_locked("user1") is True

    def test_lock_expira(self, patch_time):
        """Account unlock after lockout duration."""
        from core.security import LoginAttemptTracker
        t = LoginAttemptTracker()
        t.lock_account("user1")
        patch_time[0] += 1801  # past 30 min
        assert t.is_locked("user1") is False

    def test_lock_expira_reinicia_intentos(self, patch_time):
        """After lock expires, failed attempts reset to 0."""
        from core.security import LoginAttemptTracker
        t = LoginAttemptTracker()
        t.lock_account("user1")
        patch_time[0] += 1801
        t.is_locked("user1")  # triggers auto-unlock
        assert t.get_remaining_attempts("user1") == 5

    def test_reset_attempts_funciona(self, patch_time):
        """reset_attempts clears failed attempts and timestamps."""
        from core.security import LoginAttemptTracker
        t = LoginAttemptTracker()
        t.record_failed_attempt("user1")
        t.reset_attempts("user1")
        assert t.get_remaining_attempts("user1") == 5

    def test_remaining_attempts_decrece(self, patch_time):
        """After failures, remaining attempts decrease."""
        from core.security import LoginAttemptTracker
        t = LoginAttemptTracker()
        for _ in range(3):
            t.record_failed_attempt("user1")
        assert t.get_remaining_attempts("user1") == 2

    def test_lockout_remaining_time(self, patch_time):
        """get_lockout_remaining_time returns remaining seconds."""
        from core.security import LoginAttemptTracker
        t = LoginAttemptTracker()
        t.lock_account("user1")
        remaining = t.get_lockout_remaining_time("user1")
        assert 1795 <= remaining <= 1800

    def test_lockout_remaining_time_no_lock(self, patch_time):
        """get_lockout_remaining_time returns 0 if not locked."""
        from core.security import LoginAttemptTracker
        t = LoginAttemptTracker()
        assert t.get_lockout_remaining_time("user1") == 0

    def test_check_rate_limit_no_excedido(self, patch_time):
        """check_rate_limit returns False under the limit."""
        from core.security import LoginAttemptTracker
        t = LoginAttemptTracker()
        for _ in range(5):
            t.record_failed_attempt("user1")
        assert t.check_rate_limit("user1") is False

    def test_record_failed_con_ip(self, patch_time):
        """record_failed_attempt with IP also records on IP tracker."""
        from core.security import LoginAttemptTracker
        t = LoginAttemptTracker()
        t.record_failed_attempt("user1", ip="10.0.0.1")
        assert t._ip_tracker.get_remaining_attempts("10.0.0.1") < 20

    def test_check_ip_rate_limit_no_bloqueo(self, patch_time):
        """check_ip_rate_limit returns (False, count) under limit."""
        from core.security import LoginAttemptTracker
        t = LoginAttemptTracker()
        blocked, count = t.check_ip_rate_limit("10.0.0.1")
        assert blocked is False
        assert count == 1

    def test_check_ip_rate_limit_bloqueado(self, patch_time):
        """check_ip_rate_limit returns (True, count) after exceeding limit."""
        from core.security import LoginAttemptTracker, IP_MAX_ATTEMPTS_IN_WINDOW
        t = LoginAttemptTracker()
        final_count = IP_MAX_ATTEMPTS_IN_WINDOW + 1
        for _ in range(final_count):
            t.check_ip_rate_limit("10.0.0.99")
        blocked, count = t.check_ip_rate_limit("10.0.0.99")
        assert blocked is True
        assert count >= final_count

    def test_identificadores_independientes(self, patch_time):
        """Different identifiers have independent attempt counts."""
        from core.security import LoginAttemptTracker
        t = LoginAttemptTracker()
        t.record_failed_attempt("alice")
        t.record_failed_attempt("alice")
        t.record_failed_attempt("bob")
        assert t.get_remaining_attempts("alice") == 3
        assert t.get_remaining_attempts("bob") == 4

    def test_check_rate_limit_excede_ventana(self, patch_time):
        """check_rate_limit returns True when user exceeds MAX_LOGIN_ATTEMPTS_IN_WINDOW."""
        from core.security import LoginAttemptTracker, MAX_LOGIN_ATTEMPTS_IN_WINDOW
        t = LoginAttemptTracker()
        for _ in range(MAX_LOGIN_ATTEMPTS_IN_WINDOW + 1):
            t.record_failed_attempt("user1")
        assert t.check_rate_limit("user1") is True

    def test_check_rate_limit_ip_bloqueada(self, patch_time):
        """check_rate_limit returns True when IP is rate limited."""
        from core.security import LoginAttemptTracker
        t = LoginAttemptTracker()
        t._ip_tracker.block_ip("10.0.0.99", duration=300)
        # Use any identifier; IP blocking triggers the second return True
        assert t.check_rate_limit("user1", ip="10.0.0.99") is True

    def test_check_ip_rate_limit_sin_ip(self, patch_time):
        """check_ip_rate_limit(None) returns (False, 0)."""
        from core.security import LoginAttemptTracker
        t = LoginAttemptTracker()
        blocked, count = t.check_ip_rate_limit(None)
        assert blocked is False
        assert count == 0


# ═══════════════════════════════════════════════════════════════════════════════
# SecurityManager — hash & verify password
# ═══════════════════════════════════════════════════════════════════════════════

class TestSecurityManagerHashPassword:
    """SecurityManager.hash_password and verify_password."""

    def test_hash_retorna_string_con_salt(self):
        """hash_password returns 'hash:salt' format."""
        from core.security import SecurityManager
        result = SecurityManager.hash_password("MiPassword123!")
        assert isinstance(result, str)
        assert ":" in result
        parts = result.split(":")
        # hex hash is 64 chars (sha256) + salt is 32 chars (16 bytes hex)
        assert len(parts) == 2
        assert len(parts[0]) == 64  # sha256 hex digest
        assert len(parts[1]) == 32  # 16 bytes hex

    def test_hash_diferente_para_misma_password(self):
        """Each call produces a different hash due to random salt."""
        from core.security import SecurityManager
        h1 = SecurityManager.hash_password("MiPassword123!")
        h2 = SecurityManager.hash_password("MiPassword123!")
        assert h1 != h2

    def test_verify_correcta(self):
        """verify_password returns True for correct password."""
        from core.security import SecurityManager
        h = SecurityManager.hash_password("MiPassword123!")
        assert SecurityManager.verify_password(h, "MiPassword123!") is True

    def test_verify_incorrecta(self):
        """verify_password returns False for wrong password."""
        from core.security import SecurityManager
        h = SecurityManager.hash_password("MiPassword123!")
        assert SecurityManager.verify_password(h, "WrongPassword") is False

    def test_verify_empty_stored(self):
        """verify_password returns False for empty stored hash."""
        from core.security import SecurityManager
        assert SecurityManager.verify_password("", "anything") is False

    def test_verify_malformed_hash(self):
        """verify_password returns False for hash without ':'."""
        from core.security import SecurityManager
        assert SecurityManager.verify_password("invalidhash", "password") is False

    def test_verify_stored_sin_salt(self):
        """verify_password returns False when stored lacks salt part."""
        from core.security import SecurityManager
        assert SecurityManager.verify_password("abc123", "password") is False

    def test_hash_empty_password(self):
        """hash_password('') returns empty string."""
        from core.security import SecurityManager
        assert SecurityManager.hash_password("") == ""

    def test_hash_none_password(self):
        """hash_password(None) handled as falsy — returns empty string."""
        from core.security import SecurityManager
        assert SecurityManager.hash_password(None) == ""

    def test_verify_password_exception_caught(self):
        """verify_password catches Exception and returns False (lines 192-193)."""
        from core.security import SecurityManager
        # provided=None causes .encode() to raise AttributeError → caught by except
        assert SecurityManager.verify_password("abc:def", None) is False


# ═══════════════════════════════════════════════════════════════════════════════
# SecurityManager — validate_password_strength
# ═══════════════════════════════════════════════════════════════════════════════

class TestSecurityManagerValidateStrength:
    """SecurityManager.validate_password_strength."""

    def test_password_valida_no_retorna_errores(self):
        """Strong password returns empty list."""
        from core.security import SecurityManager
        errors = SecurityManager.validate_password_strength("ValidP@ss1")
        assert errors == []

    def test_muy_corta(self):
        """Password < 8 chars returns length error."""
        from core.security import SecurityManager
        errors = SecurityManager.validate_password_strength("Ab1!")
        assert any("8 caracteres" in e for e in errors)

    def test_muy_larga(self):
        """Password > 128 chars returns length error."""
        from core.security import SecurityManager
        pwd = "A" * 129
        assert len(pwd) > 128
        errors = SecurityManager.validate_password_strength(pwd)
        assert any("128" in e for e in errors)

    def test_sin_mayuscula(self):
        """Password without uppercase returns error."""
        from core.security import SecurityManager
        errors = SecurityManager.validate_password_strength("sinmayuscula1@")
        assert any("mayúscula" in e for e in errors)

    def test_sin_minuscula(self):
        """Password without lowercase returns error."""
        from core.security import SecurityManager
        errors = SecurityManager.validate_password_strength("SINMINUSCULA1@")
        assert any("minúscula" in e for e in errors)

    def test_sin_numero(self):
        """Password without digit returns error."""
        from core.security import SecurityManager
        errors = SecurityManager.validate_password_strength("SinDigito@")
        assert any("número" in e for e in errors)

    def test_sin_caracter_especial(self):
        """Password without special char returns error."""
        from core.security import SecurityManager
        errors = SecurityManager.validate_password_strength("SinEspecial1")
        assert any("especial" in e for e in errors)

    def test_vacia_retorna_varios_errores(self):
        """Empty password returns multiple errors."""
        from core.security import SecurityManager
        errors = SecurityManager.validate_password_strength("")
        assert len(errors) >= 4  # at least length, uppercase, digit, special

    def test_borde_8_caracteres(self):
        """Exactly 8 chars with valid composition should pass."""
        from core.security import SecurityManager
        errors = SecurityManager.validate_password_strength("Pass123!")
        assert errors == []

    def test_caracteres_especiales_variados(self):
        """Various special characters are accepted."""
        from core.security import SecurityManager
        passwords = [
            "Pass123!@#$%^&*()",
            "Pass123,.\":{}|<>",
            "Pass123?/+-_=~",
        ]
        for pwd in passwords:
            errors = SecurityManager.validate_password_strength(pwd)
            assert errors == [], f"Failed for: {pwd}" if errors else True


# ═══════════════════════════════════════════════════════════════════════════════
# SecurityManager — sanitize_input
# ═══════════════════════════════════════════════════════════════════════════════

class TestSecurityManagerSanitizeInput:
    """SecurityManager.sanitize_input."""

    def test_sanitize_vacio(self):
        """sanitize_input('') returns ''."""
        from core.security import SecurityManager
        assert SecurityManager.sanitize_input("") == ""

    def test_sanitize_none(self):
        """sanitize_input(None) returns ''."""
        from core.security import SecurityManager
        assert SecurityManager.sanitize_input(None) == ""

    def test_texto_normal_pasa(self):
        """Normal text passes through unchanged."""
        from core.security import SecurityManager
        result = SecurityManager.sanitize_input("Hola mundo")
        assert result == "Hola mundo"

    def test_limita_longitud(self):
        """Input is truncated to max_length."""
        from core.security import SecurityManager
        long_text = "A" * 1000
        result = SecurityManager.sanitize_input(long_text, max_length=10)
        assert len(result) == 10
        assert result == "A" * 10

    def test_elimina_null_bytes(self):
        """Null bytes are stripped."""
        from core.security import SecurityManager
        result = SecurityManager.sanitize_input("Hola\x00Mundo")
        assert "\\x00" not in result
        assert result == "HolaMundo"

    def test_trim_espacios(self):
        """Leading/trailing spaces are trimmed."""
        from core.security import SecurityManager
        result = SecurityManager.sanitize_input("  texto con espacios  ")
        assert result == "texto con espacios"

    def test_rechaza_script_tag(self):
        """Input with <script> raises InputSanitizationError."""
        from core.security import SecurityManager
        from core.exceptions import InputSanitizationError
        with pytest.raises(InputSanitizationError):
            SecurityManager.sanitize_input("<script>alert('xss')</script>")

    def test_rechaza_javascript_protocol(self):
        """Input with javascript: raises InputSanitizationError."""
        from core.security import SecurityManager
        from core.exceptions import InputSanitizationError
        with pytest.raises(InputSanitizationError):
            SecurityManager.sanitize_input("javascript:alert(1)")

    def test_rechaza_event_handler(self):
        """Input with onclick= raises InputSanitizationError."""
        from core.security import SecurityManager
        from core.exceptions import InputSanitizationError
        with pytest.raises(InputSanitizationError):
            SecurityManager.sanitize_input('<img onclick="evil()" />')

    def test_rechaza_iframe(self):
        """Input with <iframe> raises InputSanitizationError."""
        from core.security import SecurityManager
        from core.exceptions import InputSanitizationError
        with pytest.raises(InputSanitizationError):
            SecurityManager.sanitize_input("<iframe src='http://evil.com'>")

    def test_rechaza_sql_union(self):
        """Input with SQL injection raises InputSanitizationError."""
        from core.security import SecurityManager
        from core.exceptions import InputSanitizationError
        with pytest.raises(InputSanitizationError):
            SecurityManager.sanitize_input("1 UNION SELECT * FROM users")

    def test_rechaza_sql_drop(self):
        """Input with DROP TABLE raises InputSanitizationError."""
        from core.security import SecurityManager
        from core.exceptions import InputSanitizationError
        with pytest.raises(InputSanitizationError):
            SecurityManager.sanitize_input("'; DROP TABLE users; --")

    def test_permitir_html_si_allow_html(self):
        """Html is allowed when allow_html=True."""
        from core.security import SecurityManager
        result = SecurityManager.sanitize_input("<b>Hola</b>", allow_html=True)
        assert "<b>Hola</b>" in result


# ═══════════════════════════════════════════════════════════════════════════════
# SecurityManager — generate_secure_token
# ═══════════════════════════════════════════════════════════════════════════════

class TestSecurityManagerGenerateToken:
    """SecurityManager.generate_secure_token."""

    def test_genera_token_string(self):
        """generate_secure_token returns a non-empty string."""
        from core.security import SecurityManager
        token = SecurityManager.generate_secure_token()
        assert isinstance(token, str)
        assert len(token) > 0

    def test_longitud_default(self):
        """generate_secure_token() with default length=32 produces 43 chars (base64)."""
        from core.security import SecurityManager
        token = SecurityManager.generate_secure_token()
        # token_urlsafe(32) produces ~43 chars
        assert len(token) >= 32

    def test_longitud_personalizada(self):
        """generate_secure_token(16) produces ~22 chars."""
        from core.security import SecurityManager
        token = SecurityManager.generate_secure_token(length=16)
        assert len(token) >= 16

    def test_tokens_son_unicos(self):
        """Multiple calls produce different tokens."""
        from core.security import SecurityManager
        tokens = {SecurityManager.generate_secure_token() for _ in range(100)}
        assert len(tokens) == 100

    def test_token_es_url_safe(self):
        """Token contains only URL-safe characters (no + or /)."""
        from core.security import SecurityManager
        token = SecurityManager.generate_secure_token()
        assert "+" not in token
        assert "/" not in token
        assert "=" not in token


# ═══════════════════════════════════════════════════════════════════════════════
# SessionManager
# ═══════════════════════════════════════════════════════════════════════════════

class TestSessionManager:
    """Session lifecycle: create, get, destroy, expiry, purge."""

    @pytest.fixture(autouse=True)
    def _clean_sessions(self):
        """Clear sessions before each test in this class."""
        from core.security import SessionManager
        SessionManager._sessions.clear()

    def test_create_retorna_token(self):
        """create() returns a non-empty session token."""
        from core.security import SessionManager
        sid = SessionManager.create(user_id=1, username="admin",
                                    role="Administrador", nombre="Admin")
        assert isinstance(sid, str)
        assert len(sid) > 0

    def test_get_retorna_datos(self, patch_time):
        """get() returns session data for valid session."""
        from core.security import SessionManager
        sid = SessionManager.create(user_id=1, username="admin",
                                    role="Administrador", nombre="Admin")
        data = SessionManager.get(sid)
        assert data is not None
        assert data["user_id"] == 1
        assert data["username"] == "admin"
        assert data["role"] == "Administrador"
        assert data["nombre"] == "Admin"

    def test_get_invalido_retorna_none(self):
        """get() returns None for non-existent session."""
        from core.security import SessionManager
        assert SessionManager.get("nonexistent") is None

    def test_destroy_elimina_sesion(self, patch_time):
        """destroy() removes session from store."""
        from core.security import SessionManager
        sid = SessionManager.create(user_id=1, username="admin",
                                    role="Admin", nombre="Admin")
        SessionManager.destroy(sid)
        assert SessionManager.get(sid) is None

    def test_get_actualiza_last_activity(self, patch_time):
        """get() updates last_activity timestamp."""
        from core.security import SessionManager
        sid = SessionManager.create(user_id=1, username="admin",
                                    role="Admin", nombre="Admin")
        data_before = SessionManager._sessions[sid]
        ts_before = data_before["last_activity"]

        patch_time[0] += 60
        SessionManager.get(sid)
        ts_after = SessionManager._sessions[sid]["last_activity"]
        assert ts_after > ts_before

    def test_session_expira(self, patch_time):
        """get() raises SesionExpirada after SESSION_TIMEOUT."""
        from core.security import SessionManager
        from core.exceptions import SesionExpirada
        sid = SessionManager.create(user_id=1, username="admin",
                                    role="Admin", nombre="Admin")
        patch_time[0] += 3601  # past SESSION_TIMEOUT (3600s)
        with pytest.raises(SesionExpirada):
            SessionManager.get(sid)

    def test_session_expirada_se_elimina(self, patch_time):
        """Expired session is removed from store after get() raises."""
        from core.security import SessionManager
        sid = SessionManager.create(user_id=1, username="admin",
                                    role="Admin", nombre="Admin")
        patch_time[0] += 3601
        try:
            SessionManager.get(sid)
        except Exception:
            pass
        assert SessionManager._sessions.get(sid) is None

    def test_purge_expired_retorna_cantidad(self, patch_time):
        """purge_expired() removes expired sessions and returns count."""
        from core.security import SessionManager
        s1 = SessionManager.create(user_id=1, username="a", role="R", nombre="A")
        s2 = SessionManager.create(user_id=2, username="b", role="R", nombre="B")
        patch_time[0] += 3601
        s3 = SessionManager.create(user_id=3, username="c", role="R", nombre="C")

        purged = SessionManager.purge_expired()
        assert purged == 2  # s1 and s2 expired, s3 is recent
        assert SessionManager.get(s3) is not None
        assert SessionManager._sessions.get(s1) is None

    def test_purge_expired_sin_expiradas(self, patch_time):
        """purge_expired() returns 0 when no sessions are expired."""
        from core.security import SessionManager
        SessionManager.create(user_id=1, username="a", role="R", nombre="A")
        SessionManager.create(user_id=2, username="b", role="R", nombre="B")
        purged = SessionManager.purge_expired()
        assert purged == 0

    def test_multiple_sesiones_independientes(self, patch_time):
        """Multiple sessions can coexist independently."""
        from core.security import SessionManager
        s1 = SessionManager.create(user_id=1, username="alice",
                                   role="Admin", nombre="Alice")
        s2 = SessionManager.create(user_id=2, username="bob",
                                   role="Operador", nombre="Bob")
        d1 = SessionManager.get(s1)
        d2 = SessionManager.get(s2)
        assert d1["username"] == "alice"
        assert d2["username"] == "bob"
        assert d1["user_id"] != d2["user_id"]


# ═══════════════════════════════════════════════════════════════════════════════
# Global instances
# ═══════════════════════════════════════════════════════════════════════════════

class TestGlobalInstances:
    """Global instances (login_tracker) are importable."""

    def test_login_tracker_importable(self):
        from core.security import login_tracker
        from core.security import LoginAttemptTracker
        assert isinstance(login_tracker, LoginAttemptTracker)
