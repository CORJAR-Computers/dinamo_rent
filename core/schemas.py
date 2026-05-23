"""
schemas.py — Pydantic Schemas for Dinamo Rent ERP

This module provides data validation schemas using Pydantic v2.
Used for request/response validation in the service layer.

F1A Changes applied:
  - GastoBase/GastoCreate/GastoResponse: Agregado campo placa (FK a Auto)
  - ReservaUpdate: Nuevo schema para actualizacion parcial de reservas
  - ComparendoResponse: Agregado relaciones con renta/cliente
  - GastoResponse: Agregado updated_at

F1C Changes applied:
  - AutoUpdate: Agregado campo placa (identificador del registro a actualizar)
  - ClienteUpdate: Agregado campo id (identificador del registro a actualizar)
  - UsuarioUpdate: Agregado campo username (identificador del registro a actualizar)

Usage:
    from core.schemas import UsuarioCreate, AutoSchema, RentaCreate, etc.
"""
from datetime import date, time, datetime
from typing import Optional
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


# =====================================================================
# COMMON TYPES & VALIDATORS
# =====================================================================

class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    model_config = ConfigDict(str_strip_whitespace=True, use_enum_values=True)


# =====================================================================
# USUARIOS
# =====================================================================

class UsuarioBase(BaseSchema):
    username: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_]+$')
    nombre: Optional[str] = Field(None, max_length=100)
    rol: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=100)
    activo: bool = True


class UsuarioCreate(UsuarioBase):
    password_raw: str = Field(..., min_length=6, max_length=100)


class UsuarioUpdate(BaseSchema):
    username: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_]+$')
    nombre: Optional[str] = Field(None, max_length=100)
    rol: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=100)
    activo: Optional[bool] = None
    password_raw: Optional[str] = Field(None, min_length=6, max_length=100)


class UsuarioResponse(UsuarioBase):
    id: int
    ultimo_acceso: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# AUTOS
# =====================================================================

class AutoBase(BaseSchema):
    placa: str = Field(..., min_length=6, max_length=20, pattern=r'^[A-Z0-9]+$')
    marca: Optional[str] = Field(None, max_length=80)
    modelo: Optional[str] = Field(None, max_length=80)
    version: Optional[str] = Field(None, max_length=80)
    color: Optional[str] = Field(None, max_length=50)
    tipo: Optional[str] = Field(None, max_length=50)
    cilindraje: Optional[str] = Field(None, max_length=30)
    transmision: Optional[str] = Field(None, max_length=30)
    combustible: Optional[str] = Field(None, max_length=30)
    no_motor: Optional[str] = Field(None, max_length=80)
    no_chasis: Optional[str] = Field(None, max_length=80)
    propietario: Optional[str] = Field(None, max_length=150)
    estado: str = Field(default='Disponible', max_length=30)
    costo_fijo_mensual: Decimal = Field(default=Decimal('0.00'), ge=0)
    kilometraje: float = Field(default=0.0, ge=0)
    ubicacion: Optional[str] = Field(None, max_length=150)
    tipo_adquisicion: Optional[str] = Field(None, max_length=30)
    proximo_aceite: Optional[int] = Field(default=0, ge=0)
    proximo_frenos: Optional[int] = Field(default=0, ge=0)
    vencimiento_soat: Optional[date] = None
    vencimiento_tecnico: Optional[date] = None
    vencimiento_extintor: Optional[date] = None
    vencimiento_bateria: Optional[date] = None
    observaciones: Optional[str] = None
    fecha_ingreso: date = Field(default_factory=date.today)


class AutoCreate(AutoBase):
    pass


