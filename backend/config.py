import os

# ==========================================
# CONFIGURACIÓN GENERAL
# ==========================================

FONT_FAMILY = "Helvetica" # FPDF usa fuentes core por defecto
NOMBRE_EMPRESA_ONEDRIVE = "Tecnocomp Computacion Ltda"

# --- SEGURIDAD: Leemos del entorno o usamos un valor por defecto solo para pruebas locales ---
# En Render, configuraremos estas variables en el panel de control.
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123") 
SHAREPOINT_BACKUP_FOLDER = "Backups_DB"

# Tareas de Mantenimiento
TAREAS_MANTENIMIENTO = [
    "Solicitar cierre de documentos y credenciales",
    "Reinicio Forzado (Shutdown -r -f -t 00)",
    "Borrar Temporales (%temp%)",
    "Borrar Papelera (Consultar al usuario)",
    "Comprobador de Errores (Tomar Evidencia)",
    "Windows Update (Validar parches grandes/Foto)",
    "Antivirus (Escaneo Rápido + Evidencia)"
]

# DATOS INICIALES (Clientes por defecto si la DB está vacía)
CORREOS_POR_CLIENTE = {
    "Intermar": "contacto@intermar.cl",
    "Las200": "admin@las200.cl"
}

USUARIOS_POR_CLIENTE = {
    "Intermar": ["Usuario 1", "Usuario 2"],
    "Las200": ["Usuario A", "Usuario B"]
}

# ==========================================
# CREDENCIALES MICROSOFT GRAPH (SEGURAS)
# ==========================================
GRAPH_CLIENT_ID = os.getenv("GRAPH_CLIENT_ID", "TU_CLIENT_ID_LOCAL")
GRAPH_CLIENT_SECRET = os.getenv("GRAPH_CLIENT_SECRET", "TU_SECRET_LOCAL")
GRAPH_TENANT_ID = os.getenv("GRAPH_TENANT_ID", "TU_TENANT_ID_LOCAL")
GRAPH_USER_EMAIL = os.getenv("GRAPH_USER_EMAIL", "soporte@tecnocomp.cl")

# SHAREPOINT
SHAREPOINT_HOST_NAME = "tecnocompcomputacion.sharepoint.com" 
SHAREPOINT_SITE_PATH = "/sites/Pruueba" 
SHAREPOINT_DRIVE_NAME = "Documentos"

# ==========================================
# ESTILOS Y COLORES
# ==========================================
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

# Asegurar directorios
if not os.path.exists("backups"):
    os.makedirs("backups")
if not os.path.exists("reportes"):
    os.makedirs("reportes")