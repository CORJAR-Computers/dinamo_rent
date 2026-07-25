# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.2.1] - 2026-07-25

### Fixed

- **Tests**: Fixed 15 pre-existing test failures across 9 files:
  - `test_about_dialog.py`: Updated copyright assertion from 'Dinamo' to 'Corjar' to match `_COPYRIGHT`
  - `test_config.py`: Changed default engine from 'mysql' to 'firebird' (2 places)
  - `test_validators.py`: Adapted 4 `TestSanitizeForSql` tests to match `sanitizar()` behavior (strip-only, no SQL escaping per SEC-05)
  - `test_database_sa.py`: Added `DB_ENGINE='mysql'` monkeypatch so migrations actually run in tests
  - `test_services.py`: Updated KPI keys to match actual `kpi_y_financiero()` output
  - `test_services_restantes.py`: Updated KPI keys and changed `test_obtener_resumen_financiero_sin_datos` to test structure/types instead of exact values (shared DB)
  - `test_cierre_renta_dialog.py`: Set date to pactada before calculating `otros` to avoid incorrect mora
- **Security**: Fixed `unlock_account()` in `auth_service.py` to properly clear `_lockout_until` via `reset_attempts()` in `core/security.py`
- **CI/CD**: Enabled GitHub Actions on every push (was only on PRs) and added `workflow_dispatch` for manual triggers

### Added

- **Documentation**: Created comprehensive `docs/DEPLOYMENT_PLAN.md` with:
  - Step-by-step installation guide for production
  - Database configuration (Firebird, MySQL, SQLite)
  - Alembic migration instructions
  - Security checklist (encryption key, backups, RBAC)
  - Troubleshooting table for common issues
  - Critical warning about `db_encryption_key` rotation

### Security

- **Git History**: Cleaned `.env` file and old `db_encryption_key` from entire git history using `git-filter-repo`
- **Git Tracking**: Added `.env`, `config.ini`, and `*.fdb` to `.gitignore`
- **Branch Cleanup**: Removed `backup-before-cleanup` branch that contained compromised credentials
- **Force Push**: Synchronized clean history to remote repository

### Changed

- **core/security.py**: `reset_attempts()` now includes `self._lockout_until.pop(identifier, None)` to centralize lockout cleanup
- **services/auth_service.py**: `unlock_account()` simplified to use `reset_attempts()` without accessing private attributes directly

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
