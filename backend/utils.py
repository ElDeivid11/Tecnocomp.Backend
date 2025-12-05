import datetime
import pytz
import requests
import base64
import tempfile
import os
from PIL import Image, ImageDraw
import config

def obtener_hora_chile():
    try:
        return datetime.datetime.now(pytz.timezone('Chile/Continental'))
    except:
        return datetime.datetime.now()

# --- HELPER INTERNO PARA AUTH (Token Único) ---
def _obtener_token_graph():
    url = f"https://login.microsoftonline.com/{config.GRAPH_TENANT_ID}/oauth2/v2.0/token"
    data = {
        'grant_type': 'client_credentials',
        'client_id': config.GRAPH_CLIENT_ID,
        'client_secret': config.GRAPH_CLIENT_SECRET,
        'scope': 'https://graph.microsoft.com/.default'
    }
    try:
        r = requests.post(url, data=data)
        js = r.json()
        if 'access_token' in js:
            return js['access_token']
        print(f"Error Token: {js}")
        return None
    except Exception as e:
        print(f"Excepción Token: {e}")
        return None

# --- HELPER PARA LIMPIAR NOMBRES DE CARPETAS ---
def _sanitizar_nombre(nombre):
    """Elimina caracteres ilegales para carpetas de SharePoint"""
    if not nombre: return "SinNombre"
    # Caracteres prohibidos en SharePoint/OneDrive
    for char in ['"', '*', ':', '<', '>', '?', '/', '\\', '|']:
        nombre = nombre.replace(char, '')
    return nombre.strip()

# --- SHAREPOINT (SUBIDA AUTOMÁTICA DINÁMICA) ---
def subir_archivo_sharepoint(ruta_local, cliente):
    """
    Sube el PDF a SharePoint creando la estructura: /NombreCliente/YYYY-MM-DD/Archivo.pdf
    La carpeta del cliente se crea dinámicamente según lo seleccionado en la App.
    """
    if not os.path.exists(ruta_local):
        return False, "Archivo local no existe"

    token = _obtener_token_graph()
    if not token:
        return False, "No se pudo autenticar con Graph"

    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    filename = os.path.basename(ruta_local)
    
    # Definimos la estructura dinámica
    cliente_limpio = _sanitizar_nombre(cliente) # Ej: "Intermar" o "Las200"
    fecha_carpeta = obtener_hora_chile().strftime('%Y-%m-%d') # Ej: "2025-12-03"

    try:
        # 1. Obtener ID del Sitio
        site_url = f"https://graph.microsoft.com/v1.0/sites/{config.SHAREPOINT_HOST_NAME}:{config.SHAREPOINT_SITE_PATH}"
        r_site = requests.get(site_url, headers=headers)
        if r_site.status_code != 200:
            return False, f"Error buscando Sitio SharePoint ({config.SHAREPOINT_SITE_PATH}): {r_site.text}"
        
        site_id = r_site.json()['id']

        # 2. Obtener ID del Drive (Documentos)
        drives_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
        r_drives = requests.get(drives_url, headers=headers)
        drive_id = None
        
        # Buscar el drive correcto por nombre configurado
        for d in r_drives.json().get('value', []):
            if d['name'] == config.SHAREPOINT_DRIVE_NAME or d['name'] == "Documents" or d['name'] == "Documentos":
                drive_id = d['id']
                break
        
        if not drive_id and r_drives.json().get('value'):
            drive_id = r_drives.json()['value'][0]['id'] # Fallback

        if not drive_id:
            return False, "No se encontró la biblioteca de documentos"

        # 3. Construir ruta dinámica y Subir
        # Estructura final: /NombreCliente/2025-12-03/Reporte...pdf
        ruta_sharepoint = f"/{cliente_limpio}/{fecha_carpeta}/{filename}"
        
        # API Endpoint para subir contenido (PUT crea carpetas automáticamente)
        upload_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:{ruta_sharepoint}:/content"

        with open(ruta_local, 'rb') as f_upload:
            headers_put = headers.copy()
            headers_put['Content-Type'] = 'application/pdf'
            r_up = requests.put(upload_url, headers=headers_put, data=f_upload)

        if r_up.status_code in [200, 201]:
            return True, f"Subido a carpeta '{cliente_limpio}/{fecha_carpeta}'"
        else:
            return False, f"Error subida SP: {r_up.status_code}"

    except Exception as e:
        return False, f"Excepción SharePoint: {e}"

