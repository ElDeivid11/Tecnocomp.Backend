import os
import tempfile
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import config
import utils

class PDFReporte(FPDF):
    def header(self):
        # Fondo cabecera
        self.set_fill_color(5, 131, 242) # Azul similar a COLOR_PRIMARIO
        self.rect(0, 0, 210, 42, 'F')
        
        # --- CORRECCIÓN LOGO (Ruta Absoluta) ---
        # Buscamos la carpeta 'assets' en el mismo directorio donde está este script
        base_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(base_dir, "assets", "logo.png")
        logo2_path = os.path.join(base_dir, "assets", "logo2.png")
        
        logo_final = None
        if os.path.exists(logo_path):
            logo_final = logo_path
        elif os.path.exists(logo2_path):
            logo_final = logo2_path
            
        if logo_final:
            try: 
                # Ajustamos coordenadas y tamaño
                self.image(logo_final, x=10, y=6, w=50) 
            except Exception as e:
                print(f"Error cargando logo: {e}")
            
        # Título
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(255, 255, 255)
        self.set_xy(140, 15)
        self.cell(60, 10, 'INFORME TÉCNICO', 0, 0, 'R')
        self.ln(45)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}} - App Visitas Tecnocomp', 0, 0, 'C')

def generar_pdf(cliente, tecnico, obs, path_firma, datos_usuarios):
    pdf = PDFReporte(orientation='P', unit='mm', format='A4')
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Datos generales
    pdf.set_fill_color(240, 240, 240)
    pdf.rect(10, 48, 190, 28, 'F')
    
    def add_data_row(label, value):
        pdf.set_x(15)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(25, 6, label, new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 6, value, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_y(53)
    add_data_row("CLIENTE:", cliente)
    add_data_row("TÉCNICO:", tecnico)
    add_data_row("FECHA:", utils.obtener_hora_chile().strftime('%d/%m/%Y %H:%M'))
    
    pdf.ln(15)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(5, 131, 242)
    pdf.cell(0, 8, "BITÁCORA DE ATENCIÓN", align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    for u in datos_usuarios:
        if pdf.get_y() > 220: pdf.add_page()
        
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(140, 8, u['nombre'], new_x=XPos.RIGHT, new_y=YPos.TOP, align='L')
        
        pdf.set_font("Helvetica", "B", 9)
        if u['atendido']:
            pdf.set_fill_color(220, 255, 220)
            pdf.set_text_color(0, 100, 0)
            pdf.cell(50, 8, "ATENDIDO", align='C', fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        else:
            pdf.set_fill_color(255, 220, 220)
            pdf.set_text_color(180, 0, 0)
            pdf.cell(50, 8, "NO ATENDIDO", align='C', fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)
        pdf.set_x(10)
        pdf.set_font("Helvetica", "", 10)
        texto = f"Trabajo: {u['trabajo']}" if u['atendido'] else f"Motivo: {u['motivo']}"
        pdf.multi_cell(0, 5, texto, align='L')
        
        # Fotos
        if u.get('fotos') and u['atendido']:
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(5, 131, 242)
            pdf.cell(0, 4, "Evidencias:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            x_c, y_c = 10, pdf.get_y() + 1
            for fp in u['fotos']:
                if os.path.exists(fp):
                    if x_c + 45 > 200: 
                        x_c = 10
                        y_c += 40
                    if y_c + 40 > 250: 
                        pdf.add_page()
                        x_c = 10
                        y_c = pdf.get_y()
                    try: 
                        pdf.image(fp, x=x_c, y=y_c, h=35)
                        x_c += 48
                    except: pass
            pdf.set_y(y_c + 40)
        
        # Firma usuario (Ajustada)
        firma_usr = u.get('firma')
        if firma_usr and os.path.exists(firma_usr):
            if pdf.get_y() + 25 > 270: pdf.add_page()
            
            pdf.ln(2)
            pdf.set_x(10)
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 4, f"Firma de conformidad - {u['nombre']}:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            try: 
                pdf.image(firma_usr, h=15) 
                pdf.ln(5)
            except: pass

        pdf.ln(5)
        pdf.set_draw_color(230, 230, 230)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

    if pdf.get_y() > 220: pdf.add_page()
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(5, 131, 242)
    pdf.cell(0, 8, "OBSERVACIONES ADICIONALES", align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(0,0,0)
    pdf.multi_cell(0, 6, obs if obs else "Sin observaciones adicionales.", align='L')
    pdf.ln(10)
    
    if path_firma and os.path.exists(path_firma):
        if pdf.get_y() > 200: pdf.add_page()
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 6, "CONFORMIDAD DEL SERVICIO", align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.image(path_firma, w=50)

    temp_dir = tempfile.gettempdir()
    nombre_archivo = f"Reporte_{cliente}_{utils.obtener_hora_chile().strftime('%Y%m%d_%H%M%S')}.pdf"
    ruta = os.path.join(temp_dir, nombre_archivo)
    pdf.output(ruta)
    return ruta