"""
test_security_utils.py — Unit tests for core/security_utils.py

Covers:
  FileEncryptor:     _derive_key, encrypt_file, decrypt_file
  SecureEnvManager:  mask_sensitive_value, validate_env_security, secure_delete_file
  CredentialManager: store, get, clear, list_services

Run: pytest tests/test_security_utils.py -v
"""

import os
import tempfile

import pytest

from core.security_utils import (
    FileEncryptor,
    SecureEnvManager,
    CredentialManager,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture(autouse=True)
def reset_credential_manager():
    """Clear CredentialManager state before each test."""
    CredentialManager.clear()
    yield


@pytest.fixture
def temp_file():
    """Create a temporary file with known content for encrypt/decrypt tests."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        f.write(b"Contenido secreto de prueba para encriptacion Dinamo Rent")
        temp_path = f.name
    yield temp_path
    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)


@pytest.fixture
def temp_env_file():
    """Create a temporary .env file for validation tests."""
    content = (
        "# DB Config\n"
        "DB_HOST=localhost\n"
        "DB_PASSWORD=\n"
        "DB_USER=root\n"
        "# Security\n"
        "ADMIN_PASSWORD=123\n"
        "SECRET_KEY=abc\n"
        "API_TOKEN=weak_token\n"
    )
    with tempfile.NamedTemporaryFile(delete=False, suffix=".env", mode="w") as f:
        f.write(content)
        env_path = f.name
    yield env_path
    if os.path.exists(env_path):
        os.remove(env_path)


# ═══════════════════════════════════════════════════════════════════════════════
# FileEncryptor._derive_key
# ═══════════════════════════════════════════════════════════════════════════════


class TestDeriveKey:
    def test_retorna_bytes(self):
        """_derive_key returns a bytes object."""
        salt = os.urandom(16)
        key = FileEncryptor._derive_key("password123", salt)
        assert isinstance(key, bytes)

    def test_longitud_esperada(self):
        """Derived key is 44 bytes (32 bytes base64-encoded)."""
        salt = os.urandom(16)
        key = FileEncryptor._derive_key("password123", salt)
        assert len(key) == 44  # 32 bytes -> 44 base64 chars

    def test_misma_password_mismo_salt_misma_clave(self):
        """Same password and salt produce the same key."""
        salt = os.urandom(16)
        key1 = FileEncryptor._derive_key("password123", salt)
        key2 = FileEncryptor._derive_key("password123", salt)
        assert key1 == key2

    def test_distinto_salt_distinta_clave(self):
        """Different salts produce different keys for same password."""
        salt1 = os.urandom(16)
        salt2 = os.urandom(16)
        key1 = FileEncryptor._derive_key("password123", salt1)
        key2 = FileEncryptor._derive_key("password123", salt2)
        assert key1 != key2

    def test_distinta_password_distinta_clave(self):
        """Different passwords produce different keys for same salt."""
        salt = os.urandom(16)
        key1 = FileEncryptor._derive_key("password123", salt)
        key2 = FileEncryptor._derive_key("different_password", salt)
        assert key1 != key2

    def test_password_vacia(self):
        """Empty password still produces a key (no crash)."""
        salt = os.urandom(16)
        key = FileEncryptor._derive_key("", salt)
        assert isinstance(key, bytes)
        assert len(key) == 44


# ═══════════════════════════════════════════════════════════════════════════════
# FileEncryptor.encrypt_file
# ═══════════════════════════════════════════════════════════════════════════════


class TestEncryptFile:
    def test_encripta_archivo_retorna_ruta(self, temp_file):
        """encrypt_file returns the output path."""
        output = FileEncryptor.encrypt_file(temp_file, "s3cr3t")
        assert isinstance(output, str)
        assert os.path.exists(output)
        # Cleanup
        os.remove(output)

    def test_output_default_con_extension_enc(self, temp_file):
        """Default output appends .enc to original filename."""
        output = FileEncryptor.encrypt_file(temp_file, "s3cr3t")
        assert output == temp_file + ".enc"
        os.remove(output)

    def test_output_personalizado(self, temp_file):
        """Custom output_path is respected."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".enc") as f:
            custom_output = f.name
        try:
            output = FileEncryptor.encrypt_file(temp_file, "s3cr3t", custom_output)
            assert output == custom_output
            assert os.path.exists(custom_output)
        finally:
            if os.path.exists(custom_output):
                os.remove(custom_output)
            if os.path.exists(temp_file + ".enc"):
                os.remove(temp_file + ".enc")

    def test_archivo_inexistente_lanza_error(self):
        """Non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="no encontrado"):
            FileEncryptor.encrypt_file("/ruta/inexistente.txt", "pass")

    def test_archivo_encriptado_tiene_salt(self, temp_file):
        """Encrypted file starts with a 16-byte salt before the encrypted data."""
        output = FileEncryptor.encrypt_file(temp_file, "s3cr3t")
        try:
            with open(output, "rb") as f:
                salt = f.read(16)
                payload = f.read()
            assert len(salt) == 16
            assert len(payload) > 0
        finally:
            os.remove(output)

    def test_archivo_encriptado_diferente_al_original(self, temp_file):
        """Encrypted content is different from original content."""
        with open(temp_file, "rb") as f:
            original = f.read()
        output = FileEncryptor.encrypt_file(temp_file, "s3cr3t")
        try:
            with open(output, "rb") as f:
                encrypted = f.read()
            assert encrypted != original
        finally:
            os.remove(output)

    def test_misma_password_distintos_salts(self, temp_file):
        """Same password produces different encrypted output (different salt)."""
        # Use different output paths to avoid second call overwriting first
        output1 = temp_file + ".enc1"
        output2 = temp_file + ".enc2"
        out1 = FileEncryptor.encrypt_file(temp_file, "s3cr3t", output1)
        out2 = FileEncryptor.encrypt_file(temp_file, "s3cr3t", output2)
        try:
            with open(out1, "rb") as f:
                data1 = f.read()
            with open(out2, "rb") as f:
                data2 = f.read()
            assert data1 != data2
        finally:
            for p in [out1, out2, temp_file + ".enc"]:
                if os.path.exists(p):
                    os.remove(p)

    def test_archivo_vacio(self, temp_file):
        """Empty file is encrypted without error."""
        # Create an empty file
        empty_path = temp_file + ".empty"
        with open(empty_path, "w") as _:
            pass
        try:
            output = FileEncryptor.encrypt_file(empty_path, "pass")
            assert os.path.exists(output)
        finally:
            if os.path.exists(empty_path):
                os.remove(empty_path)
            if os.path.exists(output):
                os.remove(output)


# ═══════════════════════════════════════════════════════════════════════════════
# FileEncryptor.decrypt_file
# ═══════════════════════════════════════════════════════════════════════════════


class TestDecryptFile:
    def test_ciclo_completo_encriptar_desencriptar(self, temp_file):
        """Round-trip encrypt -> decrypt produces original content."""
        encrypted = FileEncryptor.encrypt_file(temp_file, "s3cr3t")
        decrypted = FileEncryptor.decrypt_file(encrypted, "s3cr3t")
        try:
            with open(decrypted, "rb") as f:
                content = f.read()
            with open(temp_file, "rb") as f:
                original = f.read()
            assert content == original
        finally:
            os.remove(encrypted)
            if os.path.exists(decrypted):
                os.remove(decrypted)

    def test_output_default_quita_extension_enc(self, temp_file):
        """Default output removes .enc extension from encrypted path."""
        encrypted = FileEncryptor.encrypt_file(temp_file, "s3cr3t")
        decrypted = FileEncryptor.decrypt_file(encrypted, "s3cr3t")
        try:
            assert decrypted == temp_file  # original path without .enc
        finally:
            os.remove(encrypted)
            if os.path.exists(decrypted):
                os.remove(decrypted)

    def test_output_default_sin_enc_agrega_decrypted(self, temp_file):
        """File without .enc extension gets .decrypted suffix."""
        # First encrypt, then rename to remove .enc extension
        encrypted = FileEncryptor.encrypt_file(temp_file, "s3cr3t")
        renamed = temp_file + ".bin"
        os.rename(encrypted, renamed)
        try:
            output = FileEncryptor.decrypt_file(renamed, "s3cr3t")
            assert output == renamed + ".decrypted"
            assert os.path.exists(output)
        finally:
            for p in [encrypted, renamed, renamed + ".decrypted"]:
                if os.path.exists(p):
                    os.remove(p)

    def test_output_personalizado(self, temp_file):
        """Custom output_path for decryption is respected."""
        encrypted = FileEncryptor.encrypt_file(temp_file, "s3cr3t")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dec") as f:
            custom = f.name
        try:
            output = FileEncryptor.decrypt_file(encrypted, "s3cr3t", custom)
            assert output == custom
            assert os.path.exists(custom)
            with open(custom, "rb") as f:
                assert len(f.read()) > 0
        finally:
            os.remove(encrypted)
            if os.path.exists(custom):
                os.remove(custom)

    def test_password_incorrecta_lanza_error(self, temp_file):
        """Wrong password raises an exception during decrypt."""
        encrypted = FileEncryptor.encrypt_file(temp_file, "correct_pass")
        try:
            with pytest.raises(Exception):
                FileEncryptor.decrypt_file(encrypted, "wrong_pass")
        finally:
            os.remove(encrypted)

    def test_archivo_inexistente_lanza_error(self):
        """Non-existent encrypted file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="no encontrado"):
            FileEncryptor.decrypt_file("/ruta/inexistente.enc", "pass")

    def test_multiples_passwords(self, temp_file):
        """Multiple encrypt/decrypt cycles with different passwords work."""
        # Read original content to restore between iterations
        with open(temp_file, "rb") as f:
            original_content = f.read()

        passwords = ["pass1", "P@ssw0rd!", "una_clave_muy_larga_12345", "!@#$%"]
        for i, pwd in enumerate(passwords):
            # Use unique temp file per iteration to avoid overwrite issues
            iter_path = temp_file + f".iter{i}"
            with open(iter_path, "wb") as f:
                f.write(original_content)
            encrypted = None
            decrypted = None
            try:
                encrypted = FileEncryptor.encrypt_file(iter_path, pwd)
                decrypted = FileEncryptor.decrypt_file(encrypted, pwd)
                with open(decrypted, "rb") as f:
                    content = f.read()
                assert content == original_content
            finally:
                for p in [iter_path, iter_path + ".enc", decrypted, encrypted]:
                    if p and os.path.exists(p):
                        os.remove(p)


