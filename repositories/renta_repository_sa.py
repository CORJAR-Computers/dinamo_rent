"""
renta_repository_sa.py — Renta Repository with SQLAlchemy 2.0
"""
from typing import List, Optional, Dict
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_

from core.database_sa import get_session
from core.models import Renta, Auto, Cliente
from core.schemas import RentaCreate, RentaCierre, RentaUpdate
from core.exceptions import RegistroNoEncontrado
from core.logger import get_logger

log = get_logger(__name__)


class RentaRepositorySA:

    @staticmethod
    def obtener_activas() -> List[Dict]:
        with get_session() as session:
            rentas = session.query(Renta).filter(
                Renta.estado == 'Activo'
            ).order_by(Renta.fecha_retorno).all()
            return [RentaRepositorySA._to_dict(r) for r in rentas]

    @staticmethod
    def obtener_por_id(id_renta: int) -> Optional[Dict]:
        with get_session() as session:
            renta = session.query(Renta).filter(Renta.id == id_renta).first()
            
            if not renta:
                raise RegistroNoEncontrado(f"Renta #{id_renta} no encontrada.")
            
            return RentaRepositorySA._to_dict(renta)

    @staticmethod
    def obtener_para_calendario(mes: int, anio: int) -> List[Dict]:
        from core.models import Reserva
        
        fecha_ini = date(anio, mes, 1)
        if mes == 12:
            fecha_fin = date(anio + 1, 1, 1)
        else:
            fecha_fin = date(anio, mes + 1, 1)
        
        with get_session() as session:
            # Rentas activas
            rentas = session.query(Renta).filter(
                and_(
                    Renta.estado == 'Activo',
                    Renta.fecha_recogida < fecha_fin,
                    Renta.fecha_retorno >= fecha_ini
                )
            ).all()
            
            resultados = []
            for r in rentas:
                resultados.append({
                    'placa': r.placa,
                    'fecha_recogida': r.fecha_recogida,
                    'fecha_retorno': r.fecha_retorno,
                    'tipo': 'Renta',
                    'nombre_cliente': r.nombre_cliente,
                })
            
            # Reservas confirmadas
            reservas = session.query(Reserva).filter(
                and_(
                    Reserva.estado == 'Confirmada',
                    Reserva.placa_asignada.isnot(None),
                    Reserva.fecha_recogida < fecha_fin,
                    Reserva.fecha_retorno >= fecha_ini
                )
            ).all()
            
            for r in reservas:
                resultados.append({
                    'placa': r.placa_asignada,
                    'fecha_recogida': r.fecha_recogida,
                    'fecha_retorno': r.fecha_retorno,
                    'tipo': 'Reserva',
                    'nombre_cliente': r.nombre_cliente,
                })
            
            return resultados

    @staticmethod
    def insertar(datos: RentaCreate) -> int:
        with get_session() as session:
            nueva_renta = Renta(
                placa=datos.placa.upper(),
                id_cliente=datos.id_cliente,
                nombre_cliente=datos.nombre_cliente,
                no_licencia=datos.no_licencia,
                nacionalidad=datos.nacionalidad,
                fecha_recogida=datos.fecha_recogida,
                hora_recogida=datos.hora_recogida,
                ubicacion_recogida=datos.ubicacion_recogida,
                fecha_retorno=datos.fecha_retorno,
                hora_retorno=datos.hora_retorno,
                ubicacion_retorno=datos.ubicacion_retorno,
                dias_calculados=datos.dias_calculados,
                horas_extras=datos.horas_extras,
                valor_dia=datos.valor_dia,
                valor_hora_extra=datos.valor_hora_extra,
                valor_dia_extra=datos.valor_dia_extra,
                costo_lavado=datos.costo_lavado,
                costo_silla=datos.costo_silla,
                costo_retorno=datos.costo_retorno,
                costo_domicilio=datos.costo_domicilio,
                costo_cables=datos.costo_cables,
                costo_inversor=datos.costo_inversor,
                descuento=datos.descuento,
                subtotal=datos.subtotal,
                impuestos=datos.impuestos,
                total=datos.total,
                abono=datos.abono,
                saldo_pendiente=datos.saldo_pendiente,
                estado=datos.estado,
                observaciones=datos.observaciones,
                km_salida=datos.km_salida,
                tanque_salida=datos.tanque_salida,
                id_reserva=datos.id_reserva,
            )
            
            session.add(nueva_renta)
            session.flush()
            log.info("Renta creada: id=%s, placa=%s, cliente=%s", 
                     nueva_renta.id, datos.placa, datos.nombre_cliente)
            return nueva_renta.id

    @staticmethod
    def cerrar_renta(id_renta: int, datos_cierre: RentaCierre) -> None:
        with get_session() as session:
            renta = session.query(Renta).filter(Renta.id == id_renta).first()
            
            if not renta:
                raise RegistroNoEncontrado(f"Renta #{id_renta} no encontrada.")
            
            renta.estado = 'Finalizado'
            renta.fecha_devolucion_real = datos_cierre.fecha_devolucion_real
            renta.hora_devolucion_real = datos_cierre.hora_devolucion_real
            renta.km_final = datos_cierre.km_final
            renta.tanque_final = datos_cierre.tanque_final
            renta.total = datos_cierre.total
            renta.observaciones = (renta.observaciones or '') + '\n' + datos_cierre.nota_cierre
            
            log.info("Renta #%s cerrada. Total: %s", id_renta, datos_cierre.total)

    @staticmethod
    def extender(id_renta: int, nueva_fecha: date, nueva_hora: datetime, 
                 nuevos_dias: int, nuevo_total: Decimal, nuevo_saldo: Decimal) -> None:
        with get_session() as session:
            renta = session.query(Renta).filter(Renta.id == id_renta).first()
            
            if not renta:
                raise RegistroNoEncontrado(f"Renta #{id_renta} no encontrada.")
            
            renta.fecha_retorno = nueva_fecha
            renta.hora_retorno = nueva_hora
            renta.dias_calculados = nuevos_dias
            renta.total = nuevo_total
            renta.saldo_pendiente = nuevo_saldo
            
            log.info("Renta #%s extendida hasta %s", id_renta, nueva_fecha)

    @staticmethod
    def obtener_datos_documento(id_renta: int) -> Dict:
        with get_session() as session:
            renta = session.query(Renta).options(
                joinedload(Renta.auto_rel),
                joinedload(Renta.cliente_rel)
            ).filter(Renta.id == id_renta).first()
            
            if not renta:
                raise RegistroNoEncontrado(f"No se pudo generar documento para la renta #{id_renta}")
            
            data = RentaRepositorySA._to_dict(renta)
            
            # Add auto data
            if renta.auto_rel:
                data.update({
                    'auto_marca': renta.auto_rel.marca,
                    'auto_modelo': renta.auto_rel.modelo,
                    'auto_color': renta.auto_rel.color,
                    'auto_tipo': renta.auto_rel.tipo,
                    'auto_combustible': renta.auto_rel.combustible,
                    'auto_cilindraje': renta.auto_rel.cilindraje,
                    'auto_version': renta.auto_rel.version,
                    'auto_placa': renta.auto_rel.placa,
                })
            
            # Add cliente data
            if renta.cliente_rel:
                data.update({
                    'documento_cliente': renta.cliente_rel.no_doc,
                    'direccion': renta.cliente_rel.dir_residencia,
                    'celular': renta.cliente_rel.celular,
                    'email': renta.cliente_rel.email,
                    'licencia_numero': renta.cliente_rel.no_licencia,
                    'tipo_licencia': renta.cliente_rel.tipo_licencia,
                })
            
            return data

    @staticmethod
    def actualizar_placa(id_renta: int, nueva_placa: str, nota: str) -> None:
        with get_session() as session:
            renta = session.query(Renta).filter(Renta.id == id_renta).first()
            
            if not renta:
                raise RegistroNoEncontrado(f"Renta #{id_renta} no encontrada.")
            
            renta.placa = nueva_placa.upper()
            renta.observaciones = (renta.observaciones or '') + '\n' + nota

    @staticmethod
    def kpi_globales() -> Dict:
        with get_session() as session:
            total = session.query(func.count(Renta.id)).scalar()
            activas = session.query(func.count(Renta.id)).filter(Renta.estado == 'Activo').scalar()
            ingresos = session.query(func.coalesce(func.sum(Renta.total), 0)).scalar()
            
            return {
                'total_rentas': total,
                'rentas_activas': activas,
                'ingresos_totales': float(ingresos),
            }

    @staticmethod
    def balance_mensual() -> Dict:
        with get_session() as session:
            from core.models import MantenimientoVehiculo
            
            # Ingresos por mes
            ingresos_query = session.query(
                func.date_format(Renta.fecha_recogida, '%Y-%m').label('mes'),
                func.sum(Renta.total).label('total')
            ).filter(
                Renta.estado != 'Cancelado'
            ).group_by('mes').all()
            
            ingresos = {row.mes: float(row.total or 0) for row in ingresos_query}
            
            # Egresos (mantenimiento) por mes
            egresos_query = session.query(
                func.date_format(MantenimientoVehiculo.created_at, '%Y-%m').label('mes'),
                func.sum(MantenimientoVehiculo.total_mantenimiento).label('total')
            ).group_by('mes').all()
            
            egresos = {row.mes: float(row.total or 0) for row in egresos_query}
            
            # Autos con costo fijo
            autos = session.query(Auto).filter(Auto.costo_fijo_mensual > 0).all()
            autos_data = [{
                'placa': a.placa,
                'costo_fijo_mensual': float(a.costo_fijo_mensual or 0),
                'fecha_real': a.fecha_ingreso or a.created_at,
            } for a in autos]
            
            return {
                'ingresos': ingresos,
                'egresos': egresos,
                'autos': autos_data,
            }

    @staticmethod
    def _to_dict(renta: Renta) -> Dict:
        return {
            'id': renta.id,
            'placa': renta.placa,
            'id_cliente': renta.id_cliente,
            'nombre_cliente': renta.nombre_cliente,
            'no_licencia': renta.no_licencia,
            'nacionalidad': renta.nacionalidad,
            'fecha_recogida': renta.fecha_recogida,
            'hora_recogida': renta.hora_recogida,
            'ubicacion_recogida': renta.ubicacion_recogida,
            'fecha_retorno': renta.fecha_retorno,
            'hora_retorno': renta.hora_retorno,
            'ubicacion_retorno': renta.ubicacion_retorno,
            'dias_calculados': renta.dias_calculados,
            'horas_extras': renta.horas_extras,
            'valor_dia': float(renta.valor_dia or 0),
            'valor_hora_extra': float(renta.valor_hora_extra or 0),
            'valor_dia_extra': float(renta.valor_dia_extra or 0),
            'costo_lavado': float(renta.costo_lavado or 0),
            'costo_silla': float(renta.costo_silla or 0),
            'costo_retorno': float(renta.costo_retorno or 0),
            'costo_domicilio': float(renta.costo_domicilio or 0),
            'costo_cables': float(renta.costo_cables or 0),
            'costo_inversor': float(renta.costo_inversor or 0),
            'descuento': float(renta.descuento or 0),
            'subtotal': float(renta.subtotal or 0),
            'impuestos': float(renta.impuestos or 0),
            'total': float(renta.total or 0),
            'abono': float(renta.abono or 0),
            'saldo_pendiente': float(renta.saldo_pendiente or 0),
            'estado': renta.estado,
            'observaciones': renta.observaciones,
            'fecha_devolucion_real': renta.fecha_devolucion_real,
            'hora_devolucion_real': renta.hora_devolucion_real,
            'km_final': renta.km_final,
            'tanque_final': renta.tanque_final,
            'km_salida': renta.km_salida,
            'tanque_salida': renta.tanque_salida,
            'id_reserva': renta.id_reserva,
            'created_at': renta.created_at,
        }
