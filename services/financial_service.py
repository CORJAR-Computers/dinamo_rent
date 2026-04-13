"""
financial_service.py — Servicio de Lógica Financiera

NUEVO en F1B: Extraído de RentaService para separar responsabilidades.
Contiene: cálculos de totales, ROI de flota (CORREGIDO), y utilidades financieras.

El método roi_flota() original estaba ROTO (devolvía ceros hardcodeados).
Esta versión consulta datos reales de la base de datos.
"""
import datetime
from typing import List, Dict
from decimal import Decimal

from core.logger import get_logger, get_audit_logger
from repositories.repositories_sa import (
    AutoRepositorySA,
    RentaRepositorySA,
    InformeRepositorySA,
)

log = get_logger(__name__)
audit = get_audit_logger()


class FinancialService:

    @staticmethod
    def calcular_total_renta(datos: dict) -> float:
        """
        Calcula el total de una renta nueva.
        Fórmula: (días × valor_día) + (horas_extra × valor_hora) + extras - descuento + impuestos
        """
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
    def calcular_total_cierre(renta: dict, datos_cierre: dict) -> float:
        """
        Calcula el gran total al cerrar una renta.
        Incluye: total pactado + días de retraso + otros cobros.
        """
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
    def roi_flota() -> List[Dict]:
        """
        Calcula el ROI (Retorno de Inversión) de cada vehículo de la flota.

        FIX F1B: La versión original devolvía ceros hardcodeados.
        Esta versión consulta ingresos, mantenimiento y gastos reales por vehículo.

        Fórmula:
          ingresos = SUM(total) de rentas finalizadas por placa
          mantenimiento = SUM(total_mantenimiento) de mantenimientos por placa
          gastos = SUM(monto) de gastos vinculados por placa
          costos_fijos = costo_fijo_mensual × meses_antigüedad
          utilidad = ingresos - mantenimiento - gastos - costos_fijos
          roi % = (utilidad / costos_fijos) × 100  (si costos_fijos > 0)
        """
        hoy = datetime.datetime.now()
        autos = AutoRepositorySA.obtener_todos()

        # Obtener datos financieros consolidados por placa
        ingresos_por_placa = InformeRepositorySA.obtener_ingresos_por_vehiculo()
        mantenimiento_por_placa = InformeRepositorySA.obtener_mantenimiento_por_vehiculo()
        gastos_por_placa = InformeRepositorySA.obtener_gastos_por_vehiculo()

        reporte = []

        for a in autos:
            if a.get('estado') in ['Vendido', 'Baja']:
                continue

            placa = a["placa"]

            # Ingresos reales
            ingresos = float(ingresos_por_placa.get(placa, 0))

            # Mantenimiento real
            manto = float(mantenimiento_por_placa.get(placa, 0))

            # Gastos vinculados al vehículo
            gastos_auto = float(gastos_por_placa.get(placa, 0))

            # Meses de antigüedad
            try:
                f_ing = datetime.datetime.strptime(
                    str(a.get("fecha_ingreso", ""))[:10], "%Y-%m-%d"
                )
                meses = max(1, (hoy.year - f_ing.year) * 12 + (hoy.month - f_ing.month))
            except (ValueError, TypeError):
                meses = 1

            costo_fijo_mensual = float(a.get("costo_fijo_mensual", 0))
            costos_fijos = costo_fijo_mensual * meses

            utilidad = ingresos - manto - gastos_auto - costos_fijos

            # ROI como porcentaje
            roi_pct = 0.0
            if costos_fijos > 0:
                roi_pct = (utilidad / costos_fijos) * 100

            # Punto de equilibrio: días necesarios para cubrir costo fijo mensual
            ingresos_totales = ingresos
            dias_rentado = 0
            if meses > 0 and ingresos_totales > 0:
                promedio_dia = ingresos_totales / (meses * 30)
                if promedio_dia > 0 and costo_fijo_mensual > 0:
                    dias_rentado = round(costo_fijo_mensual / promedio_dia, 1)

            reporte.append({
                "placa": placa,
                "vehiculo": f"{a.get('marca', '')} {a.get('modelo', '')}",
                "ingresos": ingresos,
                "mantenimiento": manto,
                "gastos": gastos_auto,
                "costos_fijos": costos_fijos,
                "utilidad": utilidad,
                "roi_pct": round(roi_pct, 1),
                "equilibrio_dias": dias_rentado,
            })

        return reporte