class AutoUpdate(BaseSchema):
    placa: str = Field(..., min_length=6, max_length=20, pattern=r'^[A-Z0-9]+$')
    marca: Optional[str] = Field(None, max_length=80)
    modelo: Optional[str] = Field(None, max_length=80)
    version: Optional[str] = Field(None, max_length=80)
    color: Optional[str] = Field(None, max_length=50)
    tipo: Optional[str] = Field(None, max_length=50)
    cilindraje: Optional[str] = Field(None, max_length=30)
    transmision: Optional[str] = Field(None, max_length=30)
    combustible: Optional[str] = Field(None, max_length=30)
    no_motor: Optional[str] = Field(None, max_length=80)
    no_chasis: Optional[str] = Field(None, max_length=80)
    propietario: Optional[str] = Field(None, max_length=150)
    estado: Optional[str] = Field(None, max_length=30)
    costo_fijo_mensual: Optional[Decimal] = Field(None, ge=0)
    kilometraje: Optional[float] = Field(None, ge=0)
    ubicacion: Optional[str] = Field(None, max_length=150)
    tipo_adquisicion: Optional[str] = Field(None, max_length=30)
    proximo_aceite: Optional[int] = Field(None, ge=0)
    proximo_frenos: Optional[int] = Field(None, ge=0)
    vencimiento_soat: Optional[date] = None
    vencimiento_tecnico: Optional[date] = None
    vencimiento_extintor: Optional[date] = None
    vencimiento_bateria: Optional[date] = None
    observaciones: Optional[str] = None


class AutoResponse(AutoBase):
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# CLIENTES
# =====================================================================

class ClienteBase(BaseSchema):
    tipo_doc: Optional[str] = Field(None, max_length=30)
    no_doc: Optional[str] = Field(None, max_length=30)
    nombres: Optional[str] = Field(None, max_length=100)
    apellidos: Optional[str] = Field(None, max_length=100)
    nombre_completo: str = Field(default='', max_length=200)
    celular: Optional[str] = Field(None, max_length=20)
    celular2: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=150)
    ciudad: Optional[str] = Field(None, max_length=100)
    estado_region: Optional[str] = Field(None, max_length=100)
    pais: Optional[str] = Field(None, max_length=80)
    nacionalidad: Optional[str] = Field(None, max_length=80)
    dir_residencia: Optional[str] = Field(None, max_length=200)
    dir_temporal: Optional[str] = Field(None, max_length=200)
    hotel: Optional[str] = Field(None, max_length=150)
    habitacion: Optional[str] = Field(None, max_length=30)
    no_licencia: Optional[str] = Field(None, max_length=50)
    tipo_licencia: Optional[str] = Field(None, max_length=50)
    vencimiento_licencia: Optional[date] = None
    estado: str = Field(default='Activo', max_length=30)

    @model_validator(mode='after')
    def generar_nombre_completo(self):
        if not self.nombre_completo and self.nombres:
            nombres = self.nombres or ''
            apellidos = self.apellidos or ''
            self.nombre_completo = f"{nombres} {apellidos}".strip()
        return self


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(BaseSchema):
    id: int = Field(..., gt=0)
    tipo_doc: Optional[str] = Field(None, max_length=30)
    no_doc: Optional[str] = Field(None, max_length=30)
    nombres: Optional[str] = Field(None, max_length=100)
    apellidos: Optional[str] = Field(None, max_length=100)
    nombre_completo: Optional[str] = Field(None, max_length=200)
    celular: Optional[str] = Field(None, max_length=20)
    celular2: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=150)
    ciudad: Optional[str] = Field(None, max_length=100)
    estado_region: Optional[str] = Field(None, max_length=100)
    pais: Optional[str] = Field(None, max_length=80)
    nacionalidad: Optional[str] = Field(None, max_length=80)
    dir_residencia: Optional[str] = Field(None, max_length=200)
    dir_temporal: Optional[str] = Field(None, max_length=200)
    hotel: Optional[str] = Field(None, max_length=150)
    habitacion: Optional[str] = Field(None, max_length=30)
    no_licencia: Optional[str] = Field(None, max_length=50)
    tipo_licencia: Optional[str] = Field(None, max_length=50)
    vencimiento_licencia: Optional[date] = None
    estado: Optional[str] = Field(None, max_length=30)


