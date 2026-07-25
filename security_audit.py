"""
security_audit.py - Auditoria de seguridad del proyecto

Este script verifica el estado de seguridad del proyecto y genera un reporte.
Ejecutar periodicamente para validar que las medidas de seguridad estan activas.
"""
import sys
from pathlib import Path
from datetime import datetime


class SecurityAuditor:
    """Audita la seguridad del proyecto Dinamo Rent ERP."""

    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent
        self.issues = []
        self.warnings = []
        self.passed = []

    def audit_all(self) -> dict:
        """Ejecuta todas las auditorias y retorna resultados."""
        print("=" * 70)
        print("AUDITORIA DE SEGURIDAD - DINAMO RENT ERP")
        print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        print()

        self._check_env_file()
        self._check_gitignore()
        self._check_password_security()
        self._check_file_permissions()
        self._check_dependencies()
        self._check_backup_security()
        self._check_logging_security()

        return self._generate_report()

    def _check_env_file(self):
        """Verifica la seguridad del archivo .env."""
        print("[CHECK] Verificando archivo .env...")
        env_path = self.base_dir / ".env"

        if not env_path.exists():
            self.issues.append("Archivo .env no encontrado")
            print("  [FAIL] No existe .env")
            return

        # Verificar que .env este en gitignore
        gitignore_path = self.base_dir / ".gitignore"
        if gitignore_path.exists():
            with open(gitignore_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
                if ".env" not in content:
                    self.issues.append(".env no esta en gitignore")
                    print("  [FAIL] .env no esta en gitignore")
                else:
                    self.passed.append(".env esta en gitignore")
                    print("  [PASS] .env esta en gitignore")
        else:
            self.warnings.append(".env podria no estar correctamente ignorado")
            print("  [WARN] Verificar que .env este ignorado (no se encontro .gitignore)")

        # Verificar contrasenas vacias
        with open(env_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    if "password" in key.lower() and not value:
                        self.warnings.append(f"Contrasena vacia en .env: {key}")
                        print(f"  [WARN] {key} esta vacia")

        print()

    def _check_gitignore(self):
        """Verifica que archivos sensibles esten ignorados."""
        print("[CHECK] Verificando gitignore...")
        gitignore_path = self.base_dir / ".gitignore"
        if not gitignore_path.exists():
            gitignore_path = self.base_dir / "gitignore"

        if gitignore_path.exists():
            with open(gitignore_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            required_patterns = [
                ".env",
                "Backups/",
                "logs/",
                "*.db",
                "__pycache__",
                ".idea",
            ]

            for pattern in required_patterns:
                if pattern in content:
                    self.passed.append(f"gitignore contiene: {pattern}")
                    print(f"  [PASS] {pattern}")
                else:
                    self.warnings.append(f"gitignore podria necesitar: {pattern}")
                    print(f"  [WARN] Falta {pattern}")
        else:
            self.issues.append("No se encontro archivo gitignore")
            print("  [FAIL] No existe gitignore")

        print()

    def _check_password_security(self):
        """Verifica la seguridad de contrasenas."""
        print("[CHECK] Verificando seguridad de contrasenas...")

        # Verificar que security.py tenga validacion
        security_path = self.base_dir / "core" / "security.py"
        if security_path.exists():
            with open(security_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            if "validate_password_strength" in content:
                self.passed.append("Validacion de fortaleza de contrasena implementada")
                print("  [PASS] Validacion de contrasena presente")
            else:
                self.issues.append("No hay validacion de fortaleza de contrasena")
                print("  [FAIL] Falta validacion de contrasena")

            if "LoginAttemptTracker" in content:
                self.passed.append("Rate limiting de login implementado")
                print("  [PASS] Rate limiting presente")
            else:
                self.issues.append("No hay rate limiting para login")
                print("  [FAIL] Falta rate limiting")
        else:
            self.issues.append("core/security.py no encontrado")
            print("  [FAIL] security.py no encontrado")

        print()

    def _check_file_permissions(self):
        """Verifica permisos de archivos sensibles (Windows-friendly)."""
        print("[CHECK] Verificando archivos sensibles...")

        sensitive_files = [
            self.base_dir / ".env",
            self.base_dir / "core" / "database_sa.py",
        ]

        for file_path in sensitive_files:
            if file_path.exists():
                # En Windows, verificar si es accesible
                try:
                    with open(
                        file_path, "r", encoding="utf-8", errors="replace"
                    ) as f:
                        f.read(1)
                    self.passed.append(f"Archivo accesible: {file_path.name}")
                    print(f"  [PASS] {file_path.name}")
                except PermissionError:
                    self.passed.append(f"Archivo protegido: {file_path.name}")
                    print(f"  [PASS] {file_path.name} (protegido)")

        print()

    def _check_dependencies(self):
        """Verifica que las dependencias de seguridad esten instaladas."""
        print("[CHECK] Verificando dependencias de seguridad...")

        try:
            import cryptography

            self.passed.append(
                f"cryptography instalado: v{cryptography.__version__}"
            )
            print(f"  [PASS] cryptography v{cryptography.__version__}")
        except ImportError:
            self.issues.append("cryptography no instalado")
            print("  [FAIL] cryptography no instalado (pip install cryptography)")

        try:
            import bcrypt

            self.passed.append("bcrypt instalado (alternativa a PBKDF2)")
            print("  [PASS] bcrypt disponible")
        except ImportError:
            self.warnings.append("bcrypt no instalado (PBKDF2 es OK)")
            print("  [INFO] bcrypt no instalado (PBKDF2 es suficiente)")

        print()

    def _check_backup_security(self):
        """Verifica seguridad de backups."""
        print("[CHECK] Verificando backups...")

        backup_path = self.base_dir / "Backups"
        if backup_path.exists():
            backups = list(backup_path.glob("*"))
            if len(backups) > 0:
                self.passed.append(f"Existen backups: {len(backups)} archivos")
                print(f"  [PASS] {len(backups)} backups encontrados")

                # Verificar si hay backups encriptados
                encrypted = list(backup_path.glob("*.enc"))
                if encrypted:
                    self.passed.append(
                        f"Backups encriptados: {len(encrypted)}"
                    )
                    print(f"  [PASS] {len(encrypted)} backups encriptados")
                else:
                    self.warnings.append("No hay backups encriptados")
                    print("  [INFO] Ningun backup encriptado (opcional)")
            else:
                self.warnings.append("No hay backups en el directorio")
                print("  [INFO] No hay backups (recomendado crear)")
        else:
            self.warnings.append("Directorio Backups no encontrado")
            print("  [WARN] Directorio Backups no existe")

        print()

    def _check_logging_security(self):
        """Verifica configuracion de logging."""
        print("[CHECK] Verificando logging de seguridad...")

        logger_path = self.base_dir / "core" / "logger.py"
        if logger_path.exists():
            with open(
                logger_path, "r", encoding="utf-8", errors="replace"
            ) as f:
                content = f.read()

            if "audit" in content.lower():
                self.passed.append("Audit logging configurado")
                print("  [PASS] Audit logging presente")
            else:
                self.warnings.append("No se encontro audit logging")
                print("  [WARN] Podria faltar audit logging")
        else:
            self.issues.append("logger.py no encontrado")
            print("  [FAIL] logger.py no encontrado")

        # Verificar que existan logs
        logs_path = self.base_dir / "logs"
        if logs_path.exists():
            self.passed.append("Directorio logs existe")
            print("  [PASS] Directorio logs presente")

        print()

    def _generate_report(self) -> dict:
        """Genera reporte final."""
        print("=" * 70)
        print("RESUMEN DE AUDITORIA")
        print("=" * 70)
        print(f"[PASS]  PASSED:   {len(self.passed)}")
        print(f"[WARN]  WARNINGS: {len(self.warnings)}")
        print(f"[FAIL]  FAIL:     {len(self.issues)}")
        print()

        if self.issues:
            print("[CRIT] PROBLEMAS CRITICOS:")
            for issue in self.issues:
                print(f"  [FAIL] {issue}")
            print()

        if self.warnings:
            print("[WARN] ADVERTENCIAS:")
            for warning in self.warnings:
                print(f"  [WARN] {warning}")
            print()

        if not self.issues:
            print("[OK] No se encontraron problemas criticos!")
        else:
            print(
                "[WARN] Se recomienda resolver los problemas criticos lo antes posible."
            )

        print("=" * 70)

        return {
            "passed": len(self.passed),
            "warnings": len(self.warnings),
            "issues": len(self.issues),
            "passed_items": self.passed,
            "warning_items": self.warnings,
            "issue_items": self.issues,
            "timestamp": datetime.now().isoformat(),
        }


if __name__ == "__main__":
    auditor = SecurityAuditor()
    results = auditor.audit_all()

    # Exit code based on issues
    sys.exit(1 if results["issues"] > 0 else 0)