# ═══════════════════════════════════════════════════════════════════════════════
# SecureEnvManager.mask_sensitive_value
# ═══════════════════════════════════════════════════════════════════════════════


class TestMaskSensitiveValue:
    def test_valor_no_sensible_retorna_igual(self):
        """Non-sensitive key returns value unchanged."""
        result = SecureEnvManager.mask_sensitive_value("DB_HOST", "localhost")
        assert result == "localhost"

    def test_password_enmascarada(self):
        """Password values are masked."""
        result = SecureEnvManager.mask_sensitive_value("DB_PASSWORD", "my_secret_pass")
        # "my_secret_pass" = 14 chars → first 2 + 10 asterisks + last 2
        assert result == "my**********ss"

    def test_secret_enmascarado(self):
        """Secret values are masked."""
        result = SecureEnvManager.mask_sensitive_value("SECRET_KEY", "super_secreto_123")
        assert result == "su*************23"

    def test_token_enmascarado(self):
        """Token values are masked."""
        result = SecureEnvManager.mask_sensitive_value("API_TOKEN", "tok_abc12345")
        # "tok_abc12345" = 12 chars → first 2 + 8 asterisks + last 2
        assert result == "to********45"

    def test_valor_corto_menor_4_retorna_asteriscos(self):
        """Value shorter than 4 chars returns '****'."""
        result = SecureEnvManager.mask_sensitive_value("PASSWORD", "ab")
        assert result == "****"

    def test_valor_vacio_retorna_asteriscos(self):
        """Empty value returns '****'."""
        result = SecureEnvManager.mask_sensitive_value("PASSWORD", "")
        assert result == "****"

    def test_valor_none_retorna_asteriscos(self):
        """None value returns '****'."""
        result = SecureEnvManager.mask_sensitive_value("PASSWORD", None)
        assert result == "****"

    def test_valor_exactamente_4_caracteres(self):
        """Value with exactly 4 chars with sensitive key: first 2 + 0 asterisks + last 2."""
        result = SecureEnvManager.mask_sensitive_value("TOKEN", "abcd")
        assert result == "abcd"  # first 2 (ab) + 0 asterisks + last 2 (cd)

    def test_key_insensible_con_password_substring(self):
        """Key with 'password' substring is treated as sensitive even if not exact."""
        result = SecureEnvManager.mask_sensitive_value("MY_PASSWORD_KEY", "secret_value_123")
        assert "*" in result
        assert result != "secret_value_123"

    def test_case_insensitive_key(self):
        """Sensitive key matching is case-insensitive."""
        result = SecureEnvManager.mask_sensitive_value("DB_Password", "my_secret_pass")
        assert "*" in result

    def test_key_no_sensible_pasa_igual(self):
        """Non-sensitive key (like 'NAME', 'HOST', 'PORT') returns value as-is."""
        assert SecureEnvManager.mask_sensitive_value("APP_NAME", "MiApp") == "MiApp"
        assert SecureEnvManager.mask_sensitive_value("DB_PORT", "3306") == "3306"
        assert SecureEnvManager.mask_sensitive_value("DEBUG", "true") == "true"

    def test_key_con_pass_comienza(self):
        """Key starting with 'pass' is treated as sensitive."""
        result = SecureEnvManager.mask_sensitive_value("passcode", "value_123456")
        assert "*" in result


