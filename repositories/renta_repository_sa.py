"""
renta_repository_sa.py — Repositorio de Rentas.

Métodos críticos aceptan parámetro `session` para soporte de UnitOfWork.
Si session es provisto, lo usa (transacción compartida).
Si no, crea su propia sesión (comportamiento original).
"""

from typing import List, Dict

from sqlalchemy import func, and_, extract
from sqlalchemy.orm import Session

from core.models import Renta, Reserva
from core.schemas import RentaCreate, RentaCierre
from core.exceptions import RegistroNoEncontrado
from core.logger import get_logger
from core.unit_of_work import session_scope

log = get_logger(__name__)


class RentaRepositorySA:
    @staticmethod
    def insertar(datos: RentaCreate, session: Session = None) -> int:
        """Inserta una nueva renta. Retorna el ID.

        Args:
            datos: Datos validados de la renta (Pydantic RentaCreate)
            session: Sesión de UnitOfWork (opcional). Si no se pasa,
                     crea su propia sesión con commit automático.
        """
        with session_scope(session) as s:
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
            s.add(nueva_renta)
            s.flush()
            log.info(
                "Renta creada: id=%s, placa=%s, cliente=%s",
                nueva_renta.id,
                datos.placa,
                datos.nombre_cliente,
            )
            return nueva_renta.id

    @staticmethod
    def obtener_por_id(id_renta: int, session: Session = None) -> Dict:
        """Obtiene una renta por su ID."""
        with session_scope(session) as s:
            renta = s.query(Renta).filter(Renta.id == id_renta).first()
            if not renta:
                raise RegistroNoEncontrado(f"Renta #{id_renta} no encontrada.")
            return RentaRepositorySA._to_dict(renta)

    @staticmethod
    def obtener_activas(session: Session = None) -> List[Dict]:
        """Obtiene todas las rentas con estado 'Activo'."""
        with session_scope(session) as s:
            rentas = (
                s.query(Renta)
                .filter(Renta.estado == "Activo")
                .order_by(Renta.fecha_recogida.desc())
                .all()
            )
            return [RentaRepositorySA._to_dict(r) for r in rentas]

    @staticmethod
    def obtener_activas_filtradas(filtro: str, session: Session = None) -> List[Dict]:
        """Obtiene rentas activas aplicando filtros de fecha directamente en la BD."""
        from datetime import date, timedelta

        with session_scope(session) as s:
            query = s.query(Renta).filter(Renta.estado == "Activo")
            hoy = date.today()

            if filtro == "Vencen Hoy":
                query = query.filter(Renta.fecha_retorno == hoy)
            elif filtro == "Retrasadas (Vencidas)":
                query = query.filter(Renta.fecha_retorno < hoy)
            elif filtro == "Entregas de Mañana":
                manana = hoy + timedelta(days=1)
                query = query.filter(Renta.fecha_retorno == manana)

            rentas = query.order_by(Renta.fecha_recogida.desc()).all()
            return [RentaRepositorySA._to_dict(r) for r in rentas]

    @staticmethod
    def cerrar_renta(id_renta: int, datos_cierre: RentaCierre, session: Session = None) -> None:
        """Cierra una renta registrando la devolución.

        Args:
            id_renta: ID de la renta a cerrar
            datos_cierre: Datos del cierre validados (Pydantic RentaCierre)
            session: Sesión de UnitOfWork (opcional)
        """
        with session_scope(session) as s:
            renta = s.query(Renta).filter(Renta.id == id_renta).first()
            if not renta:
                raise RegistroNoEncontrado(f"Renta #{id_renta} no encontrada.")

            renta.estado = "Finalizado"
            renta.fecha_devolucion_real = datos_cierre.fecha_devolucion_real
            renta.hora_devolucion_real = datos_cierre.hora_devolucion_real
            renta.km_final = datos_cierre.km_final
            renta.tanque_final = datos_cierre.tanque_final

            # Agregar nota de cierre a observaciones
            nota = datos_cierre.nota_cierre or ""
            if nota:
                obs_previas = renta.observaciones or ""
                renta.observaciones = f"{obs_previas}\n{nota}".strip() if obs_previas else nota

            # Agregar otros cobros al total
            otros = float(datos_cierre.otros_cobros or 0)
            if otros > 0:
                renta.total = float(renta.total or 0) + otros
                renta.saldo_pendiente = max(0, float(renta.total or 0) - float(renta.abono or 0))

            log.info("Renta cerrada: id=%s", id_renta)

    @staticmethod
    def extender(
        id_renta: int,
        nueva_fecha: str,
        nueva_hora: str,
        nuevos_dias: int,
        nuevo_total: float,
        nuevo_saldo: float,
        session: Session = None,
    ) -> None:
        """Extiende una renta activa con nueva fecha de retorno."""
        with session_scope(session) as s:
            renta = s.query(Renta).filter(Renta.id == id_renta).first()
            if not renta:
                raise RegistroNoEncontrado(f"Renta #{id_renta} no encontrada.")

            renta.fecha_retorno = nueva_fecha
            renta.hora_retorno = nueva_hora
            renta.dias_calculados = nuevos_dias
            renta.total = nuevo_total
            renta.saldo_pendiente = nuevo_saldo

            log.info("Renta extendida: id=%s, nueva fecha=%s", id_renta, nueva_fecha)

    @staticmethod
    def actualizar_placa(
        id_renta: int, placa_nueva: str, nota: str, session: Session = None
    ) -> None:
        """Actualiza la placa del vehículo asignado a una renta.

        Args:
            id_renta: ID de la renta
            placa_nueva: Nueva placa a asignar
            nota: Nota de cambio para agregar a observaciones
            session: Sesión de UnitOfWork (opcional)
        """
        with session_scope(session) as s:
            renta = s.query(Renta).filter(Renta.id == id_renta).first()
            if not renta:
                raise RegistroNoEncontrado(f"Renta #{id_renta} no encontrada.")

            renta.placa = placa_nueva.upper()
            obs_previas = renta.observaciones or ""
            renta.observaciones = f"{obs_previas}\n{nota}".strip() if obs_previas else nota

            log.info("Renta %s: placa actualizada a %s", id_renta, placa_nueva)

    @staticmethod
    def obtener_datos_documento(id_renta: int, session: Session = None) -> Dict:
        """
        Obtiene los datos completos de una renta para generar documentos (contratos, recibos).
        Incluye datos del cliente y vehículo via JOIN.
        """
        with session_scope(session) as s:
            renta = s.query(Renta).filter(Renta.id == id_renta).first()
            if not renta:
                raise RegistroNoEncontrado(f"Renta #{id_renta} no encontrada.")

            resultado = RentaRepositorySA._to_dict(renta)

            # Agregar datos del auto si existe la relación
            if renta.auto_rel:
                auto = renta.auto_rel
                resultado["auto_marca"] = auto.marca
                resultado["auto_modelo"] = auto.modelo
                resultado["auto_color"] = auto.color
                resultado["auto_tipo"] = auto.tipo
                resultado["auto_transmision"] = auto.transmision
                resultado["auto_combustible"] = auto.combustible

            # Agregar datos del cliente si existe la relación
            if renta.cliente_rel:
                cliente = renta.cliente_rel
                resultado["cliente_celular"] = cliente.celular
                resultado["cliente_email"] = cliente.email
                resultado["cliente_direccion"] = cliente.dir_residencia or cliente.dir_temporal
                resultado["cliente_no_licencia"] = cliente.no_licencia
                resultado["cliente_tipo_licencia"] = cliente.tipo_licencia

            return resultado

    @staticmethod
    def obtener_para_calendario(mes: int, anio: int, session: Session = None) -> List[Dict]:
        """Obtiene rentas activas y reservas para mostrar en el calendario del mes dado."""
        with session_scope(session) as s:
            # Rentas activas del mes
            rentas = (
                s.query(Renta)
                .filter(
                    and_(
                        Renta.estado == "Activo",
                        extract('month', Renta.fecha_recogida) == mes,
                        extract('year', Renta.fecha_recogida) == anio,
                    )
                )
                .all()
            )

            # Reservas confirmadas del mes
            reservas = (
                s.query(Reserva)
                .filter(
                    and_(
                        Reserva.estado == "Confirmada",
                        extract('month', Reserva.fecha_recogida) == mes,
                        extract('year', Reserva.fecha_recogida) == anio,
                    )
                )
                .all()
            )

            resultado = []
            for r in rentas:
                resultado.append(
                    {
                        "tipo": "renta",
                        "id": r.id,
                        "placa": r.placa,
                        "cliente": r.nombre_cliente,
                        "fecha_recogida": r.fecha_recogida,
                        "fecha_retorno": r.fecha_retorno,
                        "estado": r.estado,
                    }
                )
            for rv in reservas:
                resultado.append(
                    {
                        "tipo": "reserva",
                        "id": rv.id,
                        "placa": rv.placa_asignada,
                        "cliente": rv.nombre_cliente,
                        "fecha_recogida": rv.fecha_recogida,
                        "fecha_retorno": rv.fecha_retorno,
                        "estado": rv.estado,
                    }
                )

            return resultado

    @staticmethod
    def _to_dict(renta: Renta) -> Dict:
        return {
            "id": renta.id,
            "placa": renta.placa,
            "id_cliente": renta.id_cliente,
            "nombre_cliente": renta.nombre_cliente,
            "no_licencia": renta.no_licencia,
            "nacionalidad": renta.nacionalidad,
            "fecha_recogida": renta.fecha_recogida,
            "hora_recogida": renta.hora_recogida,
            "ubicacion_recogida": renta.ubicacion_recogida,
            "fecha_retorno": renta.fecha_retorno,
            "hora_retorno": renta.hora_retorno,
            "ubicacion_retorno": renta.ubicacion_retorno,
            "dias_calculados": renta.dias_calculados,
            "horas_extras": renta.horas_extras,
            "valor_dia": float(renta.valor_dia or 0),
            "valor_hora_extra": float(renta.valor_hora_extra or 0),
            "valor_dia_extra": float(renta.valor_dia_extra or 0),
            "costo_lavado": float(renta.costo_lavado or 0),
            "costo_silla": float(renta.costo_silla or 0),
            "costo_retorno": float(renta.costo_retorno or 0),
            "costo_domicilio": float(renta.costo_domicilio or 0),
            "costo_cables": float(renta.costo_cables or 0),
            "costo_inversor": float(renta.costo_inversor or 0),
            "descuento": float(renta.descuento or 0),
            "subtotal": float(renta.subtotal or 0),
            "impuestos": float(renta.impuestos or 0),
            "total": float(renta.total or 0),
            "abono": float(renta.abono or 0),
            "saldo_pendiente": float(renta.saldo_pendiente or 0),
            "estado": renta.estado,
            "observaciones": renta.observaciones,
            "fecha_devolucion_real": renta.fecha_devolucion_real,
            "hora_devolucion_real": renta.hora_devolucion_real,
            "km_final": renta.km_final,
            "tanque_final": renta.tanque_final,
            "km_salida": float(renta.km_salida or 0),
            "tanque_salida": renta.tanque_salida,
            "id_reserva": renta.id_reserva,
            "created_at": renta.created_at,
        }
