"""
repositories_sa.py — All SQLAlchemy Repositories

This module provides all repository classes with SQLAlchemy 2.0 ORM.
Replaces all old *_repository.py files.

F1A Changes applied:
  - ReservaRepositorySA: _to_dict incluye updated_at
  - ComparendoRepositorySA: _to_dict incluye updated_at y relationships
  - PagoRepositorySA: _to_dict incluye updated_at
  - GastoRepositorySA: _to_dict incluye placa y updated_at, insertar incluye placa
  - MantenimientoRepositorySA: _to_dict incluye updated_at
  - InspeccionRepositorySA: sin cambios (no tiene updated_at en modelo)

Usage:
    from repositories.repositories_sa import (
        AutoRepositorySA,
        ClienteRepositorySA,
        RentaRepositorySA,
        ReservaRepositorySA,
        MantenimientoRepositorySA,
        ComparendoRepositorySA,
        PagoRepositorySA,
        GastoRepositorySA,
        InspeccionRepositorySA,
        AlertaRepositorySA,
        InformeRepositorySA,
    )
"""

# Import all repositories
from repositories.auto_repository_sa import AutoRepositorySA
from repositories.cliente_repository_sa import ClienteRepositorySA
from repositories.renta_repository_sa import RentaRepositorySA
from repositories.usuario_repository_sa import UsuarioRepositorySA

# These will be created now
from typing import List, Dict, Optional
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_

from core.database_sa import get_session
from core.models import Reserva, MantenimientoVehiculo, Comparendo, Pago, Gasto, Inspeccion
from core.schemas import (
    ReservaCreate,
    MantenimientoCreate,
    ComparendoCreate,
    ComparendoUpdate,
    PagoCreate,
    GastoCreate,
    InspeccionCreate,
)
from core.exceptions import RegistroNoEncontrado
from core.logger import get_logger

log = get_logger(__name__)


class ReservaRepositorySA:

    @staticmethod
    def obtener_todas() -> List[Dict]:
        with get_session() as session:
            reservas = session.query(Reserva).order_by(Reserva.fecha_recogida).all()
            return [ReservaRepositorySA._to_dict(r) for r in reservas]

    @staticmethod
    def insertar(datos: ReservaCreate) -> int:
        with get_session() as session:
            nueva_reserva = Reserva(
                id_cliente=datos.id_cliente,
                nombre_cliente=datos.nombre_cliente,
                nacionalidad=datos.nacionalidad,
                categoria_vehiculo=datos.categoria_vehiculo,
                placa_asignada=datos.placa_asignada.upper() if datos.placa_asignada else None,
                fecha_recogida=datos.fecha_recogida,
                hora_recogida=datos.hora_recogida,
                ubicacion_recogida=datos.ubicacion_recogida,
                fecha_retorno=datos.fecha_retorno,
                hora_retorno=datos.hora_retorno,
                ubicacion_retorno=datos.ubicacion_retorno,
                dias_calculados=datos.dias_calculados,
                horas_extras=datos.horas_extras,
                valor_dia=datos.valor_dia,
                valor_hora_adic=datos.valor_hora_adic,
                abono=datos.abono,
                total=datos.total,
                observaciones=datos.observaciones,
                estado=datos.estado,
            )

            session.add(nueva_reserva)
            session.flush()
            log.info("Reserva creada: id=%s, cliente=%s", nueva_reserva.id, datos.nombre_cliente)
            return nueva_reserva.id

    @staticmethod
    def cancelar(id_reserva: int) -> None:
        with get_session() as session:
            reserva = session.query(Reserva).filter(Reserva.id == id_reserva).first()

            if not reserva:
                raise RegistroNoEncontrado(f"Reserva #{id_reserva} no encontrada.")

            reserva.estado = 'Cancelada'
            log.info("Reserva #%s cancelada", id_reserva)

    @staticmethod
    def obtener_contacto_cliente(id_reserva: int) -> Dict:
        with get_session() as session:
            reserva = session.query(Reserva).filter(Reserva.id == id_reserva).first()

            if not reserva:
                raise RegistroNoEncontrado(f"Reserva #{id_reserva} no encontrada.")

            return {
                'nombre_cliente': reserva.nombre_cliente,
                'nacionalidad': reserva.nacionalidad,
            }

    @staticmethod
    def obtener_por_id(id_reserva: int) -> Dict:
        with get_session() as session:
            reserva = session.query(Reserva).filter(Reserva.id == id_reserva).first()

            if not reserva:
                raise RegistroNoEncontrado(f"Reserva #{id_reserva} no encontrada.")

            return ReservaRepositorySA._to_dict(reserva)

    @staticmethod
    def _to_dict(reserva: Reserva) -> Dict:
        return {
            'id': reserva.id,
            'id_cliente': reserva.id_cliente,
            'nombre_cliente': reserva.nombre_cliente,
            'nacionalidad': reserva.nacionalidad,
            'categoria_vehiculo': reserva.categoria_vehiculo,
            'placa_asignada': reserva.placa_asignada,
            'fecha_recogida': reserva.fecha_recogida,
            'hora_recogida': reserva.hora_recogida,
            'ubicacion_recogida': reserva.ubicacion_recogida,
            'fecha_retorno': reserva.fecha_retorno,
            'hora_retorno': reserva.hora_retorno,
            'ubicacion_retorno': reserva.ubicacion_retorno,
            'dias_calculados': reserva.dias_calculados,
            'horas_extras': reserva.horas_extras,
            'valor_dia': float(reserva.valor_dia or 0),
            'valor_hora_adic': float(reserva.valor_hora_adic or 0),
            'abono': float(reserva.abono or 0),
            'total': float(reserva.total or 0),
            'observaciones': reserva.observaciones,
            'estado': reserva.estado,
            'created_at': reserva.created_at,
            'updated_at': reserva.updated_at,                          # NUEVO
        }