# ═══════════════════════════════════════════════════════════════════════════════
# SecureEnvManager.validate_env_security
# ═══════════════════════════════════════════════════════════════════════════════


class TestValidateEnvSecurity:
    def test_archivo_inexistente_retorna_issue(self):
        """Non-existent .env returns a single issue about file not found."""
        issues = SecureEnvManager.validate_env_security("/ruta/no/existe/.env")
        assert isinstance(issues, list)
        assert any("no encontrado" in i.lower() for i in issues)

    def test_detecta_password_vacia(self, temp_env_file):
        """Empty DB_PASSWORD is flagged."""
        issues = SecureEnvManager.validate_env_security(temp_env_file)
        assert any("vacía" in i.lower() or "empty" in i.lower() for i in issues)

    def test_detecta_password_corta(self, temp_env_file):
        """ADMIN_PASSWORD=123 is flagged as too short."""
        issues = SecureEnvManager.validate_env_security(temp_env_file)
        assert any("corta" in i.lower() for i in issues)

    def test_detecta_password_debil(self, temp_env_file):
        """Weak passwords like 'abc' or '123' are not flagged unless exact match."""
        issues = SecureEnvManager.validate_env_security(temp_env_file)
        # 'abc' is not in the weak passwords list, but it is short
        assert any("corta" in i.lower() for i in issues)

    def test_archivo_sin_problemas(self):
        """A clean .env with strong passwords produces no issues."""
        content = "DB_HOST=localhost\nDB_PASSWORD=StrongP@ss1\nAPI_KEY=abc123XYZ!secure\n"
        with tempfile.NamedTemporaryFile(delete=False, suffix=".env", mode="w") as f:
            f.write(content)
            clean_path = f.name
        try:
            issues = SecureEnvManager.validate_env_security(clean_path)
            # Should have no password-related issues
            password_issues = [i for i in issues if "password" in i.lower()]
            assert len(password_issues) == 0
        finally:
            if os.path.exists(clean_path):
                os.remove(clean_path)

    def test_ignora_comentarios_y_vacias(self, temp_env_file):
        """Comments and blank lines are ignored."""
        issues = SecureEnvManager.validate_env_security(temp_env_file)
        # DB_HOST=localhost should not be in issues
        host_issues = [i for i in issues if "DB_HOST" in i]
        assert len(host_issues) == 0

    def test_retorna_lista(self):
        """validate_env_security always returns a list."""
        issues = SecureEnvManager.validate_env_security("/nonexistent/.env")
        assert isinstance(issues, list)

    def test_sin_path_usa_default_base_dir(self):
        """Without path argument, uses BASE_DIR/.env (likely doesn't exist, returns issue)."""
        issues = SecureEnvManager.validate_env_security()
        assert isinstance(issues, list)
        assert len(issues) >= 1  # At least "no encontrado" issue

    def test_detecta_password_por_defecto(self):
        """Known weak passwords like 'admin' or 'root' are flagged."""
        content = "ADMIN_PASSWORD=admin\nROOT_PASSWORD=root\nDB_PASSWORD=123456\n"
        with tempfile.NamedTemporaryFile(delete=False, suffix=".env", mode="w") as f:
            f.write(content)
            weak_path = f.name
        try:
            issues = SecureEnvManager.validate_env_security(weak_path)
            weak_issues = [i for i in issues if "débil" in i.lower() or "defecto" in i.lower()]
            assert len(weak_issues) >= 1
        finally:
            if os.path.exists(weak_path):
                os.remove(weak_path)


