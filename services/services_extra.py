"""
services_extra.py — Servicios adicionales con SQLAlchemy y Pydantic

Complementa services.py con las entidades restantes.
Actualizado para usar el nuevo sistema con SQLAlchemy 2.0 y validacion Pydantic.

F1A Changes applied:
  - GastoService.registrar: Soporta campo placa para vincular gasto a vehiculo
  - GastoService.listar_por_placa: Nuevo metodo para ver gastos de un vehiculo
"""
import datetime
from typing import List, Dict, Optional
from decimal import Decimal

from core.exceptions import (
    NegocioError, ValidacionError, DatabaseError, RegistroNoEncontrado
)
from core.logger import get_logger, get_audit_logger
from core.security import SecurityManager
from core.validators import requerir, validar_placa
from core.schemas import (
    ReservaCreate,
    MantenimientoCreate,
    UsuarioCreate,
    InspeccionCreate,
    ComparendoCreate,
    ComparendoUpdate,
    PagoCreate,
    GastoCreate,
)
from repositories.repositories_sa import (
    ReservaRepositorySA,
    MantenimientoRepositorySA,
    UsuarioRepositorySA,
    InspeccionRepositorySA,
    ComparendoRepositorySA,
    PagoRepositorySA,
    GastoRepositorySA,
    AlertaRepositorySA,
    InformeRepositorySA,
)
from datetime import datetime as dt_datetime

log = get_logger(__name__)
audit = get_audit_logger()


# =====================================================================
# SERVICIO DE RESERVAS
# =====================================================================

class ReservaService:

    @staticmethod
    def listar() -> List[Dict]:
        return ReservaRepositorySA.obtener_todas()

    @staticmethod
    def crear(datos: dict) -> int:
        """Crea una reserva validando que el cliente este seleccionado."""
        if not datos.get("id_cliente"):
            raise ValidacionError(
                detalle="id_cliente requerido",
                mensaje_usuario="Debe seleccionar un cliente para la reserva.",
            )
        if not datos.get("categoria_vehiculo") and not datos.get("placa_asignada"):
            raise ValidacionError(
                detalle="Sin vehiculo/categoria",
                mensaje_usuario="Seleccione un vehiculo o categoria valida.",
            )

        # Calcular total si no viene
        if not datos.get("total"):
            dias = int(datos.get("dias_calculados", 1))
            horas = int(datos.get("horas_extras", 0))
            val_dia = float(datos.get("valor_dia", 0))
            val_hora = float(datos.get("valor_hora_adic", 0))
            datos["total"] = dias * val_dia + horas * val_hora

        datos.setdefault("estado", "Confirmada")
        datos.setdefault("ubicacion_recogida", "Oficina")
        datos.setdefault("ubicacion_retorno", "Oficina")

        # Validar con Pydantic
        try:
            reserva_validada = ReservaCreate(**datos)
        except Exception as e:
            raise ValidacionError(f"Datos de reserva invalidos: {str(e)}")

        id_reserva = ReservaRepositorySA.insertar(reserva_validada)
        audit.info("Reserva creada: id=%s, cliente=%s", id_reserva, datos.get("nombre_cliente"))
        return id_reserva

    @staticmethod
    def cancelar(id_reserva: int) -> None:
        ReservaRepositorySA.cancelar(id_reserva)
        audit.info("Reserva #%s cancelada", id_reserva)

    @staticmethod
    def obtener_contacto(id_reserva: int) -> Dict:
        return ReservaRepositorySA.obtener_contacto_cliente(id_reserva)

    @staticmethod
    def obtener_para_pdf(id_reserva: int) -> Dict:
        return ReservaRepositorySA.obtener_por_id(id_reserva)


# =====================================================================
# SERVICIO DE MANTENIMIENTO
# =====================================================================