class MantenimientoRepositorySA:

    @staticmethod
    def obtener_historial(limite: int = 50) -> List[Dict]:
        with get_session() as session:
            mantenimientos = session.query(MantenimientoVehiculo).order_by(
                MantenimientoVehiculo.created_at.desc()
            ).limit(limite).all()

            return [MantenimientoRepositorySA._to_dict(m) for m in mantenimientos]

    @staticmethod
    def obtener_autos_con_km() -> List[Dict]:
        from core.models import Auto

        with get_session() as session:
            autos = session.query(Auto).filter(
                Auto.estado.notin_(['Vendido', 'Baja'])
            ).all()

            return [{
                'placa': a.placa,
                'marca': a.marca,
                'modelo': a.modelo,
                'kilometraje': a.kilometraje,
                'estado': a.estado,
            } for a in autos]

    @staticmethod
    def insertar(datos: MantenimientoCreate) -> int:
        with get_session() as session:
            nuevo_mant = MantenimientoVehiculo(
                placa=datos.placa.upper(),
                pieza_varias_tipo=datos.pieza_varias_tipo,
                pieza_varias_fecha=datos.pieza_varias_fecha,
                pieza_varias_desc=datos.pieza_varias_desc,
                pieza_varias_obs=datos.pieza_varias_obs,
                cost_varios=datos.cost_varios,
                km_proximo_cambio_aceite=datos.km_proximo_cambio_aceite,
                total_mantenimiento=datos.total_mantenimiento,
            )

            session.add(nuevo_mant)
            log.info("Mantenimiento registrado: placa=%s, tipo=%s", datos.placa, datos.pieza_varias_tipo)
            return nuevo_mant.id

    @staticmethod
    def actualizar_auto(placa: str, campos: Dict) -> None:
        from core.models import Auto

        with get_session() as session:
            auto = session.query(Auto).filter(Auto.placa == placa.upper()).first()

            if not auto:
                raise RegistroNoEncontrado(f"Vehiculo {placa} no encontrado.")

            for campo, valor in campos.items():
                if hasattr(auto, campo):
                    setattr(auto, campo, valor)

    @staticmethod
    def _to_dict(mant: MantenimientoVehiculo) -> Dict:
        return {
            'id': mant.id,
            'placa': mant.placa,
            'pieza_varias_tipo': mant.pieza_varias_tipo,
            'pieza_varias_fecha': mant.pieza_varias_fecha,
            'pieza_varias_desc': mant.pieza_varias_desc,
            'pieza_varias_obs': mant.pieza_varias_obs,
            'cost_varios': float(mant.cost_varios or 0),
            'km_proximo_cambio_aceite': mant.km_proximo_cambio_aceite,
            'total_mantenimiento': float(mant.total_mantenimiento or 0),
            'created_at': mant.created_at,
            'updated_at': mant.updated_at,                              # NUEVO
        }


