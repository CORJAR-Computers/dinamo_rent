import pymysql
from datetime import datetime
from core.database_sa import SessionLocal
from core.models import Cliente, Auto


def parse_date(val):
    if not val:
        return None
    if isinstance(val, datetime):
        return val.date() if hasattr(val, 'date') else val
    try:
        return datetime.strptime(str(val), '%Y-%m-%d').date()
    except:
        return None


def migrar_datos():
    print("Conectando al servidor MySQL antiguo...")
    conn_vieja = pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='dinamo_rent_vieja',
        cursorclass=pymysql.cursors.DictCursor
    )
    cursor = conn_vieja.cursor()
    session = SessionLocal()

    try:
        print("Migrando Clientes...")
        cursor.execute("SELECT * FROM clientes")
        clientes_viejos = cursor.fetchall()

        for c in clientes_viejos:
            existe = session.query(Cliente).filter_by(no_doc=c.get('no_doc')).first()
            if existe:
                continue
            nombres = c.get('nombres', '') or ''
            apellidos = c.get('apellidos', '') or ''
            nombre_completo = f"{nombres} {apellidos}".strip() or c.get('nombre_completo') or 'Cliente sin nombre'

            cliente = Cliente(
                tipo_doc=c.get('tipo_doc'),
                no_doc=c.get('no_doc'),
                nombres=nombres,
                apellidos=apellidos,
                nombre_completo=nombre_completo,
                celular=c.get('celular'),
                celular2=c.get('celular2'),
                email=c.get('email'),
                ciudad=c.get('ciudad'),
                estado_region=c.get('estado_region'),
                pais=c.get('pais'),
                nacionalidad=c.get('nacionalidad'),
                dir_residencia=c.get('dir_residencia'),
                dir_temporal=c.get('dir_temporal'),
                hotel=c.get('hotel'),
                habitacion=c.get('habitacion'),
                no_licencia=c.get('no_licencia'),
                tipo_licencia=c.get('tipo_licencia'),
                vencimiento_licencia=parse_date(c.get('vencimiento_licencia')),
            )
            session.add(cliente)
        session.commit()
        print(f"  {len(clientes_viejos)} clientes procesados")

        print("Migrando Flota de Vehículos...")
        cursor.execute("SELECT * FROM autos")
        flota_vieja = cursor.fetchall()

        for f in flota_vieja:
            existe = session.query(Auto).filter_by(placa=f.get('placa')).first()
            if existe:
                continue
            vehiculo = Auto(
                placa=f.get('placa'),
                marca=f.get('marca'),
                modelo=f.get('modelo'),
                version=f.get('version'),
                color=f.get('color'),
                tipo=f.get('tipo'),
                cilindraje=f.get('cilindraje'),
                transmision=f.get('transmision'),
                combustible=f.get('combustible'),
                no_motor=f.get('no_motor'),
                no_chasis=f.get('no_chasis'),
                propietario=f.get('propietario'),
                estado=f.get('estado', 'Disponible'),
                costo_fijo_mensual=float(f.get('costo_fijo_mensual') or 0),
                kilometraje=float(f.get('kilometraje') or 0),
                ubicacion=f.get('ubicacion'),
                tipo_adquisicion=f.get('tipo_adquisicion'),
                proximo_aceite=f.get('proximo_aceite'),
                proximo_frenos=f.get('proximo_frenos'),
                vencimiento_soat=parse_date(f.get('vencimiento_soat')),
                vencimiento_tecnico=parse_date(f.get('vencimiento_tecnico')),
                vencimiento_extintor=parse_date(f.get('vencimiento_extintor')),
                vencimiento_bateria=parse_date(f.get('vencimiento_bateria')),
                observaciones=f.get('observaciones'),
                fecha_ingreso=parse_date(f.get('fecha_ingreso')),
            )
            session.add(vehiculo)
        session.commit()
        print(f"  {len(flota_vieja)} vehículos procesados")

        print("Migración completada!")

    except Exception as e:
        session.rollback()
        print(f"Error durante la migración: {e}")
        raise
    finally:
        session.close()
        conn_vieja.close()


if __name__ == "__main__":
    migrar_datos()