class ClienteResponse(ClienteBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# RENTAS
# =====================================================================

class RentaBase(BaseSchema):
    placa: str = Field(..., min_length=6, max_length=20)
    id_cliente: Optional[int] = Field(None, gt=0)
    nombre_cliente: Optional[str] = Field(None, max_length=200)
    no_licencia: Optional[str] = Field(None, max_length=50)
    nacionalidad: Optional[str] = Field(None, max_length=80)
    fecha_recogida: date
    hora_recogida: time
    ubicacion_recogida: Optional[str] = Field('Oficina', max_length=200)
    fecha_retorno: date
    hora_retorno: time
    ubicacion_retorno: Optional[str] = Field('Oficina', max_length=200)
    dias_calculados: Optional[int] = Field(default=0, ge=0)
    horas_extras: Optional[int] = Field(default=0, ge=0)
    valor_dia: Decimal = Field(default=Decimal('0.00'), ge=0)
    valor_hora_extra: Decimal = Field(default=Decimal('0.00'), ge=0)
    valor_dia_extra: Decimal = Field(default=Decimal('0.00'), ge=0)
    costo_lavado: Decimal = Field(default=Decimal('0.00'), ge=0)
    costo_silla: Decimal = Field(default=Decimal('0.00'), ge=0)
    costo_retorno: Decimal = Field(default=Decimal('0.00'), ge=0)
    costo_domicilio: Decimal = Field(default=Decimal('0.00'), ge=0)
    costo_cables: Decimal = Field(default=Decimal('0.00'), ge=0)
    costo_inversor: Decimal = Field(default=Decimal('0.00'), ge=0)
    descuento: Decimal = Field(default=Decimal('0.00'), ge=0)
    subtotal: Decimal = Field(default=Decimal('0.00'), ge=0)
    impuestos: Decimal = Field(default=Decimal('0.00'), ge=0)
    total: Decimal = Field(default=Decimal('0.00'), ge=0)
    abono: Decimal = Field(default=Decimal('0.00'), ge=0)
    saldo_pendiente: Decimal = Field(default=Decimal('0.00'), ge=0)
    estado: str = Field(default='Activo', max_length=30)
    observaciones: Optional[str] = None
    km_salida: Optional[float] = Field(default=0.0, ge=0)
    tanque_salida: Optional[str] = Field(default='Lleno', max_length=20)
    id_reserva: Optional[int] = None


class RentaCreate(RentaBase):
    pass


class RentaCierre(BaseSchema):
    fecha_devolucion_real: date
    hora_devolucion_real: time
    km_final: Optional[str] = None
    tanque_final: Optional[str] = Field(None, max_length=20)
    nota_cierre: str = Field(default='', max_length=500)
    otros_cobros: Decimal = Field(default=Decimal('0.00'), ge=0)


class RentaUpdate(BaseSchema):
    fecha_retorno: Optional[date] = None
    hora_retorno: Optional[time] = None
    dias_calculados: Optional[int] = Field(None, ge=0)
    total: Optional[Decimal] = Field(None, ge=0)
    saldo_pendiente: Optional[Decimal] = Field(None, ge=0)
    observaciones: Optional[str] = None


class RentaResponse(RentaBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# RESERVAS
# =====================================================================

class ReservaBase(BaseSchema):
    id_cliente: Optional[int] = Field(None, gt=0)
    nombre_cliente: Optional[str] = Field(None, max_length=200)
    nacionalidad: Optional[str] = Field(None, max_length=80)
    categoria_vehiculo: Optional[str] = Field(None, max_length=50)
    placa_asignada: Optional[str] = Field(None, min_length=6, max_length=20)
    fecha_recogida: date
    hora_recogida: time
    ubicacion_recogida: Optional[str] = Field('Oficina', max_length=200)
    fecha_retorno: date
    hora_retorno: time
    ubicacion_retorno: Optional[str] = Field('Oficina', max_length=200)
    dias_calculados: Optional[int] = Field(default=0, ge=0)
    horas_extras: Optional[int] = Field(default=0, ge=0)
    valor_dia: Decimal = Field(default=Decimal('0.00'), ge=0)
    valor_hora_adic: Decimal = Field(default=Decimal('0.00'), ge=0)
    abono: Decimal = Field(default=Decimal('0.00'), ge=0)
    total: Decimal = Field(default=Decimal('0.00'), ge=0)
    observaciones: Optional[str] = None
    estado: str = Field(default='Confirmada', max_length=30)


class ReservaCreate(ReservaBase):
    pass


class ReservaUpdate(BaseSchema):
    """Schema para actualizacion parcial de reservas."""
    id_cliente: Optional[int] = Field(None, gt=0)
    nombre_cliente: Optional[str] = Field(None, max_length=200)
    nacionalidad: Optional[str] = Field(None, max_length=80)
    categoria_vehiculo: Optional[str] = Field(None, max_length=50)
    placa_asignada: Optional[str] = Field(None, min_length=6, max_length=20)
    fecha_recogida: Optional[date] = None
    hora_recogida: Optional[time] = None
    ubicacion_recogida: Optional[str] = Field(None, max_length=200)
    fecha_retorno: Optional[date] = None
    hora_retorno: Optional[time] = None
    ubicacion_retorno: Optional[str] = Field(None, max_length=200)
    dias_calculados: Optional[int] = Field(None, ge=0)
    horas_extras: Optional[int] = Field(None, ge=0)
    valor_dia: Optional[Decimal] = Field(None, ge=0)
    valor_hora_adic: Optional[Decimal] = Field(None, ge=0)
    abono: Optional[Decimal] = Field(None, ge=0)
    total: Optional[Decimal] = Field(None, ge=0)
    observaciones: Optional[str] = None
    estado: Optional[str] = Field(None, max_length=30)


class ReservaResponse(ReservaBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# MANTENIMIENTO
# =====================================================================

class MantenimientoBase(BaseSchema):
    placa: str = Field(..., min_length=6, max_length=20)
    pieza_varias_tipo: Optional[str] = Field(None, max_length=80)
    pieza_varias_fecha: Optional[date] = None
    pieza_varias_desc: Optional[str] = Field(None, max_length=250)
    pieza_varias_obs: Optional[str] = None
    cost_varios: Decimal = Field(default=Decimal('0.00'), ge=0)
    km_proximo_cambio_aceite: Optional[int] = Field(default=0, ge=0)
    total_mantenimiento: Decimal = Field(default=Decimal('0.00'), ge=0)


class MantenimientoCreate(MantenimientoBase):
    pass


class MantenimientoResponse(MantenimientoBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# COMPARENDOS
# =====================================================================

class ComparendoBase(BaseSchema):
    placa: str = Field(..., min_length=6, max_length=20)
    fecha_infraccion: date
    hora_infraccion: time
    monto: Decimal = Field(..., ge=0)
    id_renta: Optional[int] = None
    id_cliente: Optional[int] = None
    estado: str = Field(default='Pendiente', max_length=20)
    observaciones: Optional[str] = None


class ComparendoCreate(ComparendoBase):
    pass


class ComparendoUpdate(BaseSchema):
    estado: Optional[str] = Field(None, max_length=20)
    observaciones: Optional[str] = None


class ComparendoResponse(ComparendoBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# PAGOS
# =====================================================================

class PagoBase(BaseSchema):
    id_renta: int = Field(..., gt=0)
    monto: Decimal = Field(..., gt=0)
    metodo_pago: str = Field(..., max_length=50)
    concepto: str = Field(..., max_length=80)
    observaciones: Optional[str] = None
    usuario: Optional[str] = Field(None, max_length=50)


class PagoCreate(PagoBase):
    pass


class PagoResponse(PagoBase):
    id: int
    fecha: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# GASTOS
# =====================================================================

class GastoBase(BaseSchema):
    placa: Optional[str] = Field(None, min_length=6, max_length=20)
    fecha: date
    categoria: str = Field(..., max_length=50)
    descripcion: str = Field(..., max_length=200)
    monto: Decimal = Field(..., gt=0)
    comprobante: Optional[str] = Field(None, max_length=50)
    usuario: Optional[str] = Field('Sistema', max_length=50)


class GastoCreate(GastoBase):
    pass


class GastoResponse(GastoBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# INSPECCIONES
# =====================================================================

class InspeccionBase(BaseSchema):
    id_renta: int = Field(..., gt=0)
    tipo: str = Field(..., max_length=30)
    kilometraje: float = Field(..., ge=0)
    nivel_gasolina: str = Field(..., max_length=20)
    limpieza: Optional[str] = Field('Limpio', max_length=50)
    tiene_repuesto: Optional[bool] = True
    tiene_gato_cruceta: Optional[bool] = True
    tiene_kit_carretera: Optional[bool] = True
    tiene_documentos: Optional[bool] = True
    danos_carroceria: Optional[str] = None
    observaciones: Optional[str] = None


class InspeccionCreate(InspeccionBase):
    pass


class InspeccionResponse(InspeccionBase):
    id: int
    fecha: datetime

    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# LOGIN & AUTH
# =====================================================================

class LoginRequest(BaseSchema):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=1, max_length=100)


class LoginResponse(BaseSchema):
    success: bool
    session_id: str
    username: str
    nombre: str
    rol: str


# =====================================================================
# COMPOSITE RESPONSE SCHEMAS (F1E)
# =====================================================================
# Schemas para tipar los retornos de los servicios compuestos.
# Los servicios individuales (Auto, Cliente, etc.) ya usan sus *Response
# propios. Estos son para Dashboard, Financial, RentaDocumento y
# ComparendoRegistro que retornan estructuras compuestas.

class RentaDetalleResponse(RentaBase):
    """Respuesta extendida de Renta con campos de cierre."""
    id: int
    fecha_devolucion_real: Optional[date] = None
    hora_devolucion_real: Optional[time] = None
    km_final: Optional[str] = None
    tanque_final: Optional[str] = None
    created_at: datetime

    # Datos del auto (si relación existe)
    auto_marca: Optional[str] = None
    auto_modelo: Optional[str] = None
    auto_color: Optional[str] = None
    auto_tipo: Optional[str] = None
    auto_transmision: Optional[str] = None
    auto_combustible: Optional[str] = None

    # Datos del cliente (si relación existe)
    cliente_celular: Optional[str] = None
    cliente_email: Optional[str] = None
    cliente_direccion: Optional[str] = None
    cliente_no_licencia: Optional[str] = None
    cliente_tipo_licencia: Optional[str] = None


class KpiGlobalesResponse(BaseSchema):
    """Respuesta de KPIs globales del Dashboard."""
    rentas_activas: int = 0
    autos_disponibles: int = 0
    autos_rentados: int = 0
    autos_mantenimiento: int = 0
    total_flota: int = 0
    ocupacion_flota: float = 0.0
    ingresos_mes: float = 0.0
    pagos_pendientes: float = 0.0


class ResumenFinancieroResponse(BaseSchema):
    """Respuesta del resumen financiero mensual."""
    mes: str
    ingresos_mes: float = 0.0
    egresos_taller_mes: float = 0.0
    gastos_caja_mes: float = 0.0
    utilidad_mes: float = 0.0


class RoiVehiculoResponse(BaseSchema):
    """Respuesta del ROI de un vehículo individual."""
    placa: str
    vehiculo: str
    ingresos: float = 0.0
    mantenimiento: float = 0.0
    gastos: float = 0.0
    costos_fijos: float = 0.0
    utilidad: float = 0.0
    roi_pct: float = 0.0
    equilibrio_dias: float = 0.0


class BalanceMensualItemResponse(BaseSchema):
    """Respuesta de un item del balance mensual."""
    mes: str
    ingresos: float = 0.0
    taller: float = 0.0
    caja_menor: float = 0.0
    utilidad: float = 0.0


class AlertaClienteResponse(BaseSchema):
    """Respuesta de alerta para clientes (rentas por vencer)."""
    titulo: str
    cliente: str
    celular: Optional[str] = None
    fecha: str
    mensaje_whatsapp: str


class AlertaInternaResponse(BaseSchema):
    """Respuesta de alerta interna (documentos, mantenimiento)."""
    titulo: str
    nivel: str = "Advertencia"
    descripcion: str


class AlertasResponse(BaseSchema):
    """Respuesta consolidada de todas las alertas."""
    clientes: list[AlertaClienteResponse] = []
    internas: list[AlertaInternaResponse] = []


class CalendarioItemResponse(BaseSchema):
    """Respuesta de item del calendario (renta o reserva)."""
    tipo: str                          # 'renta' o 'reserva'
    id: int
    placa: Optional[str] = None
    cliente: Optional[str] = None
    fecha_recogida: Optional[date] = None
    fecha_retorno: Optional[date] = None
    estado: str


class ComparendoRegistroResponse(BaseSchema):
    """Respuesta del registro de comparendo con vinculación automática."""
    id_comparendo: int
    vinculado: bool
    id_renta: Optional[int] = None
    id_cliente: Optional[int] = None
