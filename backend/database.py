import sqlite3
import json
import config

DB_NAME = config.DB_PATH if hasattr(config, 'DB_PATH') else "visitas.db"

def conectar():
    return sqlite3.connect(DB_NAME)

def inicializar_db():
    con = conectar()
    cur = con.cursor()
    
    # --- CREACIÓN DE TABLAS ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reportes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            fecha TEXT, cliente TEXT, tecnico TEXT, 
            observaciones TEXT, imagen_path TEXT, 
            pdf_path TEXT, detalles_usuarios TEXT, 
            email_enviado INTEGER DEFAULT 0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tecnicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            nombre TEXT UNIQUE
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            nombre TEXT PRIMARY KEY, 
            email TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            nombre TEXT, 
            cliente_nombre TEXT, 
            FOREIGN KEY(cliente_nombre) REFERENCES clientes(nombre) ON DELETE CASCADE
        )
    """)

    # --- MIGRACIONES DE COLUMNAS (Para evitar errores si ya existen) ---
    columnas_reportes = [
        ("pdf_path", "TEXT"),
        ("detalles_usuarios", "TEXT"),
        ("email_enviado", "INTEGER DEFAULT 0"),
        ("latitud", "TEXT"),
        ("longitud", "TEXT")
    ]
    
    for col, tipo in columnas_reportes:
        try: 
            cur.execute(f"ALTER TABLE reportes ADD COLUMN {col} {tipo}")
        except: pass

    # --- DATOS POR DEFECTO (ELIMINADO) ---
    # He comentado estas líneas para evitar que los datos borrados reaparezcan.
    # Si quieres iniciar con datos vacíos, esto es lo correcto.
    
    # cur.execute("SELECT COUNT(*) FROM tecnicos")
    # if cur.fetchone()[0] == 0:
    #     cur.executemany("INSERT OR IGNORE INTO tecnicos (nombre) VALUES (?)", [("Francisco Alfaro",), ("David Quezada",)])

    # cur.execute("SELECT COUNT(*) FROM clientes")
    # if cur.fetchone()[0] == 0:
    #     for cli, email in config.CORREOS_POR_CLIENTE.items():
    #         cur.execute("INSERT OR IGNORE INTO clientes (nombre, email) VALUES (?, ?)", (cli, email))
            
    # cur.execute("SELECT COUNT(*) FROM usuarios")
    # if cur.fetchone()[0] == 0:
    #     for cli, lista_users in config.USUARIOS_POR_CLIENTE.items():
    #         for u in lista_users:
    #             cur.execute("INSERT INTO usuarios (nombre, cliente_nombre) VALUES (?, ?)", (u, cli))

    con.commit()
    con.close()

# --- FUNCIONES TÉCNICOS ---

def obtener_tecnicos():
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT nombre FROM tecnicos ORDER BY nombre ASC")
    lista = [row[0] for row in cur.fetchall()]
    con.close()
    return lista

def agregar_nuevo_tecnico(nombre):
    try: 
        con = conectar()
        cur = con.cursor()
        cur.execute("INSERT INTO tecnicos (nombre) VALUES (?)", (nombre,))
        con.commit()
        con.close()
        return True
    except: 
        return False

def eliminar_tecnico(nombre):
    try: 
        con = conectar()
        cur = con.cursor()
        cur.execute("DELETE FROM tecnicos WHERE nombre = ?", (nombre,))
        con.commit()
        con.close()
        return True
    except: 
        return False

# --- FUNCIONES CLIENTES ---

def obtener_clientes():
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT nombre, email FROM clientes ORDER BY nombre ASC")
    datos = cur.fetchall()
    con.close()
    return datos

def obtener_nombres_clientes():
    return [c[0] for c in obtener_clientes()]

def agregar_cliente(nombre, email):
    if not nombre: return False
    try: 
        con = conectar()
        cur = con.cursor()
        cur.execute("INSERT OR REPLACE INTO clientes (nombre, email) VALUES (?, ?)", (nombre, email))
        con.commit()
        con.close()
        return True
    except Exception as e: 
        print(f"Error agregando cliente DB: {e}")
        return False

def eliminar_cliente(nombre):
    try:
        con = conectar()
        cur = con.cursor()
        # Primero borramos usuarios asociados para mantener integridad
        cur.execute("DELETE FROM usuarios WHERE cliente_nombre = ?", (nombre,))
        cur.execute("DELETE FROM clientes WHERE nombre = ?", (nombre,))
        con.commit()
        con.close()
        return True
    except: 
        return False

def obtener_correo_cliente(nombre_cliente):
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT email FROM clientes WHERE nombre = ?", (nombre_cliente,))
    res = cur.fetchone()
    con.close()
    return res[0] if res else ""

# --- FUNCIONES USUARIOS ---

def obtener_usuarios_por_cliente(cliente_nombre):
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT nombre FROM usuarios WHERE cliente_nombre = ? ORDER BY nombre ASC", (cliente_nombre,))
    lista = [row[0] for row in cur.fetchall()]
    con.close()
    return lista

def agregar_usuario(nombre, cliente_nombre):
    try: 
        con = conectar()
        cur = con.cursor()
        cur.execute("INSERT INTO usuarios (nombre, cliente_nombre) VALUES (?, ?)", (nombre, cliente_nombre))
        con.commit()
        con.close()
        return True
    except: 
        return False

def eliminar_usuario(nombre, cliente_nombre):
    try: 
        con = conectar()
        cur = con.cursor()
        cur.execute("DELETE FROM usuarios WHERE nombre = ? AND cliente_nombre = ?", (nombre, cliente_nombre))
        con.commit()
        con.close()
        return True
    except: 
        return False

# --- FUNCIONES REPORTES (CRUD y ELIMINACIÓN) ---

def eliminar_reporte(id_reporte):
    try:
        con = conectar()
        cur = con.cursor()
        cur.execute("DELETE FROM reportes WHERE id = ?", (id_reporte,))
        filas_afectadas = cur.rowcount
        con.commit()
        con.close()
        return filas_afectadas > 0
    except Exception as e:
        print(f"Error eliminando reporte: {e}")
        return False

def obtener_conteo_reportes():
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM reportes")
    total = cur.fetchone()[0]
    con.close()
    return total

def obtener_historial():
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT id, fecha, cliente, tecnico, observaciones, pdf_path, email_enviado, detalles_usuarios, imagen_path FROM reportes ORDER BY id DESC")
    datos = cur.fetchall()
    con.close()
    return datos

def obtener_reporte_por_id(id_reporte):
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT id, fecha, cliente, tecnico, observaciones, pdf_path, email_enviado, detalles_usuarios, imagen_path FROM reportes WHERE id = ?", (id_reporte,))
    dato = cur.fetchone()
    con.close()
    return dato

def obtener_datos_clientes():
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT cliente, COUNT(*) FROM reportes GROUP BY cliente ORDER BY COUNT(*) DESC")
    datos = cur.fetchall()
    con.close()
    return datos

def obtener_datos_tecnicos():
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT tecnico, COUNT(*) FROM reportes GROUP BY tecnico ORDER BY COUNT(*) DESC")
    datos = cur.fetchall()
    con.close()
    return datos

def actualizar_estado_email(id_reporte, estado):
    con = conectar()
    cur = con.cursor()
    cur.execute("UPDATE reportes SET email_enviado = ? WHERE id = ?", (estado, id_reporte))
    con.commit()
    con.close()

def guardar_reporte(fecha, cliente, tecnico, obs, fotos_json, pdf_path, detalles_json, estado_envio, lat="", lon=""):
    con = conectar()
    cur = con.cursor()
    cur.execute("""
        INSERT INTO reportes (fecha, cliente, tecnico, observaciones, imagen_path, pdf_path, detalles_usuarios, email_enviado, latitud, longitud) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (fecha, cliente, tecnico, obs, fotos_json, pdf_path, detalles_json, estado_envio, lat, lon))
    con.commit()
    inserted_id = cur.lastrowid 
    con.close()
    return inserted_id 

