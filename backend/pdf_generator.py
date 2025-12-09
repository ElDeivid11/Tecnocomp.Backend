import os
import tempfile
from fpdf import FPDF
import config
import utils

class PDFReporte(FPDF):
    def header(self):
        # --- FONDO ENCABEZADO ---
        self.set_fill_color(245, 247, 250) # Gris muy claro de fondo
        self.rect(0, 0, 210, 45, 'F')
        
        # --- LOGO ---
        base_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(base_dir, "assets", "logo.png") # Prioridad png
        if not os.path.exists(logo_path):
             logo_path = os.path.join(base_dir, "assets", "logo2.png")
            
        if os.path.exists(logo_path):
            try: 
                # Logo a la izquierda
                self.image(logo_path, x=12, y=10, h=18) 
            except: pass
            
        # --- TÍTULOS ---
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(33, 37, 41) # Gris oscuro casi negro
        self.set_xy(12, 12)
        self.cell(0, 10, 'INFORME DE SERVICIO TÉCNICO', 0, 0, 'R')
        
        self.set_font('Helvetica', '', 9)
        self.set_text_color(100, 100, 100)
        self.set_xy(12, 20)
        self.cell(0, 10, 'Departamento de IT & Soporte', 0, 0, 'R')
        
        # Línea separadora azul
        self.set_draw_color(5, 131, 242) # Azul principal
        self.set_line_width(0.5)
        self.line(10, 38, 200, 38)
        self.ln(30)

    def footer(self):
        self.set_y(-20)
        self.set_draw_color(220, 220, 220)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)
        
        self.set_font('Helvetica', '', 8)
        self.set_text_color(150, 150, 150)
        
        # Texto izquierda
        self.cell(95, 4, 'Tecnocomp Ltda. | Servicios Informáticos Profesionales', 0, 0, 'L')
        # Paginación derecha
        self.cell(95, 4, f'Página {self.page_no()}/{{nb}}', 0, 0, 'R')