# ═══════════════════════════════════════════════════════════════════════════════
# SecureEnvManager.secure_delete_file
# ═══════════════════════════════════════════════════════════════════════════════


class TestSecureDeleteFile:
    def test_elimina_archivo_retorna_true(self):
        """secure_delete_file returns True and removes the file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"datos sensibles")
            path = f.name
        assert os.path.exists(path)
        result = SecureEnvManager.secure_delete_file(path)
        assert result is True
        assert not os.path.exists(path)

    def test_archivo_inexistente_retorna_false(self):
        """Non-existent file returns False."""
        result = SecureEnvManager.secure_delete_file("/ruta/inexistente.txt")
        assert result is False

    def test_passes_personalizado(self):
        """Custom number of passes works."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"datos")
            path = f.name
        try:
            result = SecureEnvManager.secure_delete_file(path, passes=5)
            assert result is True
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_archivo_vacio(self):
        """Empty file can be securely deleted."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name
        assert os.path.exists(path)
        result = SecureEnvManager.secure_delete_file(path)
        assert result is True
        assert not os.path.exists(path)

    def test_exception_logeada_retorna_false(self, monkeypatch):
        """When os.remove raises, function logs error and returns False."""
        real_remove = os.remove

        def broken_remove(path):
            raise PermissionError("Access denied")

        monkeypatch.setattr("os.remove", broken_remove)

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"datos")
            path = f.name
        try:
            result = SecureEnvManager.secure_delete_file(path)
            assert result is False
            # File should still exist since remove failed
            assert os.path.exists(path)
        finally:
            # Restore real os.remove for cleanup
            monkeypatch.setattr("os.remove", real_remove, raising=False)
            if os.path.exists(path):
                os.remove(path)


# ═══════════════════════════════════════════════════════════════════════════════
# CredentialManager.store
# ═══════════════════════════════════════════════════════════════════════════════


class TestCredentialManagerStore:
    def test_almacena_credenciales(self):
        """store() saves credentials without error."""
        CredentialManager.store("api_service", "user1", "pass123")
        assert "api_service" in CredentialManager._credentials

    def test_password_almacenada_encriptada(self):
        """Password is stored encrypted, not in plain text."""
        CredentialManager.store("test_svc", "admin", "my_secret_password")
        stored = CredentialManager._credentials["test_svc"]
        assert stored["password"] != "my_secret_password"
        assert stored.get("_encrypted") is True

    def test_store_no_retorna_nada(self):
        """store() returns None."""
        result = CredentialManager.store("svc", "u", "p")
        assert result is None

    def test_sobreescribe_servicio_existente(self):
        """store() overwrites existing service credentials."""
        CredentialManager.store("svc", "old_user", "old_pass")
        CredentialManager.store("svc", "new_user", "new_pass")
        creds = CredentialManager.get("svc")
        assert creds["username"] == "new_user"
        assert creds["password"] == "new_pass"

    def test_password_vacia(self):
        """Empty password is stored (encrypted form)."""
        CredentialManager.store("svc", "user", "")
        stored = CredentialManager._credentials["svc"]
        assert stored["_encrypted"] is True
        assert stored["password"] != ""


# ═══════════════════════════════════════════════════════════════════════════════
# CredentialManager.get
# ═══════════════════════════════════════════════════════════════════════════════


class TestCredentialManagerGet:
    def test_obtiene_credenciales_desencriptadas(self):
        """get() returns decrypted credentials."""
        CredentialManager.store("api", "my_user", "my_pass_123")
        creds = CredentialManager.get("api")
        assert creds["username"] == "my_user"
        assert creds["password"] == "my_pass_123"

    def test_servicio_inexistente_retorna_none(self):
        """get() returns None for unknown service."""
        result = CredentialManager.get("nonexistent_service")
        assert result is None

    def test_multiples_servicios_aislados(self):
        """Multiple services can be stored and retrieved independently."""
        CredentialManager.store("svc_a", "user_a", "pass_a")
        CredentialManager.store("svc_b", "user_b", "pass_b")
        creds_a = CredentialManager.get("svc_a")
        creds_b = CredentialManager.get("svc_b")
        assert creds_a["username"] == "user_a" and creds_a["password"] == "pass_a"
        assert creds_b["username"] == "user_b" and creds_b["password"] == "pass_b"

    def test_ciclo_completo_store_get(self):
        """Full store -> get cycle works for multiple entries."""
        services = {
            "email": ("email_user", "email_pass"),
            "db": ("db_user", "db_pass_secure!"),
            "api": ("api_user", "api_token_xyz"),
        }
        for svc, (user, pwd) in services.items():
            CredentialManager.store(svc, user, pwd)
        for svc, (user, pwd) in services.items():
            creds = CredentialManager.get(svc)
            assert creds["username"] == user
            assert creds["password"] == pwd

    def test_password_con_caracteres_especiales(self):
        """Passwords with special chars survive encrypt/decrypt."""
        special = "P@ssw0rd!$%&/()=?#´`+*~_-.:,;"
        CredentialManager.store("svc", "user", special)
        creds = CredentialManager.get("svc")
        assert creds["password"] == special


# ═══════════════════════════════════════════════════════════════════════════════
# CredentialManager.clear
# ═══════════════════════════════════════════════════════════════════════════════


class TestCredentialManagerClear:
    def test_clear_servicio_especifico(self):
        """clear(service) removes only that service."""
        CredentialManager.store("svc_a", "u1", "p1")
        CredentialManager.store("svc_b", "u2", "p2")
        CredentialManager.clear("svc_a")
        assert CredentialManager.get("svc_a") is None
        assert CredentialManager.get("svc_b") is not None

    def test_clear_todos(self):
        """clear() without args removes all services."""
        CredentialManager.store("svc_a", "u1", "p1")
        CredentialManager.store("svc_b", "u2", "p2")
        CredentialManager.clear()
        assert CredentialManager.get("svc_a") is None
        assert CredentialManager.get("svc_b") is None
        assert CredentialManager.list_services() == []

    def test_clear_servicio_inexistente_no_falla(self):
        """clear() with unknown service doesn't raise."""
        CredentialManager.clear("nonexistent_svc")

    def test_clear_y_restore(self):
        """After clear, new credentials can be stored."""
        CredentialManager.store("svc", "user", "pass")
        CredentialManager.clear("svc")
        CredentialManager.store("svc", "new_user", "new_pass")
        creds = CredentialManager.get("svc")
        assert creds["username"] == "new_user"