# --- EMAIL OFICIAL (DISEÑO MEJORADO) ---
def enviar_correo_graph(ruta_pdf, cliente, tecnico):
    if not os.path.exists(ruta_pdf): return False, "PDF no existe."
    
    destinatario = config.CORREOS_POR_CLIENTE.get(cliente, "")
    if not destinatario: return False, f"No hay correo para {cliente}"

    token = _obtener_token_graph()
    if not token: return False, "Error Auth Azure"

    with open(ruta_pdf, "rb") as f:
        pdf_content = base64.b64encode(f.read()).decode("utf-8")
    
    # --- PLANTILLA HTML PROFESIONAL ---
    color_brand = config.COLOR_PRIMARIO
    fecha_hoy = obtener_hora_chile().strftime('%d/%m/%Y')
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ margin: 0; padding: 0; background-color: #f4f4f4; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
            .email-container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1); margin-top: 20px; margin-bottom: 20px; }}
            .header {{ background-color: {color_brand}; color: #ffffff; padding: 30px 20px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 24px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; }}
            .content {{ padding: 40px 30px; color: #333333; line-height: 1.6; }}
            .greeting {{ font-size: 18px; margin-bottom: 20px; color: #2c3e50; }}
            .info-card {{ background-color: #f8f9fa; border-left: 5px solid {color_brand}; padding: 20px; margin: 25px 0; border-radius: 4px; }}
            .info-row {{ margin-bottom: 10px; display: flex; justify-content: space-between; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
            .info-row:last-child {{ border-bottom: none; margin-bottom: 0; padding-bottom: 0; }}
            .info-label {{ font-weight: bold; color: #7f8c8d; text-transform: uppercase; font-size: 12px; }}
            .info-value {{ font-weight: 600; color: #2c3e50; text-align: right; }}
            .btn-fake {{ display: block; width: 200px; margin: 30px auto; padding: 12px 0; background-color: {color_brand}; color: #ffffff !important; text-align: center; text-decoration: none; border-radius: 25px; font-weight: bold; font-size: 14px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            .footer {{ background-color: #ecf0f1; padding: 20px; text-align: center; font-size: 12px; color: #95a5a6; border-top: 1px solid #e0e0e0; }}
            .footer p {{ margin: 5px 0; }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h1>Reporte Técnico</h1>
            </div>
            <div class="content">
                <p class="greeting">Estimados <strong>{cliente}</strong>,</p>
                <p>Se ha completado una visita técnica en sus instalaciones. Adjunto a este correo encontrará el informe detallado con las actividades realizadas, evidencias y conformidad del servicio.</p>
                
                <div class="info-card">
                    <div class="info-row">
                        <span class="info-label">Fecha del Servicio</span>
                        <span class="info-value">{fecha_hoy}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Técnico Responsable</span>
                        <span class="info-value">{tecnico}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Estado</span>
                        <span class="info-value" style="color: #27ae60;">Finalizado con Éxito</span>
                    </div>
                </div>

                <p style="text-align: center; font-size: 14px; color: #7f8c8d;">
                    El documento PDF adjunto contiene el detalle completo.
                </p>
                
                <div style="text-align:center; margin-top:20px;">
                    <span style="background-color: {color_brand}; color: white; padding: 10px 20px; border-radius: 20px; font-size: 14px; font-weight: bold;">
                        📎 Revisar PDF Adjunto
                    </span>
                </div>

                <p style="margin-top: 40px; border-top: 1px solid #eee; padding-top: 20px;">
                    Atentamente,<br>
                    <strong>Soporte Tecnocomp</strong>
                </p>
            </div>
            <div class="footer">
                <p>&copy; {datetime.datetime.now().year} Tecnocomp Computación Ltda.</p>
                <p>Este es un mensaje automático, por favor no responder a esta dirección.</p>
                <p>La información contenida en este mensaje es confidencial.</p>
            </div>
        </div>
    </body>
    </html>
    """

    email_data = {
        "message": {
            "subject": f"📍 Reporte de Visita - {cliente} - {fecha_hoy}",
            "body": {"contentType": "HTML", "content": html_body},
            "toRecipients": [{"emailAddress": {"address": destinatario}}],
            "attachments": [{
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": os.path.basename(ruta_pdf),
                "contentType": "application/pdf",
                "contentBytes": pdf_content
            }]
        },
        "saveToSentItems": "true"
    }

    try:
        r = requests.post(
            f"https://graph.microsoft.com/v1.0/users/{config.GRAPH_USER_EMAIL}/sendMail",
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            json=email_data
        )
        if r.status_code == 202: return True, "Correo enviado (Oficial)"
        return False, f"Error Graph Email: {r.text}"
    except Exception as e:
        return False, f"Error envío: {e}"

def guardar_firma_img(trazos, nombre_archivo="firma_temp.png"):
    if not trazos: return None
    temp_dir = tempfile.gettempdir()
    path = os.path.join(temp_dir, nombre_archivo)
    img = Image.new("RGB", (400, 200), "white")
    draw = ImageDraw.Draw(img)
    for t in trazos:
        if len(t) > 1: draw.line(t, fill="black", width=3)
        elif len(t) == 1: draw.point(t[0], fill="black")
    img.save(path); return path

def subir_backup_database():
    """
    Sube el archivo 'visitas.db' a la carpeta de backups en SharePoint.
    Retorna (True/False, Mensaje).
    """
    db_filename = "visitas.db"
    if not os.path.exists(db_filename):
        return False, "No se encuentra el archivo de base de datos local."

    token = _obtener_token_graph()
    if not token:
        return False, "No se pudo autenticar con Graph"

    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    # Generar nombre con fecha para no sobrescribir
    timestamp = obtener_hora_chile().strftime('%Y%m%d_%H%M%S')
    remote_filename = f"Backup_visitas_{timestamp}.db"

    try:
        # 1. Obtener ID del Sitio (Reutilizamos lógica)
        site_url = f"https://graph.microsoft.com/v1.0/sites/{config.SHAREPOINT_HOST_NAME}:{config.SHAREPOINT_SITE_PATH}"
        r_site = requests.get(site_url, headers=headers)
        if r_site.status_code != 200:
            return False, "Error conectando al sitio SharePoint"
        
        site_id = r_site.json()['id']

        # 2. Obtener ID del Drive
        drives_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
        r_drives = requests.get(drives_url, headers=headers)
        drive_id = None
        for d in r_drives.json().get('value', []):
            if d['name'] == config.SHAREPOINT_DRIVE_NAME or d['name'] in ["Documents", "Documentos"]:
                drive_id = d['id']
                break
        
        if not drive_id: return False, "No se encontró Drive"

        # 3. Subir archivo a carpeta de Backups
        # Estructura: /Backups_DB/Backup_visitas_FECHA.db
        ruta_sharepoint = f"/{config.SHAREPOINT_BACKUP_FOLDER}/{remote_filename}"
        upload_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:{ruta_sharepoint}:/content"

        with open(db_filename, 'rb') as f_upload:
            headers_put = headers.copy()
            # application/x-sqlite3 es lo correcto, pero application/octet-stream es más genérico
            headers_put['Content-Type'] = 'application/octet-stream' 
            r_up = requests.put(upload_url, headers=headers_put, data=f_upload)

        if r_up.status_code in [200, 201]:
            return True, f"Backup exitoso: {remote_filename}"
        else:
            return False, f"Error subida: {r_up.status_code} - {r_up.text}"

    except Exception as e:
        return False, f"Excepción Backup: {e}"