def generar_pdf(cliente, tecnico, obs, path_firma, datos_usuarios):
    pdf = PDFReporte(orientation='P', unit='mm', format='A4')
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    
    # --- 1. INFORMACIÓN DE LA VISITA (Estilo Tabla) ---
    pdf.set_y(45)
    
    # Colores
    bg_header = (5, 131, 242) # Azul
    text_header = (255, 255, 255) # Blanco
    bg_cell = (250, 250, 250) # Blanco humo
    
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_fill_color(*bg_header)
    pdf.set_text_color(*text_header)
    
    # Headers Tabla
    pdf.cell(95, 8, "  CLIENTE / EMPRESA", 0, 0, 'L', True)
    pdf.cell(5, 8, "", 0, 0) # Espacio
    pdf.cell(90, 8, "  DETALLES DEL SERVICIO", 0, 1, 'L', True)
    
    # Contenido Tabla
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(50, 50, 50)
    pdf.set_fill_color(*bg_cell)
    
    # Fila 1
    start_y = pdf.get_y()
    pdf.set_x(10)
    pdf.cell(95, 8, f"  {cliente}", 0, 0, 'L', True)
    pdf.set_x(110)
    fecha = utils.obtener_hora_chile().strftime('%d/%m/%Y')
    pdf.cell(90, 8, f"  Fecha: {fecha}", 0, 1, 'L', True)
    
    # Fila 2
    pdf.set_x(10)
    pdf.cell(95, 8, f"  ID Reporte: #TEMP", 0, 0, 'L', True) # Puedes poner ID real si lo pasas
    pdf.set_x(110)
    hora = utils.obtener_hora_chile().strftime('%H:%M hrs')
    pdf.cell(90, 8, f"  Hora: {hora}", 0, 1, 'L', True)
    
    # Fila 3
    pdf.set_x(10)
    pdf.cell(95, 8, f"  Técnico: {tecnico}", 0, 0, 'L', True)
    pdf.set_x(110)
    pdf.cell(90, 8, f"  Estado: Finalizado", 0, 1, 'L', True)
    
    pdf.ln(10)

    # --- 2. DETALLE DE TRABAJOS ---
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(5, 131, 242)
    pdf.cell(0, 10, "REGISTRO DE ATENCIONES", 0, 1, 'L')
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    for u in datos_usuarios:
        if pdf.get_y() > 230: pdf.add_page()
        
        # Contenedor gris suave para cada usuario
        y_start_user = pdf.get_y()
        
        # Icono estado (Simulado con círculo)
        if u['atendido']:
            pdf.set_fill_color(40, 167, 69) # Verde
        else:
            pdf.set_fill_color(220, 53, 69) # Rojo
        
        # Dibuja círculo (elipse)
        pdf.ellipse(14, pdf.get_y() + 2.5, 3, 3, 'F')
        
        pdf.set_x(20)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(100, 8, u['nombre'].upper(), 0, 0)
        
        # Badge alineado a la derecha
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_x(160)
        estado_txt = "ATENDIDO" if u['atendido'] else "NO ATENDIDO"
        pdf.set_text_color(255, 255, 255)
        pdf.cell(30, 6, estado_txt, 0, 1, 'C', True)
        
        pdf.ln(2)
        
        # Contenido
        pdf.set_x(20)
        if u['atendido']:
            # Tareas formateadas
            texto_trabajo = u.get('trabajo', '')
            if texto_trabajo:
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(80, 80, 80)
                pdf.cell(0, 5, "Labores realizadas:", 0, 1)
                
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(50, 50, 50)
                
                items = texto_trabajo.split(',') if ',' in texto_trabajo else [texto_trabajo]
                for item in items:
                    item = item.strip()
                    if item:
                        pdf.set_x(22)
                        pdf.cell(4, 5, "-", 0, 0)
                        pdf.cell(0, 5, item, 0, 1)
        else:
            # Motivo
            pdf.set_x(20)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(80, 80, 80)
            pdf.cell(15, 5, "Motivo:", 0, 0)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(50, 50, 50)
            pdf.multi_cell(0, 5, u.get('motivo', ''))

        # Fotos Grid
        if u.get('fotos') and u['atendido']:
            pdf.ln(2)
            pdf.set_x(20)
            
            y_fotos = pdf.get_y()
            x_fotos = 20
            count = 0
            
            for fp in u['fotos']:
                if os.path.exists(fp):
                    # Chequeo salto página
                    if y_fotos + 30 > 270:
                        pdf.add_page()
                        y_fotos = pdf.get_y()
                        x_fotos = 20
                        count = 0
                    
                    try:
                        # Borde foto
                        pdf.set_draw_color(230, 230, 230)
                        pdf.rect(x_fotos-0.5, y_fotos-0.5, 36, 28)
                        # Imagen
                        pdf.image(fp, x=x_fotos, y=y_fotos, w=35, h=27)
                        
                        x_fotos += 38
                        count += 1
                        if count >= 4: # 4 fotos por fila (más pequeñas pero caben más)
                             y_fotos += 30
                             x_fotos = 20
                             count = 0
                    except: pass
            
            # Recuperar cursor Y
            if count > 0 or (count == 0 and x_fotos == 20):
                 pdf.set_y(y_fotos + 32 if count > 0 else y_fotos)

        # Firma Usuario
        firma_usr = u.get('firma')
        if firma_usr and os.path.exists(firma_usr):
             if pdf.get_y() > 250: pdf.add_page()
             pdf.set_y(pdf.get_y() + 2)
             pdf.set_x(150)
             try:
                pdf.image(firma_usr, x=150, h=10)
                pdf.set_x(150)
                pdf.set_font("Helvetica", "I", 6)
                pdf.cell(40, 3, "(Conformidad Usuario)", 0, 1, 'C')
             except: pass

        pdf.ln(4)
        pdf.set_draw_color(240, 240, 240)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y()) # Separador suave
        pdf.ln(4)

    # --- 3. OBSERVACIONES GENERALES ---
    if pdf.get_y() > 240: pdf.add_page()
    
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(5, 131, 242)
    pdf.cell(0, 6, "OBSERVACIONES GENERALES / RECOMENDACIONES", 0, 1)
    
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 5, obs if obs else "Sin observaciones registradas por el técnico.")
    
    # --- FIN DEL PDF ---
    temp_dir = tempfile.gettempdir()
    nombre_clean = "".join([c for c in cliente if c.isalnum() or c in (' ','-','_')]).strip()
    nombre_archivo = f"Reporte_{nombre_clean}_{utils.obtener_hora_chile().strftime('%Y%m%d_%H%M')}.pdf"
    ruta = os.path.join(temp_dir, nombre_archivo)
    pdf.output(ruta)
    return ruta