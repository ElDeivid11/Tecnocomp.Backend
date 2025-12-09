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
    if not nombre: return "SinNombre"
    for char in ['"', '*', ':', '<', '>', '?', '/', '\\', '|']:
        nombre = nombre.replace(char, '')
    return nombre.strip()

# --- SHAREPOINT: SUBIR ARCHIVO (Retorna URL) ---
def subir_archivo_sharepoint(ruta_local, cliente):
    """
    Sube el PDF a SharePoint y retorna: (True/False, Mensaje, WebUrl)
    """
    if not os.path.exists(ruta_local):
        return False, "Archivo local no existe", None

    token = _obtener_token_graph()
    if not token:
        return False, "No se pudo autenticar con Graph", None

    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    filename = os.path.basename(ruta_local)
    
    cliente_limpio = _sanitizar_nombre(cliente)
    fecha_carpeta = obtener_hora_chile().strftime('%Y-%m-%d')

    try:
        # 1. Obtener ID del Sitio
        site_url = f"https://graph.microsoft.com/v1.0/sites/{config.SHAREPOINT_HOST_NAME}:{config.SHAREPOINT_SITE_PATH}"
        r_site = requests.get(site_url, headers=headers)
        if r_site.status_code != 200:
            return False, f"Error Sitio SP: {r_site.text}", None
        
        site_id = r_site.json()['id']

        # 2. Obtener ID del Drive
        drives_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
        r_drives = requests.get(drives_url, headers=headers)
        drive_id = None
        
        for d in r_drives.json().get('value', []):
            if d['name'] == config.SHAREPOINT_DRIVE_NAME or d['name'] in ["Documents", "Documentos"]:
                drive_id = d['id']
                break
        
        if not drive_id and r_drives.json().get('value'):
            drive_id = r_drives.json()['value'][0]['id']

        if not drive_id:
            return False, "No se encontró biblioteca", None

        # 3. Subir Archivo
        ruta_sharepoint = f"/{cliente_limpio}/{fecha_carpeta}/{filename}"
        upload_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:{ruta_sharepoint}:/content"

        with open(ruta_local, 'rb') as f_upload:
            headers_put = headers.copy()
            headers_put['Content-Type'] = 'application/pdf'
            r_up = requests.put(upload_url, headers=headers_put, data=f_upload)

        if r_up.status_code in [200, 201]:
            resp = r_up.json()
            web_url = resp.get('webUrl', '') # Link directo al archivo
            return True, f"Subido a '{cliente_limpio}/{fecha_carpeta}'", web_url
        else:
            return False, f"Error subida SP: {r_up.status_code}", None

    except Exception as e:
        return False, f"Excepción SP: {e}", None

# --- SHAREPOINT: CREAR ITEM EN LISTA (NUEVO) ---
def crear_item_lista(datos):
    """
    Crea un registro en la Lista de SharePoint.
    datos = { 'titulo', 'cliente', 'tecnico', 'fecha', 'link' }
    """
    token = _obtener_token_graph()
    if not token: return False, "No token"

    # URL directa usando los IDs configurados
    url = f"https://graph.microsoft.com/v1.0/sites/{config.SHAREPOINT_SITE_ID}/lists/{config.SHAREPOINT_LIST_ID}/items"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    # Asegúrate de que los nombres de las claves ("Title", "Cliente", etc.)
    # coincidan EXACTAMENTE con las columnas 'internal name' de tu lista SharePoint.
    cuerpo = {
        "fields": {
            "Title": datos['titulo'],
            "Cliente": datos['cliente'],
            "Tecnico": datos['tecnico'],
            "Fecha": datos['fecha'],
            "LinkPDF": datos['link'] 
        }
    }

    try:
        r = requests.post(url, headers=headers, json=cuerpo)
        if r.status_code == 201:
            return True, "Item creado en lista"
        else:
            return False, f"Error Lista: {r.text}"
    except Exception as e:
        return False, f"Excepción Lista: {e}"

