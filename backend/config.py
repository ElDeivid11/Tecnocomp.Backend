import os

# ==========================================
# 1. CONFIGURACIÓN DE RUTAS Y SISTEMA
# ==========================================
# Obtenemos la ruta absoluta de donde está este archivo
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Definimos la carpeta temporal
TEMP_FOLDER = os.path.join(BASE_DIR, "temp_uploads")

# Ruta de la base de datos
DB_PATH = os.path.join(BASE_DIR, "visitas.db")

# Asegurar que existan los directorios necesarios al iniciar
if not os.path.exists(TEMP_FOLDER):
    os.makedirs(TEMP_FOLDER)

# ==========================================
# 2. CREDENCIALES MICROSOFT GRAPH (SEGURAS)
# ==========================================
GRAPH_CLIENT_ID = os.getenv("GRAPH_CLIENT_ID", "TU_CLIENT_ID_LOCAL")
GRAPH_CLIENT_SECRET = os.getenv("GRAPH_CLIENT_SECRET", "TU_SECRET_LOCAL")
GRAPH_TENANT_ID = os.getenv("GRAPH_TENANT_ID", "TU_TENANT_ID_LOCAL")
GRAPH_USER_EMAIL = os.getenv("GRAPH_USER_EMAIL", "soporte@tecnocomp.cl")

# ==========================================
# 3. SHAREPOINT (ARCHIVOS Y LISTAS)
# ==========================================
SHAREPOINT_HOST_NAME = "tecnocompcomputacion.sharepoint.com" 
SHAREPOINT_SITE_PATH = "/sites/Pruueba" 
SHAREPOINT_DRIVE_NAME = "Documentos"
SHAREPOINT_BACKUP_FOLDER = "Backups_DB"

# IDs para la Lista de SharePoint
SHAREPOINT_SITE_ID = "tecnocompcomputacion.sharepoint.com,f67a6766-495c-41e7-8caa-eb89b1801758,661e71e7-fee3-4a98-8c3e-323b2dd43bbe"
SHAREPOINT_LIST_ID = "803eb871-8bcc-4561-bd91-599876787eb9"

# ==========================================
# 4. CONFIGURACIÓN GENERAL Y ESTILOS
# ==========================================
FONT_FAMILY = "Helvetica"
NOMBRE_EMPRESA_ONEDRIVE = "Tecnocomp Computacion Ltda"
EMPRESA_NOMBRE = "Tecnocomp Ltda"  # <--- ¡ESTA ES LA VARIABLE QUE FALTABA!
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123") 

TAREAS_MANTENIMIENTO = [
    "Solicitar cierre de documentos y credenciales",
    "Reinicio Forzado (Shutdown -r -f -t 00)",
    "Borrar Temporales (%temp%)",
    "Borrar Papelera (Consultar al usuario)",
    "Comprobador de Errores (Tomar Evidencia)",
    "Windows Update (Validar parches grandes/Foto)",
    "Antivirus (Escaneo Rápido + Evidencia)"
]

# Datos iniciales
CORREOS_POR_CLIENTE = {
    "Intermar": "contacto@intermar.cl",
    "Las200": "admin@las200.cl"
}

USUARIOS_POR_CLIENTE = {
    "Intermar": ["Usuario 1", "Usuario 2"],
    "Las200": ["Usuario A", "Usuario B"]
}

# Estilos
COLOR_PRIMARIO = "#0583F2"
COLOR_SECUNDARIO = "#2685BF"
COLOR_ACCENTO = "#2BB9D9"
COLOR_ROJO_SUAVE = "#FFE5E5"
COLOR_AZUL_SUAVE = "#E0F2FF"
COLOR_BLANCO = "#FFFFFF"

COLORES = {
    "light": {
        "fondo": "#F5F8FA", "superficie": "#FFFFFF", "texto": "#0D0D0D",
        "texto_sec": "grey", "sombra": "#1A0583F2", "borde": "#E0E0E0",
        "input_bg": "#FFFFFF", "card_bg": "#FFFFFF"
    },
    "dark": {
        "fondo": "#121212", "superficie": "#1E1E1E", "texto": "#FFFFFF",
        "texto_sec": "#B0B0B0", "sombra": "#00000000", "borde": "#333333",
        "input_bg": "#2C2C2C", "card_bg": "#1E1E1E"
    }
}

COLORES_GRAFICOS = ["blue", "purple", "teal", "orange", "pink", "cyan", "indigo"]