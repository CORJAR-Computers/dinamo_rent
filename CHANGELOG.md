# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
