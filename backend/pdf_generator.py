import os
import tempfile
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import config
import utils

class PDFReporte(FPDF):
    def header(self):
        # 1. Fondo Cabecera Moderna (Azul con una línea inferior más oscura)
        self.set_fill_color(5, 131, 242) # Azul Corporativo
        self.rect(0, 0, 210, 40, 'F')
        self.set_fill_color(0, 86, 163) # Azul Oscuro (borde inferior)
        self.rect(0, 40, 210, 2, 'F')
        
        # 2. Logo (Misma lógica de rutas)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(base_dir, "assets", "logo.png")
        logo2_path = os.path.join(base_dir, "assets", "logo2.png")
        
        logo_final = None
        if os.path.exists(logo_path): logo_final = logo_path
        elif os.path.exists(logo2_path): logo_final = logo2_path
            
        if logo_final:
            try: 
                self.image(logo_final, x=10, y=8, h=24) 
            except: pass
            
        # 3. Título y Subtítulo
        self.set_font('Helvetica', 'B', 20)
        self.set_text_color(255, 255, 255)
        self.set_xy(80, 12)
        self.cell(120, 10, 'INFORME DE VISITA TÉCNICA', 0, 0, 'R')
        
        self.set_font('Helvetica', '', 10)
        self.set_xy(80, 22)
        self.cell(120, 10, 'Departamento de Soporte IT', 0, 0, 'R')
        self.ln(35)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Tecnocomp Ltda - Pág {self.page_no()}/{{nb}}', 0, 0, 'C')

