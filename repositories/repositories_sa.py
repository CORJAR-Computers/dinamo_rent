"""
repositories_sa.py — Re-exportación de todos los repositorios

F1C: Este archivo pasó de contener ~631 líneas con toda la lógica
a ser un thin wrapper que importa desde los módulos individuales.

MOTIVO: Los servicios existentes importan desde este archivo:
    from repositories.repositories_sa import AutoRepositorySA

Este archivo mantiene compatibilidad total con el código existente.

NUEVO uso recomendado (directo al módulo):
    from repositories.auto_repository_sa import AutoRepositorySA

Uso compatible (heredado):
    from repositories.repositories_sa import AutoRepositorySA
"""

from repositories.auto_repository_sa import AutoRepositorySA
from repositories.cliente_repository_sa import ClienteRepositorySA
from repositories.renta_repository_sa import RentaRepositorySA
from repositories.usuario_repository_sa import UsuarioRepositorySA
from repositories.reserva_repository_sa import ReservaRepositorySA
from repositories.mantenimiento_repository_sa import MantenimientoRepositorySA
from repositories.comparendo_repository_sa import ComparendoRepositorySA
from repositories.pago_repository_sa import PagoRepositorySA
from repositories.gasto_repository_sa import GastoRepositorySA
from repositories.inspeccion_repository_sa import InspeccionRepositorySA
from repositories.alerta_repository_sa import AlertaRepositorySA
from repositories.informe_repository_sa import InformeRepositorySA

__all__ = [
    "AutoRepositorySA",
    "ClienteRepositorySA",
    "RentaRepositorySA",
    "UsuarioRepositorySA",
    "ReservaRepositorySA",
    "MantenimientoRepositorySA",
    "ComparendoRepositorySA",
    "PagoRepositorySA",
    "GastoRepositorySA",
    "InspeccionRepositorySA",
    "AlertaRepositorySA",
    "InformeRepositorySA",
]
