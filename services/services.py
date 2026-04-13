"""
services.py — Capa de lógica de negocio con SQLAlchemy y Pydantic

Actualizada para usar el nuevo sistema con SQLAlchemy 2.0 y validación Pydantic.
"""
import datetime
import os
import shutil
import subprocess
from typing import List, Dict, Optional
from decimal import Decimal

from core.config import (
    BACKUP_DIR, DB_PATH, BACKUP_MAX_COPIES, DB_ENGINE, DB_MYSQL,
    DIAS_ALERTA_SOAT, DIAS_ALERTA_TECNICO, KM_ALERTA_ACEITE_PREV,
)
from core.exceptions import (
    VehiculoNoDisponible, RentaYaCerrada, ClienteEnListaNegra,
    ValidacionError, NegocioError, CredencialesInvalidas,
)
from core.logger import get_logger, get_audit_logger
from core.security import SecurityManager, SessionManager
from core.validators import validar_placa, validar_documento, parsear_fecha, requerir
from core.schemas import (
    AutoCreate, RentaCreate, RentaCierre, ClienteCreate,
    UsuarioCreate, LoginRequest,
)
from repositories.repositories_sa import (
    AutoRepositorySA,
    ClienteRepositorySA,
    RentaRepositorySA,
    UsuarioRepositorySA,
)

log = get_logger(__name__)
audit = get_audit_logger()


# ═══════════════════════════════════════════════════════════════════════════
# SERVICIO DE VEHÍCULOS
# ═══════════════════════════════════════════════════════════════════════════

class AutoService:

    @staticmethod
    def listar() -> List[Dict]:
        return AutoRepositorySA.obtener_todos()

    @staticmethod
    def listar_disponibles() -> List[Dict]:
        return AutoRepositorySA.obtener_disponibles()

    @staticmethod
    def obtener(placa: str) -> Dict:
        placa = validar_placa(placa)
        auto = AutoRepositorySA.obtener_por_placa(placa)
        if not auto:
            raise NegocioError(f"Vehículo {placa} no encontrado.")
        return auto

    @staticmethod
    def guardar(datos: dict) -> None:
        # Validar placa primero
        placa = validar_placa(datos.get("placa", ""))
        datos["placa"] = placa
        
        # Validar con Pydantic
        try:
            auto_validado = AutoCreate(**datos)
        except Exception as e:
            raise ValidacionError(f"Datos de vehículo inválidos: {str(e)}")
        
        if AutoRepositorySA.existe(placa):
            from core.schemas import AutoUpdate
            update_data = AutoUpdate(placa=placa, **datos)
            AutoRepositorySA.actualizar(update_data)
            audit.info("Auto actualizado: %s por usuario del sistema", placa)
        else:
            AutoRepositorySA.insertar(auto_validado)
            audit.info("Auto creado: %s", placa)

    @staticmethod
    def obtener_alertas() -> List[Dict]:
        alertas: List[Dict] = []
        hoy = datetime.date.today()
        
        for alerta in AutoRepositorySA.obtener_alertas_flota():
            tipo = alerta.get('tipo')
            
            if tipo == 'Aceite':
                km_act = alerta.get('km_actual', 0)
                km_prox = alerta.get('km_proximo', 0)
                estado = "CRÍTICO" if km_act >= km_prox else "Pronto"
                alertas.append({
                    "placa": alerta['placa'],
                    "tipo": "Aceite",
                    "detalle": f"{km_act:,.0f}/{km_prox:,.0f} km",
                    "estado": estado,
                })
            elif tipo in ['SOAT', 'Tecno-mecánica']:
                dias = alerta.get('dias_restantes', 0)
                if dias < 0:
                    estado = "VENCIDO"
                else:
                    estado = f"{dias} días"
                
                doc_tipo = tipo.replace('-mecánica', '').replace('Tecno', 'Tecno')
                alertas.append({
                    "placa": alerta['placa'],
                    "tipo": doc_tipo,
                    "detalle": str(alerta.get('vencimiento', '')),
                    "estado": estado,
                })
        
        return alertas


# ═══════════════════════════════════════════════════════════════════════════
# SERVICIO DE RENTAS
# ═══════════════════════════════════════════════════════════════════════════

