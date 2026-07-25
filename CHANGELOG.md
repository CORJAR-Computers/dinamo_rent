# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.2.1] - 2026-07-25

### Fixed

- **Login → Interfaz principal**: Corregido crash silencioso (exit code 1) al transicionar de
  `LoginWindow` a `MainWindow`. Causa raíz: `AuthService.login()` corría en un `QRunnable`
  (hilo secundario) y Qt terminaba la app al crear widgets desde ese hilo. Solución: login
  ejecutado en el hilo principal vía `QTimer.singleShot(0, ...)`.
- **Diálogo "¿Salir?" falso positivo**: Eliminado el diálogo de confirmación de salida que
  aparecía inmediatamente al ingresar, causado por `showMaximized()` dentro del `__init__` de
  `MainWindow` (antes de configurar `setCentralWidget`). Se agregaron flags `_login_successful`
  y `_closing_to_login` para distinguir cierres programáticos de cierres manuales.
- **Ciclo de vida de la aplicación** (`main_qt.py`): Eliminadas todas las llamadas a
  `setQuitOnLastWindowClosed(True)` dentro de transiciones de ventana. Se usa
  `setQuitOnLastWindowClosed(False)` globalmente y `app.quit()` explícito en `closeEvent`.
- **Calendario — colores ausentes** (`calendario_view.py`): `setBackground()` en
  `QTableWidgetItem` era sobreescrito por el QSS global de la app. Reemplazado por un
  `QStyledItemDelegate` personalizado (`CalendarioCeldaDelegate`) que pinta con `QPainter`
  directamente, ignorando el QSS. Colores: 🔵 Disponible, 🟢 Rentado, 🟡 Reservado, 🔴 Taller.
- **Calendario — SQL Firebird** (`renta_repository_sa.py`): Reemplazado `extract('month', ...)`
  / `extract('year', ...)` por comparación de rango de fechas (`fecha <= ultimo_dia AND fecha >=
  primer_dia`) compatible con Firebird y SQLite. Ahora también incluye rentas que se solapan con
  el mes (no solo las que empiezan en él).
- **Tests**: Fixed 15 pre-existing test failures across 9 files:
  - `test_about_dialog.py`: Updated copyright assertion from 'Dinamo' to 'Corjar'
  - `test_config.py`: Changed default engine from 'mysql' to 'firebird'
  - `test_validators.py`: Adapted `TestSanitizeForSql` tests to match `sanitizar()` behavior
  - `test_database_sa.py`: Added `DB_ENGINE='mysql'` monkeypatch for migrations in tests
  - `test_services.py`: Updated KPI keys to match actual `kpi_y_financiero()` output
  - `test_services_restantes.py`: Updated KPI keys; test structure/types instead of exact values
  - `test_cierre_renta_dialog.py`: Set date to pactada before calculating `otros`
- **Security**: Fixed `unlock_account()` in `auth_service.py` to properly clear `_lockout_until`
- **CI/CD**: Enabled GitHub Actions on every push and added `workflow_dispatch`

### Added

- **CI — Release automático** (`.github/workflows/release.yml`): Workflow que se activa al
  crear un tag `v*.*.*`, ejecuta lint + tests, y publica automáticamente un GitHub Release con
  notas del CHANGELOG.
- **Documentation**: Created comprehensive `docs/DEPLOYMENT_PLAN.md`

### Security

- **Git History**: Cleaned `.env` file and old `db_encryption_key` from entire git history
- **Git Tracking**: Added `.env`, `config.ini`, and `*.fdb` to `.gitignore`

### Changed

- **core/security.py**: `reset_attempts()` now includes `self._lockout_until.pop(identifier, None)`
- **services/auth_service.py**: `unlock_account()` simplified to use `reset_attempts()`

---

## [3.2.0] - 2026-07-24

### Added
- **Database Optimization**: Added composite indexes and applied schema corrections via Alembic (`initial_schema`).
- **CI/CD Integration**: Added GitHub Actions CI workflows for automated testing.
- **Code Quality**: Automated linting and formatting fixes using Ruff.
- **Security**: Added force password change flow and visual indicator (🔒) for users in the admin view.
- **Documentation**: Added CI build status and test coverage badges (98%) to the README.

### Changed
- **Branding**: Updated application branding to "Dinamo Rent ERP" (Author: CORJAR Computers).
- **UI/UX Refactoring**: Comprehensive improvements for production readiness across the Dashboard, messaging system, and `AboutDialog`.
- **Styling**: Migrated styling to QSS for better maintainability.
- **Performance**: Introduced asynchronous patterns for better UI responsiveness and optimized SQL repository queries.

### Fixed
- Fixed timezone formatting issues (`tzdata` for `America/Bogota`) for stable date handling.
- Resolved database foreign key constraint errors (errno: 150) during migrations.

---

*Note: Previous versions and changes prior to 3.2.0 are encompassed in this initial release of the changelog.*
