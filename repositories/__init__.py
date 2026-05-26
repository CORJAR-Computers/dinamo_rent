"""
repositories — Capa de Acceso a Datos (SQLAlchemy)

F1C: Reestructuración del módulo de repositorios.

Antes: Todo en un solo archivo repositories_sa.py (631 líneas).
Ahora: Cada repositorio en su propio archivo, con re-exportación
       desde repositories_sa.py para compatibilidad con servicios.

Estructura:
    repositories/
    ├── __init__.py                    ← Este archivo
    ├── base_repository_sa.py          ← Clase base compartida
    ├── auto_repository_sa.py          ← Vehículos
    ├── cliente_repository_sa.py       ← Clientes
    ├── renta_repository_sa.py         ← Rentas
    ├── usuario_repository_sa.py       ← Usuarios
    ├── reserva_repository_sa.py       ← Reservas
    ├── mantenimiento_repository_sa.py ← Mantenimiento
    ├── comparendo_repository_sa.py    ← Comparendos
    ├── pago_repository_sa.py          ← Pagos
    ├── gasto_repository_sa.py         ← Gastos / Caja menor
    ├── inspeccion_repository_sa.py    ← Inspecciones
    ├── alerta_repository_sa.py        ← Alertas
    ├── informe_repository_sa.py       ← Informes gerenciales
    └── repositories_sa.py             ← Re-exporta todo (compatibilidad)

Uso recomendado:
    from repositories.auto_repository_sa import AutoRepositorySA

Uso compatible (heredado):
    from repositories.repositories_sa import AutoRepositorySA
"""

from repositories.base_repository_sa import BaseRepositorySA
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
    "BaseRepositorySA",
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