def actualizar_reporte(id_reporte, fecha, cliente, tecnico, obs, fotos_json, pdf_path, detalles_json, estado_envio):
    con = conectar()
    cur = con.cursor()
    cur.execute("""
        UPDATE reportes 
        SET fecha=?, cliente=?, tecnico=?, observaciones=?, imagen_path=?, pdf_path=?, detalles_usuarios=?, email_enviado=?
        WHERE id=?
    """, (fecha, cliente, tecnico, obs, fotos_json, pdf_path, detalles_json, estado_envio, id_reporte))
    con.commit()
    con.close()

def obtener_reportes_pendientes():
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT id, pdf_path, cliente, tecnico FROM reportes WHERE email_enviado = 0")
    datos = cur.fetchall()
    con.close()
    return datos

# --- NUEVAS FUNCIONES PARA MÉTRICAS ---

def obtener_kpis_generales():
    con = conectar()
    cur = con.cursor()
    
    cur.execute("SELECT COUNT(*) FROM reportes")
    total = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM reportes WHERE email_enviado = 0")
    pendientes = cur.fetchone()[0]
    
    cur.execute("SELECT cliente, COUNT(*) as c FROM reportes GROUP BY cliente ORDER BY c DESC LIMIT 1")
    top_cli = cur.fetchone()
    cliente_top = f"{top_cli[0]} ({top_cli[1]})" if top_cli else "N/A"
    
    con.close()
    return total, pendientes, cliente_top

def obtener_evolucion_mensual():
    con = conectar()
    cur = con.cursor()
    cur.execute("""
        SELECT substr(fecha, 1, 7) as mes, COUNT(*) 
        FROM reportes 
        GROUP BY mes 
        ORDER BY mes DESC 
        LIMIT 6
    """)
    datos = cur.fetchall() 
    con.close()
    return datos[::-1]