class RentaService:

    @staticmethod
    def crear(datos: dict) -> int:
        placa = validar_placa(datos.get("placa", ""))
        auto = AutoRepositorySA.obtener_por_placa(placa)
        
        if not auto:
            raise NegocioError(f"Vehículo {placa} no encontrado.")
        
        if auto.get("estado", "").upper() != "DISPONIBLE":
            raise VehiculoNoDisponible(placa)
        
        if datos.get("estado_cliente") == "Lista Negra":
            raise ClienteEnListaNegra()
        
        # Calcular total si no viene
        if not datos.get("total"):
            datos["total"] = RentaService._calcular_total(datos)
        
        datos["placa"] = placa
        
        # Validar con Pydantic
        try:
            renta_validada = RentaCreate(**datos)
        except Exception as e:
            raise ValidacionError(f"Datos de renta inválidos: {str(e)}")
        
        id_renta = RentaRepositorySA.insertar(renta_validada)
        AutoRepositorySA.cambiar_estado(placa, "Rentado")
        
        audit.info("Renta creada: id=%s, placa=%s, cliente=%s",
                   id_renta, placa, datos.get("nombre_cliente"))
        return id_renta

    @staticmethod
    def cerrar(id_renta: int, datos_cierre: dict) -> float:
        renta = RentaRepositorySA.obtener_por_id(id_renta)
        
        if renta.get("estado") == "Finalizado":
            raise RentaYaCerrada()
        
        gran_total = RentaService._calcular_total_cierre(renta, datos_cierre)
        datos_cierre["total"] = gran_total
        
        # Crear objeto Pydantic para cierre
        try:
            cierre_validado = RentaCierre(**datos_cierre)
        except Exception as e:
            raise ValidacionError(f"Datos de cierre inválidos: {str(e)}")
        
        RentaRepositorySA.cerrar_renta(id_renta, cierre_validado)
        AutoRepositorySA.cambiar_estado(
            renta["placa"], "Disponible",
            kilometraje=datos_cierre.get("km_final_float"),
        )
        
        audit.info("Renta cerrada: id=%s, total=%.0f, placa=%s",
                   id_renta, gran_total, renta["placa"])
        return gran_total

    @staticmethod
    def _calcular_total(datos: dict) -> float:
        dias = int(datos.get("dias_calculados", 0))
        valor_dia = float(datos.get("valor_dia", 0))
        horas = int(datos.get("horas_extras", 0))
        valor_hora = float(datos.get("valor_hora_extra", 0))
        extras = sum(float(datos.get(c, 0)) for c in [
            "costo_lavado", "costo_silla", "costo_retorno",
            "costo_domicilio", "costo_cables", "costo_inversor",
        ])
        descuento = float(datos.get("descuento", 0))
        subtotal = dias * valor_dia + horas * valor_hora + extras - descuento
        impuestos = float(datos.get("impuestos", 0))
        return subtotal + impuestos

    @staticmethod
    def _calcular_total_cierre(renta: dict, datos_cierre: dict) -> float:
        fecha_pactada_str = str(renta.get("fecha_retorno", ""))[:10]
        fecha_real_str = datos_cierre.get("fecha_devolucion_real", "")[:10]
        try:
            fp = datetime.datetime.strptime(fecha_pactada_str, "%Y-%m-%d").date()
            fr = datetime.datetime.strptime(fecha_real_str, "%Y-%m-%d").date()
            dias_retraso = max(0, (fr - fp).days)
        except ValueError:
            dias_retraso = 0
        
        costo_retraso = dias_retraso * float(renta.get("valor_dia", 0))
        otros = float(datos_cierre.get("otros_cobros", 0))
        return float(renta.get("total", 0)) + costo_retraso + otros

    @staticmethod
    def obtener_activas() -> List[Dict]:
        return RentaRepositorySA.obtener_activas()

    @staticmethod
    def kpi_globales() -> Dict:
        return RentaRepositorySA.kpi_globales()

    @staticmethod
    def balance_mensual() -> List[Dict]:
        raw = RentaRepositorySA.balance_mensual()
        ingresos = raw["ingresos"]
        egresos = raw["egresos"]
        autos = raw["autos"]
        
        meses = sorted(set(list(ingresos.keys()) + list(egresos.keys())))
        balance = []
        
        for mes_str in meses:
            try:
                dt_mes = datetime.datetime.strptime(mes_str, "%Y-%m")
            except ValueError:
                continue
            
            fijos_mes = 0
            for a in autos:
                try:
                    dt_ing = datetime.datetime.strptime(str(a["fecha_real"])[:7], "%Y-%m")
                    if dt_ing <= dt_mes:
                        fijos_mes += float(a.get("costo_fijo_mensual", 0))
                except (ValueError, TypeError):
                    pass
            
            ing = float(ingresos.get(mes_str, 0) or 0)
            gas = float(egresos.get(mes_str, 0) or 0)
            balance.append({
                "mes": mes_str, "ingreso": ing, "egreso": gas,
                "fijos": fijos_mes, "utilidad": ing - gas - fijos_mes,
            })
        
        return balance

    @staticmethod
    def roi_flota() -> List[Dict]:
        from repositories.repositories_sa import MantenimientoRepositorySA
        
        autos = AutoRepositorySA.obtener_todos()
        reporte = []
        hoy = datetime.datetime.now()
        
        for a in autos:
            if a.get('estado') in ['Vendido', 'Baja']:
                continue
            
            placa = a["placa"]
            
            # Calcular ingresos por placa
            # (esto requeriría una consulta adicional, simplificado aquí)
            ing_info = {"total": 0, "prom_dia": 0}
            
            # Calcular gastos de mantenimiento
            gas = 0  # Simplificado
            
            # Calcular meses de antigüedad
            try:
                f_ing = datetime.datetime.strptime(str(a.get("fecha_ingreso", ""))[:10], "%Y-%m-%d")
                meses = max(1, (hoy.year - f_ing.year) * 12 + (hoy.month - f_ing.month))
            except (ValueError, TypeError):
                meses = 1
            
            costo_fijo_total = float(a.get("costo_fijo_mensual", 0)) * meses
            equilibrio = 0.0
            prom = ing_info.get("prom_dia", 0)
            costo_mes = float(a.get("costo_fijo_mensual", 0))
            
            if prom > 0 and costo_mes > 0:
                equilibrio = costo_mes / prom
            
            reporte.append({
                "placa": placa,
                "vehiculo": f"{a.get('marca', '')} {a.get('modelo', '')}",
                "ingresos": ing_info["total"],
                "mantenimiento": gas,
                "costos_fijos": costo_fijo_total,
                "utilidad": ing_info["total"] - gas - costo_fijo_total,
                "equilibrio": equilibrio,
            })
        
        return reporte

    @staticmethod
    def obtener(id_renta: int) -> Dict:
        return RentaRepositorySA.obtener_por_id(id_renta)

    @staticmethod
    def extender(id_renta: int, nueva_fecha: str, nueva_hora: str, 
                 nuevos_dias: int, nuevo_total: float, nuevo_saldo: float) -> None:
        RentaRepositorySA.extender(id_renta, nueva_fecha, nueva_hora, nuevos_dias, nuevo_total, nuevo_saldo)
        audit.info("Renta %s extendida hasta %s", id_renta, nueva_fecha)

    @staticmethod
    def cambiar_vehiculo(id_renta: int, placa_actual: str, km_actual: float, 
                         estado_actual: str, placa_nueva: str, motivo: str) -> None:
        # 1. Liberar auto anterior
        AutoRepositorySA.cambiar_estado(placa_actual, estado_actual, km_actual)
        # 2. Ocupar nuevo auto
        AutoRepositorySA.cambiar_estado(placa_nueva, "Rentado")
        # 3. Actualizar la renta
        nota = f"\n[CAMBIO VEHÍCULO: de {placa_actual} a {placa_nueva}. Motivo: {motivo}]"
        RentaRepositorySA.actualizar_placa(id_renta, placa_nueva, nota)
        audit.info("Cambio de vehículo renta %s: %s -> %s", id_renta, placa_actual, placa_nueva)

    @staticmethod
    def obtener_datos_documento(id_renta: int) -> Dict:
        return RentaRepositorySA.obtener_datos_documento(id_renta)

    @staticmethod
    def obtener_para_calendario(mes: int, anio: int) -> List[Dict]:
        """Obtiene las rentas activas y reservas confirmadas para el mes y año dados."""
        return RentaRepositorySA.obtener_para_calendario(mes, anio)