class ComparendoRepositorySA:

    @staticmethod
    def obtener_todos() -> List[Dict]:
        with get_session() as session:
            comparendos = session.query(Comparendo).order_by(Comparendo.fecha_infraccion.desc()).all()
            return [ComparendoRepositorySA._to_dict(c) for c in comparendos]

    @staticmethod
    def insertar(datos: ComparendoCreate) -> int:
        with get_session() as session:
            nuevo_comparendo = Comparendo(
                placa=datos.placa.upper(),
                fecha_infraccion=datos.fecha_infraccion,
                hora_infraccion=datos.hora_infraccion,
                monto=datos.monto,
                id_renta=datos.id_renta,
                id_cliente=datos.id_cliente,
                estado=datos.estado,
                observaciones=datos.observaciones,
            )

            session.add(nuevo_comparendo)
            log.info("Comparendo registrado para placa %s", datos.placa)
            return nuevo_comparendo.id

    @staticmethod
    def actualizar_estado(id_comparendo: int, estado: str) -> None:
        with get_session() as session:
            comparendo = session.query(Comparendo).filter(Comparendo.id == id_comparendo).first()

            if not comparendo:
                raise RegistroNoEncontrado(f"Comparendo #{id_comparendo} no encontrado.")

            comparendo.estado = estado

    @staticmethod
    def buscar_historial_rentas_placa(placa: str) -> List[Dict]:
        from core.models import Renta

        with get_session() as session:
            rentas = session.query(Renta).filter(
                Renta.placa == placa.upper()
            ).order_by(Renta.fecha_recogida.desc()).all()

            return [{
                'id': r.id,
                'id_cliente': r.id_cliente,
                'fecha_recogida': r.fecha_recogida,
                'hora_recogida': r.hora_recogida,
                'fecha_retorno': r.fecha_retorno,
                'hora_retorno': r.hora_retorno,
            } for r in rentas]

    @staticmethod
    def _to_dict(comp: Comparendo) -> Dict:
        return {
            'id': comp.id,
            'placa': comp.placa,
            'fecha_infraccion': comp.fecha_infraccion,
            'hora_infraccion': comp.hora_infraccion,
            'monto': float(comp.monto or 0),
            'id_renta': comp.id_renta,
            'id_cliente': comp.id_cliente,
            'estado': comp.estado,
            'observaciones': comp.observaciones,
            'created_at': comp.created_at,
            'updated_at': comp.updated_at,                              # NUEVO
        }


class PagoRepositorySA:

    @staticmethod
    def obtener_por_renta(id_renta: int) -> List[Dict]:
        with get_session() as session:
            pagos = session.query(Pago).filter(
                Pago.id_renta == id_renta
            ).order_by(Pago.fecha.desc()).all()

            return [PagoRepositorySA._to_dict(p) for p in pagos]

    @staticmethod
    def insertar(datos: PagoCreate) -> int:
        with get_session() as session:
            nuevo_pago = Pago(
                id_renta=datos.id_renta,
                monto=datos.monto,
                metodo_pago=datos.metodo_pago,
                concepto=datos.concepto,
                observaciones=datos.observaciones,
                usuario=datos.usuario,
            )

            session.add(nuevo_pago)
            log.info("Pago registrado: $%s para renta #%s", datos.monto, datos.id_renta)
            return nuevo_pago.id

    @staticmethod
    def actualizar_abono_renta(id_renta: int) -> None:
        from core.models import Renta

        with get_session() as session:
            total_abonado = session.query(func.coalesce(func.sum(Pago.monto), 0)).filter(
                Pago.id_renta == id_renta
            ).scalar()

            renta = session.query(Renta).filter(Renta.id == id_renta).first()
            if renta:
                renta.abono = total_abonado
                renta.saldo_pendiente = max(0, float(renta.total or 0) - total_abonado)

    @staticmethod
    def _to_dict(pago: Pago) -> Dict:
        return {
            'id': pago.id,
            'id_renta': pago.id_renta,
            'fecha': pago.fecha,
            'monto': float(pago.monto or 0),
            'metodo_pago': pago.metodo_pago,
            'concepto': pago.concepto,
            'observaciones': pago.observaciones,
            'usuario': pago.usuario,
            'updated_at': pago.updated_at,                              # NUEVO
        }


