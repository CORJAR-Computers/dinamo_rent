"""
models.py — SQLAlchemy Models for Dinamo Rent ERP

This module defines all database tables using SQLAlchemy's declarative base.
Compatible with both MySQL and SQLite through dialect abstraction.

Mejoras aplicadas:
  - CODE-03: Campos monetarios usan Decimal en vez de float
  - CODE-04: marca, modelo, tipo en Auto; nombres en Cliente ahora son obligatorios
  - CODE-05: Agregado helper estático para calcular nombre_completo
  - DB-02: Agregados índices compuestos para consultas frecuentes
  - CODE-08: Limpiados comentarios de versión de docstrings

Usage:
    from core.models import Base, Usuario, Auto, Cliente, Renta, etc.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Integer,
    String,
    Float,
    DECIMAL,
    Date,
    Time,
    DateTime,
    Text,
    ForeignKey,
    Index,
    SmallInteger,
    Computed,
)
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from core.security_crypto import EncryptedString, EncryptedText


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


# =====================================================================
# USUARIOS
# =====================================================================


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = {"mysql_collate": "utf8mb4_unicode_ci"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre: Mapped[Optional[str]] = mapped_column(String(100))
    rol: Mapped[Optional[str]] = mapped_column(String(50))
    email: Mapped[Optional[str]] = mapped_column(String(100))
    activo: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="1")
    intentos_fallidos: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    debe_cambiar_password: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default="0"
    )
    ultimo_acceso: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self):
        return f"<Usuario {self.username} ({self.rol})>"


# =====================================================================
# AUTOS
# =====================================================================


class Auto(Base):
    __tablename__ = "autos"
    __table_args__ = (
        Index("ix_autos_estado_tipo", "estado", "tipo"),
        {"mysql_collate": "utf8mb4_unicode_ci"},
    )

    placa: Mapped[str] = mapped_column(String(20), primary_key=True, nullable=False)
    marca: Mapped[str] = mapped_column(String(80), nullable=False, server_default="")
    modelo: Mapped[str] = mapped_column(String(80), nullable=False, server_default="")
    version: Mapped[Optional[str]] = mapped_column(String(80))
    color: Mapped[Optional[str]] = mapped_column(String(50))
    tipo: Mapped[str] = mapped_column(String(50), nullable=False, server_default="", index=True)
    cilindraje: Mapped[Optional[str]] = mapped_column(String(30))
    transmision: Mapped[Optional[str]] = mapped_column(String(30))
    combustible: Mapped[Optional[str]] = mapped_column(String(30))
    no_motor: Mapped[Optional[str]] = mapped_column(String(80))
    no_chasis: Mapped[Optional[str]] = mapped_column(String(80))
    propietario: Mapped[Optional[str]] = mapped_column(String(150))
    estado: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="Disponible", index=True
    )
    costo_fijo_mensual: Mapped[Decimal] = mapped_column(
        DECIMAL(12, 2), nullable=False, server_default="0.00"
    )
    kilometraje: Mapped[float] = mapped_column(Float, nullable=False, server_default="0.00")
    ubicacion: Mapped[Optional[str]] = mapped_column(String(150))
    tipo_adquisicion: Mapped[Optional[str]] = mapped_column(String(30))
    proximo_aceite: Mapped[Optional[int]] = mapped_column(Integer, server_default="0")
    proximo_frenos: Mapped[Optional[int]] = mapped_column(Integer, server_default="0")
    vencimiento_soat: Mapped[Optional[datetime]] = mapped_column(Date)
    vencimiento_tecnico: Mapped[Optional[datetime]] = mapped_column(Date)
    vencimiento_extintor: Mapped[Optional[datetime]] = mapped_column(Date)
    vencimiento_bateria: Mapped[Optional[datetime]] = mapped_column(Date)
    observaciones: Mapped[Optional[str]] = mapped_column(Text)
    fecha_ingreso: Mapped[datetime] = mapped_column(Date, nullable=False, default=datetime.today)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    rentas = relationship("Renta", back_populates="auto_rel")
    mantenimientos = relationship("MantenimientoVehiculo", back_populates="auto_rel")
    comparendos = relationship("Comparendo", back_populates="auto_rel")
    reservas = relationship("Reserva", back_populates="auto_rel")
    gastos = relationship("Gasto", back_populates="auto_rel")

    def __repr__(self):
        return f"<Auto {self.placa} - {self.marca} {self.modelo}>"


# =====================================================================
# CLIENTES
# =====================================================================


class Cliente(Base):
    __tablename__ = "clientes"
    __table_args__ = (
        Index("ix_clientes_estado_nombre", "estado", "nombre_completo"),
        {"mysql_collate": "utf8mb4_unicode_ci"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tipo_doc: Mapped[Optional[str]] = mapped_column(String(30))
    no_doc: Mapped[Optional[str]] = mapped_column(String(30), unique=True, index=True)
    nombres: Mapped[str] = mapped_column(String(100), nullable=False, server_default="")
    apellidos: Mapped[Optional[str]] = mapped_column(String(100))
    nombre_completo: Mapped[str] = mapped_column(
        String(200), nullable=False, server_default="", index=True
    )
    celular: Mapped[Optional[str]] = mapped_column(EncryptedString(255))
    celular2: Mapped[Optional[str]] = mapped_column(EncryptedString(255))
    email: Mapped[Optional[str]] = mapped_column(EncryptedString(255))
    ciudad: Mapped[Optional[str]] = mapped_column(String(100))
    estado_region: Mapped[Optional[str]] = mapped_column(String(100))
    pais: Mapped[Optional[str]] = mapped_column(String(80))
    nacionalidad: Mapped[Optional[str]] = mapped_column(String(80))
    dir_residencia: Mapped[Optional[str]] = mapped_column(EncryptedText)
    dir_temporal: Mapped[Optional[str]] = mapped_column(EncryptedText)
    hotel: Mapped[Optional[str]] = mapped_column(String(150))
    habitacion: Mapped[Optional[str]] = mapped_column(String(30))
    no_licencia: Mapped[Optional[str]] = mapped_column(EncryptedString(255))
    tipo_licencia: Mapped[Optional[str]] = mapped_column(String(50))
    vencimiento_licencia: Mapped[Optional[datetime]] = mapped_column(Date)
    estado: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="Activo", index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    rentas = relationship("Renta", back_populates="cliente_rel")
    reservas = relationship("Reserva", back_populates="cliente_rel")
    comparendos = relationship("Comparendo", back_populates="cliente_rel")

    @staticmethod
    def calcular_nombre_completo(nombres: str, apellidos: str = "") -> str:
        """Calcula nombre completo a partir de nombres y apellidos.

        CODE-05: Mecanismo centralizado para mantener nombre_completo sincronizado.
        Los servicios deben llamar a este método antes de insertar/actualizar.
        """
        partes = []
        if nombres and nombres.strip():
            partes.append(nombres.strip())
        if apellidos and apellidos.strip():
            partes.append(apellidos.strip())
        return " ".join(partes)

    def __repr__(self):
        return f"<Cliente {self.nombre_completo} ({self.no_doc})>"


# =====================================================================
# RENTAS
# =====================================================================


class Renta(Base):
    __tablename__ = "rentas"
    __table_args__ = (
        Index("idx_rentas_estado", "estado"),
        Index("idx_rentas_fechas", "fecha_recogida", "fecha_retorno"),
        Index("idx_rentas_estado_fecha_retorno", "estado", "fecha_retorno"),
        Index("idx_rentas_estado_placa", "estado", "placa"),
        {"mysql_collate": "utf8mb4_unicode_ci"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    placa: Mapped[Optional[str]] = mapped_column(
        String(20), ForeignKey("autos.placa", onupdate="CASCADE"), index=True
    )
    id_cliente: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("clientes.id"), index=True
    )
    nombre_cliente: Mapped[Optional[str]] = mapped_column(String(200))
    no_licencia: Mapped[Optional[str]] = mapped_column(String(50))
    nacionalidad: Mapped[Optional[str]] = mapped_column(String(80))
    fecha_recogida: Mapped[Optional[datetime]] = mapped_column(Date)
    hora_recogida: Mapped[Optional[datetime]] = mapped_column(Time)
    ubicacion_recogida: Mapped[Optional[str]] = mapped_column(String(200))
    fecha_retorno: Mapped[Optional[datetime]] = mapped_column(Date)
    hora_retorno: Mapped[Optional[datetime]] = mapped_column(Time)
    ubicacion_retorno: Mapped[Optional[str]] = mapped_column(String(200))
    dias_calculados: Mapped[Optional[int]] = mapped_column(Integer, server_default="0")
    horas_extras: Mapped[Optional[int]] = mapped_column(Integer, server_default="0")
    valor_dia: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), server_default="0.00")
    valor_hora_extra: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), server_default="0.00")
    valor_dia_extra: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), server_default="0.00")
    costo_lavado: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), server_default="0.00")
    costo_silla: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), server_default="0.00")
    costo_retorno: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), server_default="0.00")
    costo_domicilio: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), server_default="0.00")
    costo_cables: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), server_default="0.00")
    costo_inversor: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), server_default="0.00")
    descuento: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), server_default="0.00")
    subtotal: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), server_default="0.00")
    impuestos: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), server_default="0.00")
    total: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), server_default="0.00")
    abono: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), server_default="0.00")
    saldo_pendiente: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), server_default="0.00")
    estado: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="Activo", index=True
    )
    observaciones: Mapped[Optional[str]] = mapped_column(Text)
    fecha_devolucion_real: Mapped[Optional[datetime]] = mapped_column(Date)
    hora_devolucion_real: Mapped[Optional[datetime]] = mapped_column(Time)
    km_final: Mapped[Optional[str]] = mapped_column(String(20))
    tanque_final: Mapped[Optional[str]] = mapped_column(String(20))
    km_salida: Mapped[float] = mapped_column(Float, server_default="0.00")
    tanque_salida: Mapped[Optional[str]] = mapped_column(String(20), server_default="Lleno")
    id_reserva: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("reservas.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # Relationships
    auto_rel = relationship("Auto", back_populates="rentas")
    cliente_rel = relationship("Cliente", back_populates="rentas")
    reserva_rel = relationship("Reserva", back_populates="rentas")
    pagos = relationship("Pago", back_populates="renta_rel")
    inspecciones = relationship("Inspeccion", back_populates="renta_rel")
    comparendos = relationship("Comparendo", back_populates="renta_rel")

    def __repr__(self):
        return f"<Renta {self.id} - {self.placa} ({self.estado})>"


# =====================================================================
# RESERVAS
# =====================================================================


class Reserva(Base):
    __tablename__ = "reservas"
    __table_args__ = (
        Index("ix_reservas_estado_fecha", "estado", "fecha_recogida"),
        {"mysql_collate": "utf8mb4_unicode_ci"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_cliente: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("clientes.id"))
    nombre_cliente: Mapped[Optional[str]] = mapped_column(String(200))
    nacionalidad: Mapped[Optional[str]] = mapped_column(String(80))
    categoria_vehiculo: Mapped[Optional[str]] = mapped_column(String(50))
    placa_asignada: Mapped[Optional[str]] = mapped_column(
        String(20), ForeignKey("autos.placa", ondelete="SET NULL"), nullable=True
    )
    fecha_recogida: Mapped[Optional[datetime]] = mapped_column(Date)
    hora_recogida: Mapped[Optional[datetime]] = mapped_column(Time)
    ubicacion_recogida: Mapped[Optional[str]] = mapped_column(String(200))
    fecha_retorno: Mapped[Optional[datetime]] = mapped_column(Date)
    hora_retorno: Mapped[Optional[datetime]] = mapped_column(Time)
    ubicacion_retorno: Mapped[Optional[str]] = mapped_column(String(200))
    dias_calculados: Mapped[Optional[int]] = mapped_column(Integer, server_default="0")
    horas_extras: Mapped[Optional[int]] = mapped_column(Integer, server_default="0")
    valor_dia: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), server_default="0.00")
    valor_hora_adic: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), server_default="0.00")
    abono: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), server_default="0.00")
    total: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), server_default="0.00")
    observaciones: Mapped[Optional[str]] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="Confirmada", index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    cliente_rel = relationship("Cliente", back_populates="reservas")
    auto_rel = relationship("Auto", back_populates="reservas")
    rentas = relationship("Renta", back_populates="reserva_rel")

    def __repr__(self):
        return f"<Reserva {self.id} - {self.nombre_cliente}>"


# =====================================================================
# MANTENIMIENTO VEHICULOS
# =====================================================================


class MantenimientoVehiculo(Base):
    __tablename__ = "mantenimiento_vehiculos"
    __table_args__ = (
        Index("ix_mantenimiento_placa_fecha", "placa", "pieza_varias_fecha"),
        {"mysql_collate": "utf8mb4_unicode_ci"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    placa: Mapped[Optional[str]] = mapped_column(
        String(20), ForeignKey("autos.placa", ondelete="CASCADE"), index=True
    )
    pieza_varias_tipo: Mapped[Optional[str]] = mapped_column(String(80))
    pieza_varias_fecha: Mapped[Optional[datetime]] = mapped_column(Date)
    pieza_varias_desc: Mapped[Optional[str]] = mapped_column(String(250))
    pieza_varias_obs: Mapped[Optional[str]] = mapped_column(Text)
    cost_varios: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), server_default="0.00")
    km_proximo_cambio_aceite: Mapped[Optional[int]] = mapped_column(Integer, server_default="0")
    total_mantenimiento: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), server_default="0.00")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    auto_rel = relationship("Auto", back_populates="mantenimientos")

    def __repr__(self):
        return f"<Mantenimiento {self.id} - {self.placa}>"


# =====================================================================
# CONFIGURACION
# =====================================================================


class Configuracion(Base):
    __tablename__ = "configuracion"
    __table_args__ = {"mysql_collate": "utf8mb4_unicode_ci"}

    clave: Mapped[str] = mapped_column(String(100), primary_key=True, nullable=False)
    valor: Mapped[Optional[str]] = mapped_column(Text)
    tipo: Mapped[Optional[str]] = mapped_column(String(30))

    def __repr__(self):
        return f"<Configuracion {self.clave}>"


# =====================================================================
# AUDITORIA
# =====================================================================


class Auditoria(Base):
    __tablename__ = "auditoria"
    __table_args__ = (
        Index("ix_auditoria_usuario_fecha", "usuario", "fecha"),
        {"mysql_collate": "utf8mb4_unicode_ci"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    accion: Mapped[Optional[str]] = mapped_column(String(100))
    mensaje: Mapped[Optional[str]] = mapped_column(Text)
    ip: Mapped[Optional[str]] = mapped_column(String(45))
    fecha: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), index=True
    )

    def __repr__(self):
        return f"<Auditoria {self.id} - {self.usuario}>"


# =====================================================================
# INSPECCIONES
# =====================================================================


class Inspeccion(Base):
    __tablename__ = "inspecciones"
    __table_args__ = {"mysql_collate": "utf8mb4_unicode_ci"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_renta: Mapped[int] = mapped_column(
        Integer, ForeignKey("rentas.id", ondelete="CASCADE"), nullable=False
    )
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    kilometraje: Mapped[float] = mapped_column(Float, nullable=False)
    nivel_gasolina: Mapped[str] = mapped_column(String(20), nullable=False)
    limpieza: Mapped[Optional[str]] = mapped_column(String(50), server_default="Limpio")
    tiene_repuesto: Mapped[Optional[int]] = mapped_column(SmallInteger, server_default="1")
    tiene_gato_cruceta: Mapped[Optional[int]] = mapped_column(SmallInteger, server_default="1")
    tiene_kit_carretera: Mapped[Optional[int]] = mapped_column(SmallInteger, server_default="1")
    tiene_documentos: Mapped[Optional[int]] = mapped_column(SmallInteger, server_default="1")
    danos_carroceria: Mapped[Optional[str]] = mapped_column(Text)
    observaciones: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    renta_rel = relationship("Renta", back_populates="inspecciones")

    def __repr__(self):
        return f"<Inspeccion {self.id} - Renta {self.id_renta}>"


# =====================================================================
# COMPARENDOS
# =====================================================================


class Comparendo(Base):
    __tablename__ = "comparendos"
    __table_args__ = (
        Index("ix_comparendos_placa_fecha", "placa", "fecha_infraccion"),
        {"mysql_collate": "utf8mb4_unicode_ci"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    placa: Mapped[str] = mapped_column(
        String(20), ForeignKey("autos.placa", ondelete="CASCADE"), nullable=False
    )
    fecha_infraccion: Mapped[datetime] = mapped_column(Date, nullable=False)
    hora_infraccion: Mapped[datetime] = mapped_column(Time, nullable=False)
    monto: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=False, server_default="0")
    id_renta: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("rentas.id", ondelete="SET NULL"), nullable=True
    )
    id_cliente: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("clientes.id", ondelete="SET NULL"), nullable=True
    )
    estado: Mapped[Optional[str]] = mapped_column(String(20), server_default="Pendiente")
    observaciones: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    auto_rel = relationship("Auto", back_populates="comparendos")
    renta_rel = relationship("Renta", back_populates="comparendos")
    cliente_rel = relationship("Cliente", back_populates="comparendos")

    def __repr__(self):
        return f"<Comparendo {self.id} - {self.placa}>"


# =====================================================================
# PAGOS
# =====================================================================


class Pago(Base):
    __tablename__ = "pagos"
    __table_args__ = (
        Index("ix_pagos_renta_fecha", "id_renta", "fecha"),
        {"mysql_collate": "utf8mb4_unicode_ci"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_renta: Mapped[int] = mapped_column(
        Integer, ForeignKey("rentas.id", ondelete="CASCADE"), nullable=False
    )
    fecha: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    monto: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=False)
    metodo_pago: Mapped[str] = mapped_column(String(50), nullable=False)
    concepto: Mapped[str] = mapped_column(String(80), nullable=False)
    observaciones: Mapped[Optional[str]] = mapped_column(Text)
    usuario: Mapped[Optional[str]] = mapped_column(String(50))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    renta_rel = relationship("Renta", back_populates="pagos")

    def __repr__(self):
        return f"<Pago {self.id} - Renta {self.id_renta} - ${self.monto}>"


# =====================================================================
# GASTOS
# =====================================================================


class Gasto(Base):
    __tablename__ = "gastos"
    __table_args__ = (
        Index("ix_gastos_placa_fecha", "placa", "fecha"),
        Index("ix_gastos_categoria_fecha", "categoria", "fecha"),
        {"mysql_collate": "utf8mb4_unicode_ci"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    placa: Mapped[Optional[str]] = mapped_column(
        String(20), ForeignKey("autos.placa", ondelete="SET NULL"), nullable=True, index=True
    )
    fecha: Mapped[datetime] = mapped_column(Date, nullable=False)
    categoria: Mapped[str] = mapped_column(String(50), nullable=False)
    descripcion: Mapped[str] = mapped_column(String(200), nullable=False)
    monto: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=False)
    comprobante: Mapped[Optional[str]] = mapped_column(String(50))
    usuario: Mapped[Optional[str]] = mapped_column(String(50), server_default="Sistema")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    auto_rel = relationship("Auto", back_populates="gastos")

    def __repr__(self):
        return f"<Gasto {self.id} - {self.categoria} - ${self.monto}>"