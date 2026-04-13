import os
import sys
import base64
import re
import subprocess
import urllib.parse
from datetime import datetime
import jinja2

# --- CONFIGURACIÓN AUTOMÁTICA DE WEASYPRINT (GTK3) ---
if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

posibles_rutas_gtk = [
    os.path.join(base_path, "gtk3_bin"), 
    r"C:\Program Files\GTK3-Runtime Win64\bin",
    r"C:\msys64\ucrt64\bin",
    r"C:\msys64\mingw64\bin"
]

gtk_path = None
for ruta in posibles_rutas_gtk:
    if os.path.exists(ruta):
        gtk_path = ruta
        break

if gtk_path:
    os.environ['PATH'] = gtk_path + os.pathsep + os.environ['PATH']
    if hasattr(os, 'add_dll_directory'):
        try: os.add_dll_directory(gtk_path)
        except: pass

# Imports de PySide6
try:
    from PySide6.QtGui import QDesktopServices
    from PySide6.QtCore import QUrl
except ImportError:
    pass

# Intentar importar Motores PDF
try:
    from weasyprint import HTML
    TIENE_WEASYPRINT = True
except (ImportError, OSError) as e:
    TIENE_WEASYPRINT = False

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    TIENE_REPORTLAB = True
except ImportError:
    TIENE_REPORTLAB = False

# --- GESTIÓN DE DIRECTORIOS ---
def obtener_rutas_archivos():
    home = os.path.expanduser("~")
    docs = os.path.join(home, "Documents")
    if not os.path.exists(docs):
        docs = os.path.join(home, "Documentos")
        if not os.path.exists(docs): docs = home 
            
    base_folder = os.path.join(docs, "Archivos Dinamo_rent")
    
    rutas = {
        "reservas": os.path.join(base_folder, "Ordenes Reservas"),
        "ordenes": os.path.join(base_folder, "Ordenes Renta"),
        "contratos": os.path.join(base_folder, "Contratos")
    }

    for ruta in rutas.values():
        if not os.path.exists(ruta):
            try: os.makedirs(ruta)
            except: pass
            
    return rutas["reservas"], rutas["contratos"], rutas["ordenes"]

def limpiar_nombre_archivo(texto):
    if not texto: return "Cliente"
    limpio = re.sub(r'[^a-zA-Z0-9\s]', '', str(texto))
    return limpio.strip().replace(' ', '_')

def obtener_ruta_logo():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    posibles = [
        os.path.join(base_dir, "assets", "Logo_Dinamo.png"),
        os.path.join(base_dir, "assets", "LogoDinamo.png"),
        os.path.join(base_dir, "assets", "logo.png")
    ]
    for p in posibles:
        if os.path.exists(p): return p
    return None

def obtener_logo_base64():
    ruta = obtener_ruta_logo()
    if not ruta: return ""
    try:
        with open(ruta, "rb") as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')
            ext = os.path.splitext(ruta)[1].lower().replace('.', '')
            if ext == 'jpg': ext = 'jpeg'
            return f"data:image/{ext};base64,{encoded}"
    except: return ""

def cargar_plantilla_jinja():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ruta_plantilla = os.path.join(base_dir, "templates", "contrato_jinja_template.html")
    if os.path.exists(ruta_plantilla):
        with open(ruta_plantilla, "r", encoding="utf-8") as f:
            return f.read()
    return None

def abrir_archivo(ruta):
    if os.path.exists(ruta):
        try:
            QDesktopServices.openUrl(QUrl.fromLocalFile(ruta))
            return True
        except: pass
    return False

def abrir_whatsapp(celular, mensaje=""):
    if not celular: return False
    try:
        num = re.sub(r'[^0-9]', '', str(celular))
        if len(num) == 10: num = "57" + num
        msg_encoded = urllib.parse.quote(mensaje)
        url = f"https://wa.me/{num}?text={msg_encoded}"
        QDesktopServices.openUrl(QUrl(url))
        return True
    except: return False

def abrir_email(email, asunto="", cuerpo=""):
    if not email: return False
    try:
        url = f"mailto:{email}?subject={urllib.parse.quote(asunto)}&body={urllib.parse.quote(cuerpo)}"
        QDesktopServices.openUrl(QUrl(url))
        return True
    except: return False

def limpiar_moneda(valor):
    if not valor: return 0.0
    if isinstance(valor, (int, float)): return float(valor)
    try:
        return float(str(valor).replace('$', '').replace(',', '').replace(' ', '').strip())
    except: return 0.0

def fmt_moneda(valor):
    return f"$ {limpiar_moneda(valor):,.0f}".replace(",", ".")

# =============================================================================
# 1. GENERAR CONTRATO (HTML -> PDF)
# =============================================================================