class MantenimientoService:

    @staticmethod
    def listar_historial(limite: int = 50) -> List[Dict]:
        return MantenimientoRepositorySA.obtener_historial(limite)

    @staticmethod
    def listar_autos() -> List[Dict]:
        return MantenimientoRepositorySA.obtener_autos_con_km()

    @staticmethod
    def registrar(datos: dict) -> None:
        """
        Registra un servicio y actualiza el auto.
        datos debe tener: placa, tipo, fecha, costo, obs, km_actual, prox_km,
                          accion_estado ('mantener'|'mantenimiento'|'disponible')
        """
        placa = validar_placa(datos.get("placa", ""))
        if not datos.get("tipo"):
            raise ValidacionError(mensaje_usuario="Seleccione el tipo de servicio.")

        # 1. Insertar historial con validacion Pydantic
        mant_data = {
            "placa": placa,
            "pieza_varias_tipo": datos["tipo"],
            "pieza_varias_fecha": datos.get("fecha"),
            "pieza_varias_desc": datos.get("desc"),
            "pieza_varias_obs": datos.get("obs"),
            "cost_varios": float(datos.get("costo", 0)),
            "km_proximo_cambio_aceite": int(datos.get("prox_km", 0)) if datos["tipo"] == "Cambio Aceite" else 0,
            "total_mantenimiento": float(datos.get("costo", 0)),
        }

        try:
            mant_validado = MantenimientoCreate(**mant_data)
        except Exception as e:
            raise ValidacionError(f"Datos de mantenimiento invalidos: {str(e)}")

        MantenimientoRepositorySA.insertar(mant_validado)

        # 2. Actualizar campos del auto
        campos_auto: dict = {"kilometraje": datos.get("km_actual", 0)}

        tipo = datos["tipo"]
        if tipo == "Cambio Aceite":
            campos_auto["proximo_aceite"] = int(datos.get("prox_km", 0))
        elif tipo == "Frenos":
            campos_auto["proximo_frenos"] = int(datos.get("prox_km", 0))
        elif tipo == "Tecno-Mecanica":
            # 1 ano de vigencia
            try:
                fecha_base = dt_datetime.strptime(str(datos.get("fecha"))[:10], "%Y-%m-%d")
                campos_auto["vencimiento_tecnico"] = (
                    fecha_base + datetime.timedelta(days=365)
                ).strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                pass

        # Cambio de estado opcional
        accion = datos.get("accion_estado", "mantener")
        if accion == "mantenimiento":
            campos_auto["estado"] = "Mantenimiento"
        elif accion == "disponible":
            campos_auto["estado"] = "Disponible"

        MantenimientoRepositorySA.actualizar_auto(placa, campos_auto)

        audit.info("Mantenimiento registrado: placa=%s, tipo=%s, costo=%s",
                   placa, tipo, datos.get("costo"))


# =====================================================================
# SERVICIO DE USUARIOS
# =====================================================================

class UsuarioService:

    @staticmethod
    def listar() -> List[Dict]:
        return UsuarioRepositorySA.obtener_todos()

    @staticmethod
    def crear(datos: dict) -> None:
        """Crea un nuevo usuario con contrasena hasheada."""
        requerir(datos.get("username"), "Nombre de usuario")
        requerir(datos.get("nombre"), "Nombre completo")
        pwd = datos.get("password_raw", "")
        if not pwd:
            raise ValidacionError(mensaje_usuario="La contrasena es obligatoria para nuevos usuarios.")

        # Verificar que el username no exista
        if UsuarioRepositorySA.obtener_por_username(datos["username"]):
            raise NegocioError(mensaje_usuario="El nombre de usuario ya esta en uso.")

        # Validar con Pydantic
        try:
            usuario_validado = UsuarioCreate(
                username=datos["username"].strip(),
                password_raw=pwd,
                nombre=datos["nombre"].strip(),
                rol=datos.get("rol", "Operador"),
                email=datos.get("email", "").strip(),
                activo=True,
            )
        except Exception as e:
            raise ValidacionError(f"Datos de usuario invalidos: {str(e)}")

        UsuarioRepositorySA.insertar(usuario_validado)
        audit.info("Usuario creado: %s (rol=%s)", datos["username"], datos.get("rol"))

    @staticmethod
    def actualizar(datos: dict) -> None:
        """Actualiza un usuario. Si 'password_raw' esta presente, cambia la contrasena."""
        requerir(datos.get("username"), "Nombre de usuario")
        requerir(datos.get("nombre"), "Nombre completo")

        # Crear objeto de actualizacion
        from core.schemas import UsuarioUpdate

        update_data = UsuarioUpdate(
            username=datos["username"],
            nombre=datos.get("nombre", "").strip(),
            rol=datos.get("rol"),
            email=datos.get("email", "").strip(),
            activo=bool(int(datos.get("activo", 1))) if datos.get("activo") is not None else None,
            password_raw=datos.get("password_raw", "") or None,
        )

        UsuarioRepositorySA.actualizar(update_data)
        audit.info("Usuario actualizado: %s", datos["username"])

    @staticmethod
    def eliminar(username: str) -> None:
        if username == "admin":
            raise NegocioError(mensaje_usuario="No se puede eliminar el Administrador Principal.")
        UsuarioRepositorySA.eliminar(username)
        audit.info("Usuario eliminado: %s", username)


