"""
logger.py — Sistema de logs centralizado para Dinamo Rent ERP

Uso:
    from core.logger import get_logger
    log = get_logger(__name__)
    log.info("Renta creada con id=42")
    log.warning("SOAT vencido para placa ABC123")
    log.error("Error al conectar a la BD", exc_info=True)
"""
import logging
import logging.handlers

from core.config import LOGS_DIR, APP_NAME

# ─── Formato ──────────────────────────────────────────────────────────────────
_FMT_DETALLE = (
    "%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s"
)
_FMT_CONSOLA = "%(levelname)-8s | %(name)s | %(message)s"
_DATE_FMT    = "%Y-%m-%d %H:%M:%S"

# ─── Singleton de configuración ───────────────────────────────────────────────
_configured = False


def _setup_root_logger() -> None:
    global _configured
    if _configured:
        return
    _configured = True

    root = logging.getLogger(APP_NAME)
    root.setLevel(logging.DEBUG)

    # — Archivo principal: rotativo por tamaño (5 MB × 5 archivos) —
    log_file = LOGS_DIR / "dinamo_rent.log"
    fh = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(_FMT_DETALLE, datefmt=_DATE_FMT))
    root.addHandler(fh)

    # — Archivo de errores: solo WARNING+ —
    err_file = LOGS_DIR / "errores.log"
    eh = logging.handlers.RotatingFileHandler(
        err_file,
        maxBytes=2 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    eh.setLevel(logging.WARNING)
    eh.setFormatter(logging.Formatter(_FMT_DETALLE, datefmt=_DATE_FMT))
    root.addHandler(eh)

    # — Consola: solo INFO+ durante desarrollo —
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(_FMT_CONSOLA))
    root.addHandler(ch)


def get_logger(name: str) -> logging.Logger:
    """
    Retorna un logger hijo del logger raíz de la aplicación.

    Ejemplo:
        log = get_logger(__name__)
        log.info("Todo bien")
    """
    _setup_root_logger()
    # Anteponer el nombre de la app para jerarquía clara en los logs
    return logging.getLogger(f"{APP_NAME}.{name}")


# ─── Logger de auditoría (acciones de usuario) ───────────────────────────────
def get_audit_logger() -> logging.Logger:
    """
    Logger especial para acciones de usuario (login, CRUD crítico).
    Escribe en audit.log con rotación diaria.
    """
    _setup_root_logger()
    audit_name = f"{APP_NAME}.audit"
    audit = logging.getLogger(audit_name)

    if not audit.handlers:
        audit_file = LOGS_DIR / "audit.log"
        ah = logging.handlers.TimedRotatingFileHandler(
            audit_file,
            when="midnight",
            backupCount=30,
            encoding="utf-8",
        )
        ah.setLevel(logging.INFO)
        ah.setFormatter(
            logging.Formatter(
                "%(asctime)s | AUDIT | %(message)s",
                datefmt=_DATE_FMT,
            )
        )
        audit.addHandler(ah)
        audit.propagate = False  # No duplicar en el root

    return audit