def generar_contrato_temp(datos):
    _, ruta_contratos, _ = obtener_rutas_archivos()
    cliente_safe = limpiar_nombre_archivo(datos.get('nombre_cliente', 'Cliente'))
    nombre_archivo = f"Contrato_#{datos.get('id_renta')}_{cliente_safe}.pdf"
    ruta_final = os.path.join(ruta_contratos, nombre_archivo)

    datos['logo_base64'] = obtener_logo_base64()
    datos['tiene_logo'] = bool(datos['logo_base64'])
    datos['fecha_firma'] = datetime.now().strftime("%d de %B de %Y")
    datos['valor_total'] = fmt_moneda(datos.get('total', 0))
    datos['valor_hora_extra'] = fmt_moneda(datos.get('valor_hora_extra', 0))

    if TIENE_WEASYPRINT:
        plantilla_str = cargar_plantilla_jinja()
        if plantilla_str:
            try:
                template = jinja2.Template(plantilla_str)
                html_renderizado = template.render(**datos)
                HTML(string=html_renderizado, base_url=".").write_pdf(ruta_final)
                return True, "Contrato Generado", ruta_final
            except Exception as e:
                print(f"Error WeasyPrint: {e}")

    return generar_orden_alquiler_pdf(datos)

# =============================================================================
# 2. ORDEN DE RENTA (ALQUILER)
# =============================================================================

def generar_orden_alquiler_pdf(datos):
    if not TIENE_REPORTLAB: return None
    try:
        _, _, ruta_ordenes = obtener_rutas_archivos()
        cliente_safe = limpiar_nombre_archivo(datos.get('nombre_cliente', 'Cliente'))
        nombre_archivo = f"Orden_Renta_#{datos.get('id_renta')}_{cliente_safe}.pdf"
        ruta_pdf = os.path.join(ruta_ordenes, nombre_archivo)
        
        doc = SimpleDocTemplate(ruta_pdf, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        elements = []
        styles = getSampleStyleSheet()
        
        estilo_titulo = ParagraphStyle('Titulo', parent=styles['Heading1'], alignment=TA_CENTER, fontSize=16, spaceAfter=20, textColor=colors.darkblue)
        estilo_sub = ParagraphStyle('Sub', parent=styles['Heading3'], fontSize=11, spaceBefore=10, textColor=colors.black, backColor=colors.lightgrey, borderPadding=4)
        
        logo_path = obtener_ruta_logo()
        img = Image(logo_path, width=1.8*inch, height=0.9*inch) if logo_path else Paragraph("<b>DINAMO</b>", styles['Normal'])
        data_emp = [[img, Paragraph("<b>DINAMO RENT A CAR</b><br/>NIT: 900.123.456-7<br/>Sincelejo, Sucre<br/>Tel: 300 123 4567", styles['Normal'])]]
        t_head = Table(data_emp, colWidths=[2.5*inch, 4.5*inch])
        t_head.setStyle(TableStyle([('ALIGN', (1,0), (1,0), 'RIGHT'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
        elements.append(t_head); elements.append(Spacer(1, 15))
        
        elements.append(Paragraph(f"ORDEN DE SALIDA #{datos.get('id_renta')}", estilo_titulo))
        
        info_cli = [[Paragraph("<b>CLIENTE</b>", estilo_sub)], 
                    [f"Nombre: {datos.get('nombre_cliente', '')}"], 
                    [f"Doc: {datos.get('cliente_doc', datos.get('documento_cliente', ''))}"],
                    [f"Cel: {datos.get('cliente_celular', datos.get('celular', ''))}"]]
        
        info_auto = [[Paragraph("<b>VEHÍCULO</b>", estilo_sub)], 
                     [f"Placa: {datos.get('placa', datos.get('auto_placa', ''))}"],
                     [f"Vehículo: {datos.get('auto_marca', '')} {datos.get('auto_modelo', '')}"],
                     [f"Salida: {float(datos.get('km_salida', 0)):,.0f} km | {datos.get('tanque_salida', 'Full')}"]]
        
        t_main = Table([[Table(info_cli, colWidths=[3.2*inch]), Table(info_auto, colWidths=[3.2*inch])]])
        t_main.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
        elements.append(t_main); elements.append(Spacer(1, 10))
        
        f_data = [
            ["Salida:", f"{datos.get('fecha_recogida')} {datos.get('hora_recogida', '')}", "Lugar:", datos.get('ubicacion_recogida', 'Oficina')],
            ["Retorno:", f"{datos.get('fecha_retorno')} {datos.get('hora_retorno', '')}", "Lugar:", datos.get('ubicacion_retorno', 'Oficina')]
        ]
        t_fechas = Table(f_data, colWidths=[1*inch, 2.5*inch, 1*inch, 2.5*inch])
        t_fechas.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke), ('BACKGROUND', (2,0), (2,-1), colors.whitesmoke), ('SIZE', (0,0), (-1,-1), 9)]))
        elements.append(t_fechas); elements.append(Spacer(1, 15))
        
        elements.append(Paragraph("RESUMEN DE COSTOS", estilo_sub))
        fin_data = [["CONCEPTO", "CANT.", "UNITARIO", "SUBTOTAL"]]
        
        dias = limpiar_moneda(datos.get('dias_calculados', datos.get('dias', 0)))
        val_dia = limpiar_moneda(datos.get('valor_dia', 0))
        fin_data.append(["Renta Vehículo", f"{dias} Días", fmt_moneda(val_dia), fmt_moneda(dias*val_dia)])
        
        extras = [("Horas Extras", 'horas_extras', 'valor_hora_extra'), ("Lavado", None, 'costo_lavado'),
                  ("Silla Bebé", None, 'costo_silla'), ("Cables", None, 'costo_cables'),
                  ("Inversor", None, 'costo_inversor'), ("Domicilio", None, 'costo_domicilio')]
        
        for nom, k_cant, k_val in extras:
            val = limpiar_moneda(datos.get(k_val, 0))
            if val > 0:
                cant = str(datos.get(k_cant, 1)) if k_cant else "1"
                tot = val * (float(cant) if k_cant == 'horas_extras' else 1)
                fin_data.append([nom, cant, fmt_moneda(val), fmt_moneda(tot)])
                
        fin_data.append(["", "", "TOTAL:", fmt_moneda(datos.get('total', 0))])
        
        t_fin = Table(fin_data, colWidths=[3*inch, 1*inch, 1.5*inch, 1.5*inch])
        t_fin.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.darkblue), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (2,0), (-1,-1), 'RIGHT'), ('GRID', (0,0), (-1,-2), 0.5, colors.grey),
            ('FONTNAME', (-2,-1), (-1,-1), 'Helvetica-Bold'), ('BACKGROUND', (-2,-1), (-1,-1), colors.lightyellow)
        ]))
        elements.append(t_fin)
        
        elements.append(Spacer(1, 40))
        t_sig = Table([["_______________________", "_______________________"], ["FIRMA CLIENTE", "DINAMO RENT A CAR"]], colWidths=[3.5*inch, 3.5*inch])
        t_sig.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('FONTNAME', (0,1), (-1,-1), 'Helvetica-Bold')]))
        elements.append(t_sig)
        
        doc.build(elements)
        if "generar_contrato_temp" in str(sys._getframe(1).f_code): 
            return True, "Orden generada (Modo Backup)", ruta_pdf
        return ruta_pdf
    except Exception as e:
        print(f"Error PDF Renta: {e}")
        return None