# =====================================================================
# SERVICIO DE INSPECCIONES
# =====================================================================

class InspeccionService:

    @staticmethod
    def listar_por_renta(id_renta: int) -> List[Dict]:
        return InspeccionRepositorySA.obtener_por_renta(id_renta)

    @staticmethod
    def registrar(datos: dict) -> int:
        # Validaciones de negocio
        requerir(datos.get("id_renta"), "ID de Renta")
        requerir(datos.get("tipo"), "Tipo de Inspeccion")
        requerir(datos.get("kilometraje"), "Kilometraje")

        # Validar con Pydantic
        try:
            inspeccion_validada = InspeccionCreate(**datos)
        except Exception as e:
            raise ValidacionError(f"Datos de inspeccion invalidos: {str(e)}")

        id_inspeccion = InspeccionRepositorySA.insertar(inspeccion_validada)
        audit.info("Inspeccion (%s) registrada para la renta #%s", datos["tipo"], datos["id_renta"])
        return id_inspeccion


# =====================================================================
# SERVICIO DE COMPARENDOS / MULTAS
# =====================================================================

class ComparendoService:

    @staticmethod
    def listar() -> List[Dict]:
        return ComparendoRepositorySA.obtener_todos()

    @staticmethod
    def registrar(datos: dict) -> dict:
        """
        Registra la multa e intenta vincularla a un cliente automaticamente.
        Retorna un dict con el resultado de la busqueda.
        """
        placa = requerir(datos.get("placa"), "Placa del Vehiculo")
        fecha_str = requerir(datos.get("fecha"), "Fecha de Infraccion")
        hora_str = requerir(datos.get("hora"), "Hora de Infraccion")

        # 1. Armar el datetime exacto de la infraccion
        try:
            infraccion_dt = dt_datetime.strptime(f"{fecha_str} {hora_str}", "%Y-%m-%d %H:%M")
        except ValueError as e:
            raise ValidacionError(f"Fecha/hora invalida: {str(e)}")

        # 2. Buscar en el historial de la placa quien tenia el auto
        rentas = ComparendoRepositorySA.buscar_historial_rentas_placa(placa)

        cliente_encontrado = None
        renta_encontrada = None

        for r in rentas:
            # Reconstruir fechas de la renta
            try:
                f_rec_str = str(r['fecha_recogida'])[:10]
                h_rec_str = str(r['hora_recogida'])[:5] if r['hora_recogida'] else "00:00"
                f_ret_str = str(r['fecha_retorno'])[:10]
                h_ret_str = str(r['hora_retorno'])[:5] if r['hora_retorno'] else "00:00"

                inicio_dt = dt_datetime.strptime(f"{f_rec_str} {h_rec_str}", "%Y-%m-%d %H:%M")
                fin_dt = dt_datetime.strptime(f"{f_ret_str} {h_ret_str}", "%Y-%m-%d %H:%M")

                # La infraccion ocurrio durante esta renta?
                if inicio_dt <= infraccion_dt <= fin_dt:
                    cliente_encontrado = r['id_cliente']
                    renta_encontrada = r['id']
                    break
            except Exception as e:
                log.warning(f"Error parseando fechas de renta {r['id']}: {e}")
                continue

        # 3. Asignar los IDs encontrados a los datos
        datos["id_cliente"] = cliente_encontrado
        datos["id_renta"] = renta_encontrada

        # 4. Validar y guardar en base de datos
        try:
            comparendo_validado = ComparendoCreate(
                placa=placa,
                fecha_infraccion=dt_datetime.strptime(fecha_str, "%Y-%m-%d").date(),
                hora_infraccion=dt_datetime.strptime(hora_str, "%H:%M").time(),
                monto=float(datos.get("monto", 0)),
                id_renta=renta_encontrada,
                id_cliente=cliente_encontrado,
                estado=datos.get("estado", "Pendiente"),
                observaciones=datos.get("observaciones"),
            )
        except Exception as e:
            raise ValidacionError(f"Datos de comparendo invalidos: {str(e)}")

        id_nuevo = ComparendoRepositorySA.insertar(comparendo_validado)
        audit.info("Comparendo registrado para placa %s. Renta vinculada: %s", placa, renta_encontrada)

        return {
            "id_comparendo": id_nuevo,
            "vinculado": cliente_encontrado is not None,
            "id_renta": renta_encontrada,
            "id_cliente": cliente_encontrado
        }

    @staticmethod
    def cambiar_estado(id_comparendo: int, estado: str) -> None:
        ComparendoRepositorySA.actualizar_estado(id_comparendo, estado)