# ═══════════════════════════════════════════════════════════════════════════
# SERVICIO DE CLIENTES
# ═══════════════════════════════════════════════════════════════════════════

class ClienteService:

    @staticmethod
    def buscar(termino: str = "") -> List[Dict]:
        return ClienteRepositorySA.buscar(termino)

    @staticmethod
    def obtener(id_cliente: int) -> Dict:
        return ClienteRepositorySA.obtener_por_id(id_cliente)

    @staticmethod
    def guardar(datos: dict) -> None:
        # Validar documento si existe
        no_doc = datos.get("no_doc", "")
        tipo_doc = datos.get("tipo_doc", "Cédula")
        if no_doc:
            validar_documento(no_doc, tipo_doc)
        
        requerir(datos.get("nombres"), "Nombres")
        
        # Validar con Pydantic
        try:
            cliente_validado = ClienteCreate(**datos)
        except Exception as e:
            raise ValidacionError(f"Datos de cliente inválidos: {str(e)}")
        
        # Verificar si es actualización o creación
        cliente_id = datos.get("id")
        if cliente_id:
            from core.schemas import ClienteUpdate
            update_data = ClienteUpdate(id=cliente_id, **datos)
            ClienteRepositorySA.actualizar(update_data)
        else:
            ClienteRepositorySA.insertar(cliente_validado)
        
        audit.info("Cliente guardado: %s (%s)", datos.get("nombres"), datos.get("no_doc"))