def generar_pdf(cliente, tecnico, obs, path_firma, datos_usuarios):
    pdf = PDFReporte(orientation='P', unit='mm', format='A4')
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # --- BLOQUE 1: RESUMEN DE LA VISITA (Estilo Tarjeta) ---
    pdf.set_fill_color(245, 247, 250) # Gris muy suave
    pdf.set_draw_color(200, 200, 200)
    pdf.rect(10, 45, 190, 25, 'FD') # Fill and Draw
    
    pdf.set_y(48)
    pdf.set_x(15)
    
    # Función auxiliar para datos en línea
    def dato_inline(label, val, x_offset):
        pdf.set_x(x_offset)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(20, 5, label, 0, 0)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(50, 5, val, 0, 0)

    # Fila 1
    dato_inline("CLIENTE:", cliente, 15)
    dato_inline("FECHA:", utils.obtener_hora_chile().strftime('%d/%m/%Y'), 120)
    pdf.ln(8)
    # Fila 2
    dato_inline("TÉCNICO:", tecnico, 15)
    dato_inline("HORA:", utils.obtener_hora_chile().strftime('%H:%M hrs'), 120)
    
    pdf.ln(20)

    # --- TÍTULO SECCIÓN ---
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(5, 131, 242)
    pdf.cell(0, 8, "DETALLE DE USUARIOS ATENDIDOS", 0, 1, 'L')
    pdf.set_draw_color(5, 131, 242)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    # --- BLOQUE 2: USUARIOS ---
    for u in datos_usuarios:
        # Evitar cortes de página feos
        if pdf.get_y() > 220: pdf.add_page()
        
        # Marco del usuario
        y_inicio = pdf.get_y()
        
        # Nombre y Estado
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(130, 8, f"Usuario: {u['nombre']}", 0, 0)
        
        # Badge de estado
        pdf.set_font("Helvetica", "B", 9)
        if u['atendido']:
            pdf.set_fill_color(220, 255, 220) # Verde claro
            pdf.set_text_color(0, 128, 0)
            pdf.cell(40, 7, "  ATENDIDO  ", 0, 1, 'C', fill=True)
        else:
            pdf.set_fill_color(255, 230, 230) # Rojo claro
            pdf.set_text_color(180, 0, 0)
            pdf.cell(40, 7, " NO ATENDIDO ", 0, 1, 'C', fill=True)
            
        pdf.ln(2)

        # --- CONTENIDO FORMATEADO (Checklist) ---
        if u['atendido']:
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(80, 80, 80)
            pdf.cell(0, 6, "Tareas Realizadas:", 0, 1)
            
            # AQUÍ ESTÁ LA MAGIA: Parseamos el string separado por comas
            texto_trabajo = u.get('trabajo', '')
            if ',' in texto_trabajo:
                items = texto_trabajo.split(',')
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(0, 0, 0)
                for item in items:
                    item = item.strip()
                    if item:
                        # Dibujamos un bullet point
                        pdf.set_x(15)
                        pdf.cell(5, 5, chr(149), 0, 0) # Caracter bullet
                        pdf.cell(0, 5, item, 0, 1)
            else:
                # Si es texto plano sin comas
                pdf.set_x(15)
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(0, 0, 0)
                pdf.multi_cell(0, 5, texto_trabajo)
                
        else:
            # Si no fue atendido
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(80, 80, 80)
            pdf.cell(20, 6, "Motivo:", 0, 0)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(0, 6, u.get('motivo', ''))

        # --- FOTOS (GRID 3 COLUMNAS) ---
        if u.get('fotos') and u['atendido']:
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(5, 131, 242)
            pdf.cell(0, 5, "Evidencia Fotográfica:", 0, 1)
            
            y_fotos = pdf.get_y()
            x_fotos = 12
            count = 0
            
            for fp in u['fotos']:
                if os.path.exists(fp):
                    # Control de salto de página para fotos
                    if y_fotos + 35 > 270:
                        pdf.add_page()
                        y_fotos = pdf.get_y()
                        x_fotos = 12
                        count = 0
                        
                    try:
                        # Marco foto
                        pdf.set_draw_color(220, 220, 220)
                        pdf.rect(x_fotos-1, y_fotos-1, 47, 37) 
                        pdf.image(fp, x=x_fotos, y=y_fotos, w=45, h=35)
                        x_fotos += 50
                        count += 1
                        if count >= 3: # Salto de línea cada 3 fotos
                            count = 0
                            x_fotos = 12
                            y_fotos += 40
                    except: pass
            
            # Ajustamos el cursor Y al final de las fotos
            if count > 0 or (count == 0 and x_fotos == 12):
                pdf.set_y(y_fotos + 40 if count > 0 else y_fotos)

        # --- FIRMA USUARIO ---
        firma_usr = u.get('firma')
        if firma_usr and os.path.exists(firma_usr):
            # Verificar espacio
            if pdf.get_y() > 250: pdf.add_page()
            
            pdf.ln(2)
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(128, 128, 128)
            pdf.cell(0, 4, f"Conformidad: {u['nombre']}", 0, 1)
            try:
                pdf.image(firma_usr, x=15, h=12)
            except: pass
        
        pdf.ln(5)
        # Línea separadora suave
        pdf.set_draw_color(230, 230, 230)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

    # --- OBSERVACIONES FINALES ---
    if pdf.get_y() > 230: pdf.add_page()
    
    pdf.set_fill_color(245, 247, 250)
    pdf.rect(10, pdf.get_y(), 190, 20, 'F')
    pdf.set_xy(12, pdf.get_y()+2)
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(5, 131, 242)
    pdf.cell(0, 5, "OBSERVACIONES GENERALES:", 0, 1)
    
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.set_x(12)
    pdf.multi_cell(185, 5, obs if obs else "Sin observaciones adicionales.")
    
    # --- FIRMA TÉCNICO (Opcional, si existiera) ---
    # Si quieres poner un pie de página o firma del técnico al final
    pdf.ln(10)

    # Guardar
    temp_dir = tempfile.gettempdir()
    nombre_clean = "".join([c for c in cliente if c.isalnum() or c in (' ','-','_')]).strip()
    nombre_archivo = f"Reporte_{nombre_clean}_{utils.obtener_hora_chile().strftime('%Y%m%d_%H%M')}.pdf"
    ruta = os.path.join(temp_dir, nombre_archivo)
    pdf.output(ruta)
    return ruta