# =====================================================================
# SERVICIO DE PAGOS Y CAJA
# =====================================================================

class PagoService:

    @staticmethod
    def listar_por_renta(id_renta: int) -> List[Dict]:
        return PagoRepositorySA.obtener_por_renta(id_renta)

    @staticmethod
    def registrar(datos: dict) -> int:
        requerir(datos.get("id_renta"), "ID de Renta")
        requerir(datos.get("monto"), "Monto del Pago")
        requerir(datos.get("metodo_pago"), "Metodo de Pago")

        monto = float(datos["monto"])
        if monto <= 0:
            raise ValidacionError("El monto del pago debe ser mayor a cero.")

        # Validar con Pydantic
        try:
            pago_validado = PagoCreate(
                id_renta=int(datos["id_renta"]),
                monto=monto,
                metodo_pago=datos["metodo_pago"],
                concepto=datos.get("concepto", "Abono"),
                observaciones=datos.get("observaciones"),
                usuario=datos.get("usuario"),
            )
        except Exception as e:
            raise ValidacionError(f"Datos de pago invalidos: {str(e)}")

        # 1. Registrar el recibo
        id_pago = PagoRepositorySA.insertar(pago_validado)

        # 2. Sincronizar el total abonado en la tabla principal de rentas
        PagoRepositorySA.actualizar_abono_renta(int(datos["id_renta"]))

        audit.info("Pago de $%s registrado para la renta #%s (%s)", monto, datos["id_renta"], datos["metodo_pago"])
        return id_pago


# =====================================================================
# SERVICIO DE ALERTAS Y NOTIFICACIONES
# =====================================================================