# ═══════════════════════════════════════════════════════════════════════════════
# CredentialManager.list_services
# ═══════════════════════════════════════════════════════════════════════════════


class TestCredentialManagerListServices:
    def test_lista_vacia_inicialmente(self):
        """list_services() returns empty list with no stored services."""
        assert CredentialManager.list_services() == []

    def test_lista_despues_de_almacenar(self):
        """list_services() includes stored services."""
        CredentialManager.store("svc_a", "u1", "p1")
        CredentialManager.store("svc_b", "u2", "p2")
        services = CredentialManager.list_services()
        assert "svc_a" in services
        assert "svc_b" in services

    def test_lista_despues_de_clear_parcial(self):
        """list_services() reflects partial clear."""
        CredentialManager.store("svc_a", "u1", "p1")
        CredentialManager.store("svc_b", "u2", "p2")
        CredentialManager.clear("svc_a")
        services = CredentialManager.list_services()
        assert "svc_a" not in services
        assert "svc_b" in services

    def test_lista_retorna_copia_no_referencia(self):
        """list_services() returns a copy, not a reference to internal dict."""
        CredentialManager.store("svc", "u", "p")
        services = CredentialManager.list_services()
        services.append("fake")
        actual = CredentialManager.list_services()
        assert "fake" not in actual