class GastoRepositorySA:

    @staticmethod
    def obtener_todos(limite: int = 200) -> List[Dict]:
        with get_session() as session:
            gastos = session.query(Gasto).order_by(Gasto.fecha.desc()).limit(limite).all()
            return [GastoRepositorySA._to_dict(g) for g in gastos]

    @staticmethod
    def obtener_por_placa(placa: str) -> List[Dict]:                    # NUEVO
        """Obtiene todos los gastos vinculados a un vehiculo."""
        with get_session() as session:
            gastos = session.query(Gasto).filter(
                Gasto.placa == placa.upper()
            ).order_by(Gasto.fecha.desc()).all()
            return [GastoRepositorySA._to_dict(g) for g in gastos]

    @staticmethod
    def insertar(datos: GastoCreate) -> int:
        with get_session() as session:
            nuevo_gasto = Gasto(
                placa=datos.placa.upper() if datos.placa else None,     # NUEVO
                fecha=datos.fecha,
                categoria=datos.categoria,
                descripcion=datos.descripcion,
                monto=datos.monto,
                comprobante=datos.comprobante,
                usuario=datos.usuario,
            )

            session.add(nuevo_gasto)
            log.info("Gasto registrado: $%s en '%s' placa=%s",
                     datos.monto, datos.categoria, datos.placa or 'N/A')
            return nuevo_gasto.id

    @staticmethod
    def _to_dict(gasto: Gasto) -> Dict:
        return {
            'id': gasto.id,
            'placa': gasto.placa,                                       # NUEVO
            'fecha': gasto.fecha,
            'categoria': gasto.categoria,
            'descripcion': gasto.descripcion,
            'monto': float(gasto.monto or 0),
            'comprobante': gasto.comprobante,
            'usuario': gasto.usuario,
            'created_at': gasto.created_at,
            'updated_at': gasto.updated_at,                             # NUEVO
        }


class InspeccionRepositorySA:

    @staticmethod
    def obtener_por_renta(id_renta: int) -> List[Dict]:
        with get_session() as session:
            inspecciones = session.query(Inspeccion).filter(
                Inspeccion.id_renta == id_renta
            ).order_by(Inspeccion.fecha).all()

            return [InspeccionRepositorySA._to_dict(i) for i in inspecciones]

    @staticmethod
    def insertar(datos: InspeccionCreate) -> int:
        with get_session() as session:
            nueva_inspeccion = Inspeccion(
                id_renta=datos.id_renta,
                tipo=datos.tipo,
                kilometraje=datos.kilometraje,
                nivel_gasolina=datos.nivel_gasolina,
                limpieza=datos.limpieza,
                tiene_repuesto=1 if datos.tiene_repuesto else 0,
                tiene_gato_cruceta=1 if datos.tiene_gato_cruceta else 0,
                tiene_kit_carretera=1 if datos.tiene_kit_carretera else 0,
                tiene_documentos=1 if datos.tiene_documentos else 0,
                danos_carroceria=datos.danos_carroceria,
                observaciones=datos.observaciones,
            )

            session.add(nueva_inspeccion)
            log.info("Inspeccion (%s) registrada para renta #%s", datos.tipo, datos.id_renta)
            return nueva_inspeccion.id

    @staticmethod
    def _to_dict(insp: Inspeccion) -> Dict:
        return {
            'id': insp.id,
            'id_renta': insp.id_renta,
            'tipo': insp.tipo,
            'fecha': insp.fecha,
            'kilometraje': insp.kilometraje,
            'nivel_gasolina': insp.nivel_gasolina,
            'limpieza': insp.limpieza,
            'tiene_repuesto': bool(insp.tiene_repuesto),
            'tiene_gato_cruceta': bool(insp.tiene_gato_cruceta),
            'tiene_kit_carretera': bool(insp.tiene_kit_carretera),
            'tiene_documentos': bool(insp.tiene_documentos),
            'danos_carroceria': insp.danos_carroceria,
            'observaciones': insp.observaciones,
        }