# ═══════════════════════════════════════════════════════════════════════════
# SERVICIO DE AUTENTICACIÓN
# ═══════════════════════════════════════════════════════════════════════════

class AuthService:

    @staticmethod
    def login(username: str, password: str) -> dict:
        if not username or not password:
            raise CredencialesInvalidas()
        
        usuario = UsuarioRepositorySA.obtener_por_username(username)
        
        if not usuario or not SecurityManager.verify_password(usuario["password"], password):
            log.warning("Intento de login fallido: %s", username)
            audit.info("LOGIN FALLIDO: usuario=%s", username)
            raise CredencialesInvalidas()
        
        UsuarioRepositorySA.registrar_acceso(username)
        
        sid = SessionManager.create(
            usuario["id"], usuario["username"], usuario["rol"], usuario["nombre"]
        )
        
        log.info("Login exitoso: %s (rol=%s)", username, usuario["rol"])
        audit.info("LOGIN OK: usuario=%s, rol=%s", username, usuario["rol"])
        
        return {
            "success": True,
            "session_id": sid,
            "username": usuario["username"],
            "nombre": usuario["nombre"],
            "rol": usuario["rol"],
        }


# ═══════════════════════════════════════════════════════════════════════════
# SERVICIO DE BACKUPS
# ═══════════════════════════════════════════════════════════════════════════

class BackupService:

    @staticmethod
    def crear() -> tuple[bool, str]:
        """Crea backup de la base de datos (soporta MySQL y SQLite)."""
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            
            if DB_ENGINE == "mysql":
                # Backup de MySQL usando mysqldump
                nombre = f"Backup_Dinamo_{timestamp}.sql"
                destino = os.path.join(str(BACKUP_DIR), nombre)
                
                cfg = DB_MYSQL
                command = [
                    "mysqldump",
                    f"--host={cfg['host']}",
                    f"--port={cfg['port']}",
                    f"--user={cfg['user']}",
                    f"--password={cfg['password']}",
                    "--default-character-set=utf8mb4",
                    "--single-transaction",
                    "--routines",
                    "--triggers",
                    cfg['database'],
                ]
                
                # Ejecutar mysqldump
                with open(destino, 'w', encoding='utf-8') as f:
                    result = subprocess.run(
                        command,
                        stdout=f,
                        stderr=subprocess.PIPE,
                        timeout=120
                    )
                
                if result.returncode != 0:
                    error_msg = result.stderr.decode('utf-8', errors='ignore')
                    log.error("Error en mysqldump: %s", error_msg)
                    if os.path.exists(destino):
                        os.remove(destino)
                    return False, f"Error creando backup MySQL: {error_msg}"
                    
            else:
                # Backup de SQLite (copia de archivo)
                if not os.path.exists(DB_PATH):
                    return False, "Base de datos SQLite no encontrada."
                
                nombre = f"Backup_Dinamo_{timestamp}.db"
                destino = os.path.join(str(BACKUP_DIR), nombre)
                shutil.copy2(DB_PATH, destino)
            
            # Limpiar backups antiguos
            archivos = sorted(
                [os.path.join(str(BACKUP_DIR), f) for f in os.listdir(str(BACKUP_DIR))
                 if f.endswith((".db", ".sql"))],
                key=os.path.getmtime,
            )
            while len(archivos) > BACKUP_MAX_COPIES:
                os.remove(archivos.pop(0))
            
            log.info("Backup creado: %s", nombre)
            return True, f"Copia creada: {nombre}"
        except subprocess.TimeoutExpired:
            log.error("Timeout creando backup")
            return False, "Timeout creando backup"
        except Exception as e:
            log.error("Error creando backup: %s", e)
            return False, str(e)