# ═══════════════════════════════════════════════════════════════════════════════
# CredentialManager.get — decrypt failure and non-encrypted paths
# ═══════════════════════════════════════════════════════════════════════════════


class TestCredentialManagerGetEdgeCases:
    """Edge cases in CredentialManager.get(): decrypt failure and raw cred paths."""

    def test_decrypt_fallido_retorna_none(self):
        """When decrypt raises, get() returns None (except handler, lines 238-239)."""
        # Store a credential with the current Fernet key
        CredentialManager.store("svc", "user", "pass123")

        # Corrupt the internal Fernet key so decrypt fails
        from cryptography.fernet import Fernet

        original_fernet = CredentialManager._fernet
        wrong_key = Fernet.generate_key()  # Generate a different key
        CredentialManager._fernet = Fernet(wrong_key)

        try:
            result = CredentialManager.get("svc")
            assert result is None
        finally:
            # Restore original fernet to avoid bleeding into other tests
            CredentialManager._fernet = original_fernet

    def test_credencial_no_encriptada_retorna_directa(self):
        """When _encrypted is falsy, get() returns raw dict (line 240)."""
        # Directly inject a non-encrypted credential (simulating legacy format)
        CredentialManager._credentials["legacy_svc"] = {
            "username": "legacy_user",
            "password": "plain_text_pass",
            "_encrypted": False,
        }
        creds = CredentialManager.get("legacy_svc")
        assert creds is not None
        assert creds["username"] == "legacy_user"
        assert creds["password"] == "plain_text_pass"

    def test_credencial_sin_flag_encriptado_retorna_directa(self):
        """When _encrypted key is missing, get() returns raw dict (falls through to return cred)."""
        CredentialManager._credentials["old_svc"] = {
            "username": "old_user",
            "password": "old_pass",
            # No '_encrypted' key
        }
        creds = CredentialManager.get("old_svc")
        assert creds is not None
        assert creds["username"] == "old_user"
        assert creds["password"] == "old_pass"