class AlertaRepositorySA:

    @staticmethod
    def obtener_rentas_por_vencer() -> List[Dict]:
        from core.models import Renta, Cliente
        from datetime import date, timedelta

        hoy = date.today()
        tres_dias = hoy + timedelta(days=3)

        with get_session() as session:
            rentas = session.query(Renta, Cliente).join(
                Cliente, Renta.id_cliente == Cliente.id
            ).filter(
                and_(
                    Renta.estado == 'Activo',
                    Renta.fecha_retorno <= tres_dias,
                    Renta.fecha_retorno >= hoy,
                )
            ).all()

            return [{
                'id': r.id,
                'placa': r.placa,
                'nombre_completo': c.nombre_completo if c else r.nombre_cliente,
                'celular': c.celular if c else None,
                'fecha_retorno': r.fecha_retorno,
                'hora_retorno': r.hora_retorno,
            } for r, c in rentas]

    @staticmethod
    def obtener_documentos_por_vencer() -> List[Dict]:
        from core.models import Auto
        from datetime import date, timedelta

        hoy = date.today()
        quince_dias = hoy + timedelta(days=15)

        with get_session() as session:
            autos = session.query(Auto).filter(
                and_(
                    Auto.estado.notin_(['Vendido', 'Baja']),
                    and_(
                        Auto.vencimiento_soat <= quince_dias,
                        Auto.vencimiento_soat >= hoy,
                    )
                )
            ).all()

            return [{
                'placa': a.placa,
                'marca': a.marca,
                'modelo': a.modelo,
                'vencimiento_soat': a.vencimiento_soat,
                'vencimiento_tecnico': a.vencimiento_tecnico,
            } for a in autos]

    @staticmethod
    def obtener_mantenimientos_proximos() -> List[Dict]:
        from core.models import Auto

        with get_session() as session:
            autos = session.query(Auto).filter(
                and_(
                    Auto.proximo_aceite.isnot(None),
                    Auto.kilometraje >= (Auto.proximo_aceite - 500),
                )
            ).all()

            return [{
                'placa': a.placa,
                'kilometraje': a.kilometraje,
                'proximo_aceite': a.proximo_aceite,
            } for a in autos]


class InformeRepositorySA:

    @staticmethod
    def obtener_balance_consolidado() -> List[Dict]:
        from sqlalchemy import text

        with get_session() as session:
            sql = text("""
                SELECT
                    DATE_FORMAT(fecha, '%Y-%m') as mes,
                    SUM(ingreso) as ingresos,
                    SUM(taller) as egresos_taller,
                    SUM(caja) as gastos_caja
                FROM (
                    SELECT fecha, monto as ingreso, 0 as taller, 0 as caja
                    FROM pagos

                    UNION ALL

                    SELECT pieza_varias_fecha as fecha, 0 as ingreso, total_mantenimiento as taller, 0 as caja
                    FROM mantenimiento_vehiculos

                    UNION ALL

                    SELECT fecha, 0 as ingreso, 0 as taller, monto as caja
                    FROM gastos
                ) t
                WHERE fecha IS NOT NULL
                GROUP BY mes
                ORDER BY mes DESC
            """)

            result = session.execute(sql)
            return [dict(row) for row in result]