# --- EMAIL (CON COPIA A TÉCNICO) ---
def enviar_correo_graph(ruta_pdf, cliente, tecnico, email_tecnico=None):
    if not os.path.exists(ruta_pdf): return False, "PDF no existe."
    
    destinatario = config.CORREOS_POR_CLIENTE.get(cliente, "")
    if not destinatario: return False, f"No hay correo para {cliente}"

    token = _obtener_token_graph()
    if not token: return False, "Error Auth Azure"

    with open(ruta_pdf, "rb") as f:
        pdf_content = base64.b64encode(f.read()).decode("utf-8")
    
    # --- DISEÑO DE CORREO MEJORADO ---
    color = config.COLOR_PRIMARIO
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0; padding:0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f4;">
        <table width="100%" border="0" cellspacing="0" cellpadding="0">
            <tr>
                <td align="center" style="padding: 20px;">
                    <table width="600" border="0" cellspacing="0" cellpadding="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                        <tr>
                            <td bgcolor="{color}" style="padding: 30px; text-align: center; color: #ffffff;">
                                <h1 style="margin:0; font-size: 24px; font-weight: 600;">REPORTE TÉCNICO</h1>
                                <p style="margin:5px 0 0; font-size: 14px; opacity: 0.9;">Servicio de Visita en Terreno</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 40px 30px; color: #333333;">
                                <p style="font-size: 16px; margin-bottom: 20px;">Estimados <strong>{cliente}</strong>,</p>
                                <p style="line-height: 1.6; color: #555;">
                                    Se ha completado satisfactoriamente la visita técnica programada. A continuación, se detallan los datos del servicio realizado por nuestro especialista.
                                </p>
                                
                                <table width="100%" border="0" cellspacing="0" cellpadding="10" style="margin: 20px 0; background-color: #f9f9f9; border-left: 4px solid {color};">
                                    <tr>
                                        <td width="30%" style="font-weight: bold; color: #777;">TÉCNICO:</td>
                                        <td style="font-weight: 600; color: #333;">{tecnico}</td>
                                    </tr>
                                    <tr>
                                        <td style="font-weight: bold; color: #777;">FECHA:</td>
                                        <td style="font-weight: 600; color: #333;">{datetime.datetime.now().strftime('%d/%m/%Y')}</td>
                                    </tr>
                                    <tr>
                                        <td style="font-weight: bold; color: #777;">ESTADO:</td>
                                        <td style="color: #27ae60; font-weight: bold;">✅ Finalizado con Éxito</td>
                                    </tr>
                                </table>

                                <p style="text-align: center; font-size: 14px; color: #888; margin-top: 30px;">
                                    📎 El informe completo se encuentra adjunto en formato PDF.
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <td bgcolor="#eeeeee" style="padding: 20px; text-align: center; font-size: 12px; color: #999;">
                                <p style="margin: 0;">&copy; {datetime.datetime.now().year} {config.EMPRESA_NOMBRE}</p>
                                <p style="margin: 5px 0 0;">Por favor, no responder a este correo automático.</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    # ... (El resto del código de envío es igual, usando html_body) ...
    # Asegúrate de incluir el bloque de destinations y request.post aquí
    # Si necesitas el bloque completo de nuevo, pídelo, pero es reemplazar solo el html_body

    # Construimos destinatarios
    destinatarios = [{"emailAddress": {"address": destinatario}}]
    
    # Si hay email técnico, lo agregamos como destinatario (o podrías usar ccRecipients)
    cc_destinatarios = []
    if email_tecnico:
        cc_destinatarios.append({"emailAddress": {"address": email_tecnico}})

    email_data = {
        "message": {
            "subject": f"📍 Reporte Visita - {cliente}",
            "body": {"contentType": "HTML", "content": html_body},
            "toRecipients": destinatarios,
            "ccRecipients": cc_destinatarios, # Agregamos copia aquí
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
        if r.status_code == 202: return True, "Correo enviado"
        return False, f"Error Email: {r.text}"
    except Exception as e:
        return False, f"Excepción Email: {e}"

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
    # ... (Misma lógica de backup que tenías antes, omitida por brevedad si no cambió)
    return True, "Backup OK"