class AlertaService:

    @staticmethod
    def obtener_todas_las_alertas() -> dict:
        """
        Consulta todos los repositorios y devuelve un diccionario estructurado
        con todas las alertas activas y los mensajes pre-armados.
        """
        alertas = {
            "clientes": [],  # Alertas para enviar a clientes por WhatsApp
            "internas": []   # Alertas para la empresa (Mantenimientos, SOAT)
        }

        # 1. Alertas de Rentas (Para enviar a Clientes)
        rentas = AlertaRepositorySA.obtener_rentas_por_vencer()
        for r in rentas:
            # Armar el mensaje de WhatsApp
            mensaje = (
                f"Hola {r['nombre_completo']}, te saludamos de Dinamo Rent a Car. "
                f"Te recordamos que la renta del vehiculo {r['placa']} finaliza "
                f"el {r['fecha_retorno']} a las {r['hora_retorno'][:5]}. "
                "Por favor confirmanos tu hora de entrega para esperarte!"
            )

            alertas["clientes"].append({
                "titulo": f"Renta por vencer - {r['placa']}",
                "cliente": r['nombre_completo'],
                "celular": r['celular'],
                "fecha": f"{r['fecha_retorno']} {r['hora_retorno'][:5]}",
                "mensaje_whatsapp": mensaje
            })

        # 2. Alertas de Documentos (Internas)
        docs = AlertaRepositorySA.obtener_documentos_por_vencer()
        for d in docs:
            texto = f"El vehiculo {d['placa']} ({d['marca']}) tiene documentos proximos a vencer:\n"
            if d.get('vencimiento_soat'):
                texto += f"  SOAT: {d['vencimiento_soat']}\n"
            if d.get('vencimiento_tecnico'):
                texto += f"  Tecno-mecanica: {d['vencimiento_tecnico']}"

            alertas["internas"].append({
                "titulo": f"Documentos por Vencer - {d['placa']}",
                "nivel": "Critico",
                "descripcion": texto
            })

        # 3. Alertas de Mantenimiento (Internas)
        mantenimientos = AlertaRepositorySA.obtener_mantenimientos_proximos()
        for m in mantenimientos:
            faltan = m['proximo_aceite'] - m['kilometraje']
            alertas["internas"].append({
                "titulo": f"Cambio de Aceite - {m['placa']}",
                "nivel": "Advertencia",
                "descripcion": f"Faltan {faltan:,.0f} km para el proximo cambio de aceite. (Actual: {m['kilometraje']})"
            })

        return alertas


# =====================================================================
# SERVICIO DE GASTOS Y CAJA MENOR
# =====================================================================

class GastoService:

    @staticmethod
    def listar_recientes() -> List[Dict]:
        return GastoRepositorySA.obtener_todos(200)

    @staticmethod
    def listar_por_placa(placa: str) -> List[Dict]:                    # NUEVO
        """Obtiene todos los gastos vinculados a un vehiculo."""
        placa = validar_placa(placa)
        return GastoRepositorySA.obtener_por_placa(placa)

    @staticmethod
    def registrar(datos: dict) -> int:
        requerir(datos.get("fecha"), "Fecha del Gasto")
        requerir(datos.get("categoria"), "Categoria")
        requerir(datos.get("descripcion"), "Descripcion")
        requerir(datos.get("monto"), "Monto")

        monto = float(datos["monto"])
        if monto <= 0:
            raise ValidacionError("El monto del gasto debe ser mayor a cero.")

        # Validar placa si viene (es opcional)
        placa_gasto = datos.get("placa")
        if placa_gasto:
            placa_gasto = validar_placa(placa_gasto)

        # Validar con Pydantic
        try:
            gasto_validado = GastoCreate(
                placa=placa_gasto,                                       # NUEVO
                fecha=datos["fecha"],
                categoria=datos["categoria"],
                descripcion=datos["descripcion"],
                monto=monto,
                comprobante=datos.get("comprobante"),
                usuario=datos.get("usuario", "Sistema"),
            )
        except Exception as e:
            raise ValidacionError(f"Datos de gasto invalidos: {str(e)}")

        id_gasto = GastoRepositorySA.insertar(gasto_validado)
        audit.info("Gasto de $%s registrado en categoria '%s' placa=%s",
                   monto, datos["categoria"], placa_gasto or 'N/A')

        return id_gasto


# =====================================================================
# SERVICIO DE INFORMES GERENCIALES
# =====================================================================

class InformeService:

    @staticmethod
    def balance_mensual_real() -> List[Dict]:
        resultados = InformeRepositorySA.obtener_balance_consolidado()

        balance_procesado = []
        for r in resultados:
            ingresos = float(r.get('ingresos') or 0)
            taller = float(r.get('egresos_taller') or 0)
            caja = float(r.get('gastos_caja') or 0)

            utilidad = ingresos - (taller + caja)

            balance_procesado.append({
                "mes": r.get('mes', 'Desconocido'),
                "ingresos": ingresos,
                "taller": taller,
                "caja_menor": caja,
                "utilidad": utilidad
            })

        return balance_procesado