# =============================================================================
# 3. ORDEN DE RESERVA (DISEÑO PRO + POLÍTICAS)
# =============================================================================

def generar_pdf_reserva(datos):
    if not TIENE_REPORTLAB: return False, "Falta ReportLab"
    try:
        _, ruta_reservas, _ = obtener_rutas_archivos()
        
        cliente_safe = limpiar_nombre_archivo(datos.get('cliente_nombre', 'Cliente'))
        nombre_archivo = f"Reserva_#{datos.get('id_reserva')}_{cliente_safe}.pdf"
        ruta_pdf = os.path.join(ruta_reservas, nombre_archivo)
        
        doc = SimpleDocTemplate(ruta_pdf, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        elements = []
        styles = getSampleStyleSheet()
        
        estilo_titulo = ParagraphStyle('Titulo', parent=styles['Heading1'], alignment=TA_CENTER, fontSize=16, spaceAfter=20, textColor=colors.darkorange)
        estilo_sub = ParagraphStyle('Sub', parent=styles['Heading3'], fontSize=11, spaceBefore=10, textColor=colors.black, backColor=colors.lightgrey, borderPadding=4)
        
        logo_path = obtener_ruta_logo()
        img = Image(logo_path, width=1.8*inch, height=0.9*inch) if logo_path else Paragraph("<b>DINAMO</b>", styles['Normal'])
        data_emp = [[img, Paragraph("<b>DINAMO RENT A CAR</b><br/>NIT: 900.123.456-7<br/>Sincelejo, Sucre<br/>Tel: 300 123 4567", styles['Normal'])]]
        t_head = Table(data_emp, colWidths=[2.5*inch, 4.5*inch])
        t_head.setStyle(TableStyle([('ALIGN', (1,0), (1,0), 'RIGHT'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
        elements.append(t_head); elements.append(Spacer(1, 15))
        
        elements.append(Paragraph(f"COMPROBANTE DE RESERVA No.{datos.get('id_reserva')}", estilo_titulo))
        
        info_cli = [[Paragraph("<b>CLIENTE</b>", estilo_sub)],
                    [f"Nombre: {datos.get('cliente_nombre', '')}"],
                    [f"Documento: {datos.get('cliente_doc', '')}"],
                    [f"Teléfono: {datos.get('cliente_celular', '')}"]] 

        info_res = [[Paragraph("<b>DETALLES</b>", estilo_sub)],
                    [f"Vehículo: {datos.get('vehiculo', '')}"],
                    [f"Recogida: {datos.get('f_inicio', '')} {datos.get('h_inicio', '')}"],
                    [f"Devolución: {datos.get('f_fin', '')} {datos.get('h_fin', '')}"]]

        t_main = Table([[Table(info_cli, colWidths=[3.2*inch]), Table(info_res, colWidths=[3.2*inch])]])
        t_main.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
        elements.append(t_main); elements.append(Spacer(1, 15))
        
        elements.append(Paragraph("ESTADO DE CUENTA", estilo_sub))
        
        total = limpiar_moneda(datos.get('total', 0))
        abono = limpiar_moneda(datos.get('abono', 0))
        pendiente = total - abono
        
        fin_data = [
            ["CONCEPTO", "VALOR"],
            ["Valor Total Estimado", fmt_moneda(total)],
            ["Abono / Seña Recibida", fmt_moneda(abono)],
            ["SALDO PENDIENTE (Al recoger)", fmt_moneda(pendiente)]
        ]
        
        t_fin = Table(fin_data, colWidths=[4.5*inch, 2.5*inch])
        t_fin.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('TEXTCOLOR', (1,2), (1,2), colors.green),
            ('TEXTCOLOR', (1,3), (1,3), colors.red),
            ('FONTNAME', (0,3), (-1,3), 'Helvetica-Bold'), 
            ('BACKGROUND', (0,3), (-1,3), colors.lightyellow),
            ('PADDING', (0,0), (-1,-1), 8)
        ]))
        elements.append(t_fin)
        
        # --- POLÍTICAS Y REQUISITOS (NUEVO) ---
        elements.append(Spacer(1, 25))
        
        estilo_terminos_titulo = ParagraphStyle('TerminosTit', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold', spaceAfter=4)
        estilo_terminos_texto = ParagraphStyle('TerminosTxt', parent=styles['Normal'], fontSize=8, leftIndent=10, spaceAfter=2)
        
        elements.append(Paragraph("Política de Reservas", estilo_terminos_titulo))
        puntos_politica = [
            "• Las reservas se gestionan conforme al horario oficial del país. Se otorga 1 hora de tolerancia.",
            "• Si el cliente no se presenta en dicho tiempo, la reserva se cancela automáticamente.",
            "• Pagos anticipados no son reembolsables por no presentación o cancelación automática."
        ]
        for p in puntos_politica: elements.append(Paragraph(p, estilo_terminos_texto))
            
        elements.append(Spacer(1, 8))
        elements.append(Paragraph("Requisitos para la Renta", estilo_terminos_titulo))
        puntos_req = [
            "• Tarjeta de crédito con cupo libre mínimo de $2.000.000 COP para garantía.",
            "• Identificación oficial vigente y licencia de conducción válida."
        ]
        for p in puntos_req: elements.append(Paragraph(p, estilo_terminos_texto))
            
        elements.append(Spacer(1, 8))
        elements.append(Paragraph("Otras consideraciones", estilo_terminos_titulo))
        elements.append(Paragraph("En ausencia de documentos o cupo, no será posible el alquiler.", estilo_terminos_texto))
        
        elements.append(Spacer(1, 15))
        elements.append(Paragraph("Al confirmar, el cliente acepta las condiciones dadas.", ParagraphStyle('Final', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, fontName='Helvetica-Oblique')))
        
        doc.build(elements)
        return True, ruta_pdf
    except Exception as e: return False, str(e)

def enviar_a_impresora(ruta_pdf):
    """
    Intenta enviar el PDF directamente a la impresora predeterminada 
    o abre el diálogo de impresión de Windows.
    """
    if not os.path.exists(ruta_pdf): return
    
    try:
        if sys.platform == "win32":
            # El verbo 'print' le dice a Windows que imprima el archivo
            # en lugar de solo abrirlo.
            os.startfile(ruta_pdf, "print")
        else:
            # Fallback para otros sistemas (solo abrir)
            abrir_archivo(ruta_pdf)
    except Exception as e:
        print(f"Error al intentar imprimir: {e}")
        # Si falla el modo impresión, lo abrimos normal
        abrir_archivo(ruta_pdf)

# Alias para compatibilidad
crear_pdf_orden_basica = generar_orden_alquiler_pdf