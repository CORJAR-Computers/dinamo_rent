"""
importar_sql.py — Script para importar Flota (autos) y Clientes desde dinamo_rent.sql
a la base de datos Firebird activa. Cifra automáticamente campos sensibles con Fernet.
"""

import sys
import os
import re
import ast
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database_sa import get_session
from core.models import Auto, Cliente
from core.logger import get_logger

log = get_logger("importar_sql")


def parse_date(val):
    if not val or val == "0000-00-00" or val == "NULL":
        return None
    if isinstance(val, date):
        return val
    if isinstance(val, datetime):
        return val.date()
    try:
        return datetime.strptime(str(val).strip(), "%Y-%m-%d").date()
    except Exception:
        return None


def parse_datetime(val):
    if not val or val == "0000-00-00 00:00:00" or val == "NULL":
        return None
    if isinstance(val, datetime):
        return val
    try:
        return datetime.strptime(str(val).strip(), "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def parse_sql_values(sql_text: str, table_name: str):
    """Extrae nombres de columnas y lista de tuplas de valores de sentencias INSERT SQL."""
    pattern = rf"INSERT INTO `{table_name}`\s*\((.*?)\)\s*VALUES\s*(.*?);"
    matches = re.findall(pattern, sql_text, re.DOTALL | re.IGNORECASE)
    
    all_rows = []
    columns = []
    
    for cols_str, vals_str in matches:
        if not columns:
            columns = [c.strip(" `\t\r\n") for c in cols_str.split(",")]
        
        tuples = re.findall(r"\((.*?)\)(?:,|\s*;)", vals_str.strip(), re.DOTALL)
        for t_str in tuples:
            clean_str = re.sub(r"\bNULL\b", "None", t_str, flags=re.IGNORECASE)
            try:
                row_tuple = ast.literal_eval(f"({clean_str})")
                if isinstance(row_tuple, tuple):
                    all_rows.append(row_tuple)
            except Exception as e:
                log.warning(f"Error parseando fila de {table_name}: {e}")
                
    return columns, all_rows


def importar():
    sql_filepath = os.path.join(os.path.dirname(__file__), "dinamo_rent.sql")
    if not os.path.exists(sql_filepath):
        print(f"ERROR: No se encontró el archivo {sql_filepath}")
        return

    print(f"Leyendo archivo SQL: {sql_filepath}...")
    with open(sql_filepath, "r", encoding="utf-8", errors="ignore") as f:
        sql_content = f.read()

    with get_session() as session:
        # 1. IMPORTAR AUTOS
        print("\n--- Procesando Flota (Autos) ---")
        auto_cols, auto_rows = parse_sql_values(sql_content, "autos")
        autos_insertados = 0
        autos_omitidos = 0

        for row in auto_rows:
            row_dict = dict(zip(auto_cols, row))
            placa = str(row_dict.get("placa", "")).strip().upper()
            if not placa:
                continue

            existe = session.query(Auto).filter(Auto.placa == placa).first()
            if existe:
                autos_omitidos += 1
                continue

            nuevo_auto = Auto(
                placa=placa,
                marca=row_dict.get("marca") or "N/A",
                modelo=row_dict.get("modelo") or "N/A",
                version=row_dict.get("version"),
                color=row_dict.get("color"),
                tipo=row_dict.get("tipo") or "Automóvil",
                cilindraje=row_dict.get("cilindraje"),
                transmision=row_dict.get("transmision"),
                combustible=row_dict.get("combustible"),
                no_motor=row_dict.get("no_motor"),
                no_chasis=row_dict.get("no_chasis"),
                propietario=row_dict.get("propietario"),
                estado=row_dict.get("estado") or "Disponible",
                costo_fijo_mensual=float(row_dict.get("costo_fijo_mensual") or 0.0),
                kilometraje=float(row_dict.get("kilometraje") or 0.0),
                ubicacion=row_dict.get("ubicacion"),
                tipo_adquisicion=row_dict.get("tipo_adquisicion"),
                proximo_aceite=int(row_dict.get("proximo_aceite") or 0),
                proximo_frenos=int(row_dict.get("proximo_frenos") or 0),
                vencimiento_soat=parse_date(row_dict.get("vencimiento_soat")),
                vencimiento_tecnico=parse_date(row_dict.get("vencimiento_tecnico")),
                vencimiento_extintor=parse_date(row_dict.get("vencimiento_extintor")),
                vencimiento_bateria=parse_date(row_dict.get("vencimiento_bateria")),
                observaciones=row_dict.get("observaciones"),
                fecha_ingreso=parse_date(row_dict.get("fecha_ingreso")) or date.today(),
            )
            session.add(nuevo_auto)
            autos_insertados += 1

        print(f"Autos insertados: {autos_insertados} | Omitidos (ya existían): {autos_omitidos}")

        # 2. IMPORTAR CLIENTES
        print("\n--- Procesando Clientes ---")
        cli_cols, cli_rows = parse_sql_values(sql_content, "clientes")
        clientes_insertados = 0
        clientes_omitidos = 0

        for row in cli_rows:
            row_dict = dict(zip(cli_cols, row))
            no_doc = str(row_dict.get("no_doc", "")).strip() if row_dict.get("no_doc") else None
            nombres = row_dict.get("nombres") or ""
            apellidos = row_dict.get("apellidos") or ""
            nombre_completo = row_dict.get("nombre_completo") or f"{nombres} {apellidos}".strip()

            if not nombre_completo:
                continue

            if no_doc:
                existe = session.query(Cliente).filter(Cliente.no_doc == no_doc).first()
                if existe:
                    clientes_omitidos += 1
                    continue

            nuevo_cliente = Cliente(
                tipo_doc=row_dict.get("tipo_doc"),
                no_doc=no_doc,
                nombres=nombres,
                apellidos=apellidos,
                nombre_completo=nombre_completo,
                celular=row_dict.get("celular"),
                celular2=row_dict.get("celular2"),
                email=row_dict.get("email"),
                ciudad=row_dict.get("ciudad"),
                estado_region=row_dict.get("estado_region"),
                pais=row_dict.get("pais"),
                nacionalidad=row_dict.get("nacionalidad"),
                dir_residencia=row_dict.get("dir_residencia"),
                dir_temporal=row_dict.get("dir_temporal"),
                hotel=row_dict.get("hotel"),
                habitacion=row_dict.get("habitacion"),
                no_licencia=row_dict.get("no_licencia"),
                tipo_licencia=row_dict.get("tipo_licencia"),
                vencimiento_licencia=parse_date(row_dict.get("vencimiento_licencia")),
                estado=row_dict.get("estado") or "Activo",
            )
            session.add(nuevo_cliente)
            clientes_insertados += 1

        print(f"Clientes insertados: {clientes_insertados} | Omitidos (ya existían): {clientes_omitidos}")
        print("\n¡Importación a la Base de Datos completada exitosamente!")


if __name__ == "__main__":
    importar()
