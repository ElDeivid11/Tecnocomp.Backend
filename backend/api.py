import shutil
import os
import json
from typing import List, Optional
from datetime import datetime
# IMPORTANTE: Agregamos BackgroundTasks para tareas en segundo plano
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

import database
import utils
import pdf_generator
import config

app = FastAPI(title="Tecnocomp API")

# Inicializamos la DB
database.inicializar_db()

# --- MODELOS ---
class ClienteBase(BaseModel):
    nombre: str
    email: str

class TecnicoBase(BaseModel):
    nombre: str

# Nuevo Modelo para Usuarios
class UsuarioBase(BaseModel):
    nombre: str
    cliente_nombre: str

# --- ENDPOINTS DE LECTURA ---
@app.get("/clientes")
def get_clientes(): return database.obtener_clientes()

@app.get("/tecnicos")
def get_tecnicos(): return database.obtener_tecnicos()

# --- NUEVO: OBTENER TODOS LOS USUARIOS (Para sincronizar entre tablets) ---
@app.get("/usuarios_todos")
def get_all_usuarios():
    # Conectamos directamente para sacar todo el listado global
    con = database.conectar()
    cur = con.cursor()
    cur.execute("SELECT nombre, cliente_nombre FROM usuarios")
    # Formateamos como lista de diccionarios
    datos = [{"nombre": row[0], "cliente": row[1]} for row in cur.fetchall()]
    con.close()
    return datos

@app.post("/clientes")
def create_cliente(cliente: ClienteBase):
    database.agregar_cliente(cliente.nombre, cliente.email)
    return {"status": "ok"}

# --- NUEVO: CREAR TÉCNICO ---
@app.post("/tecnicos")
def create_tecnico(tecnico: TecnicoBase):
    if database.agregar_nuevo_tecnico(tecnico.nombre):
        return {"status": "ok"}
    raise HTTPException(status_code=400, detail="Error o técnico ya existe")

# --- NUEVO: CREAR USUARIO ---
@app.post("/usuarios")
def create_usuario(usuario: UsuarioBase):
    if database.agregar_usuario(usuario.nombre, usuario.cliente_nombre):
        return {"status": "ok"}
    raise HTTPException(status_code=400, detail="Error al crear usuario")

@app.get("/usuarios/{cliente_nombre}")
def get_usuarios(cliente_nombre: str):
    return database.obtener_usuarios_por_cliente(cliente_nombre)

# --- ENDPOINT DE BACKUP MANUAL ---
@app.get("/sistema/backup")
def forzar_backup():
    """
    Llama a este link para guardar una copia de la DB en SharePoint.
    """
    ok, msg = utils.subir_backup_database()
    return {"status": "ok" if ok else "error", "mensaje": msg}

# --- FUNCIÓN DE LIMPIEZA (Se ejecuta después de responder) ---
def eliminar_archivos_temporales(rutas: List[str]):
    print(f"🧹 Iniciando limpieza de {len(rutas)} archivos temporales...")
    for ruta in rutas:
        try:
            if os.path.exists(ruta):
                os.remove(ruta)
                print(f"   - Borrado: {ruta}")
        except Exception as e:
            print(f"   ⚠️ Error borrando {ruta}: {e}")

# --- ENDPOINTS DE BORRADO ---

@app.delete("/reporte/{reporte_id}")
def borrar_reporte(reporte_id: int):
    try:
        # Nota: Asegúrate de que database.eliminar_reporte exista o usa una query directa
        # Si no tienes la función en database.py, puedes descomentar esto:
        # con = database.conectar()
        # con.execute("DELETE FROM reportes WHERE id = ?", (reporte_id,))
        # con.commit()
        # con.close()
        # return {"status": "ok"}
        
        # Asumiendo que existe o usando una genérica:
        con = database.conectar()
        cur = con.cursor()
        cur.execute("DELETE FROM reportes WHERE id = ?", (reporte_id,))
        filas = cur.rowcount
        con.commit()
        con.close()
        
        if filas > 0:
            return {"status": "ok", "message": "Eliminado correctamente"}
        else:
            raise HTTPException(status_code=404, detail="Reporte no encontrado")
            
    except Exception as e:
        print(f"Error borrando reporte: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/cliente/{nombre}")
def borrar_cliente(nombre: str):
    import urllib.parse
    nombre_limpio = urllib.parse.unquote(nombre)
    if database.eliminar_cliente(nombre_limpio):
        return {"status": "ok", "message": f"Cliente {nombre_limpio} eliminado"}
    raise HTTPException(status_code=404, detail="Cliente no encontrado")

@app.delete("/tecnico/{nombre}")
def borrar_tecnico(nombre: str):
    import urllib.parse
    nombre_limpio = urllib.parse.unquote(nombre)
    if database.eliminar_tecnico(nombre_limpio):
        return {"status": "ok", "message": f"Técnico {nombre_limpio} eliminado"}
    raise HTTPException(status_code=404, detail="Técnico no encontrado")

@app.delete("/usuario/{cliente}/{nombre}")
def borrar_usuario(cliente: str, nombre: str):
    import urllib.parse
    cliente_limpio = urllib.parse.unquote(cliente)
    nombre_limpio = urllib.parse.unquote(nombre)
    if database.eliminar_usuario(nombre_limpio, cliente_limpio):
        return {"status": "ok", "message": f"Usuario {nombre_limpio} eliminado"}
    raise HTTPException(status_code=404, detail="Usuario no encontrado")


@app.post("/reporte/crear")
async def crear_reporte(
    background_tasks: BackgroundTasks, 
    cliente: str = Form(...),
    tecnico: str = Form(...),
    obs: str = Form(""),
    datos_usuarios: str = Form(...), 
    email_cliente: str = Form(None), 
    email_tecnico: str = Form(None),
    firma_tecnico: UploadFile = File(None),
    fotos: List[UploadFile] = File(None),
    firmas_usuarios: List[UploadFile] = File(None) 
):
    
    archivos_para_borrar = []

    try:
        # 0. Actualizar email
        if email_cliente:
            database.agregar_cliente(cliente, email_cliente)
            config.CORREOS_POR_CLIENTE[cliente] = email_cliente

        usuarios_parsed = json.loads(datos_usuarios)
        temp_dir = config.TEMP_FOLDER
        if not os.path.exists(temp_dir): os.makedirs(temp_dir)

        # 1. Guardar Fotos
        rutas_fotos_servidor = []
        if fotos:
            for foto in fotos:
                clean_name = os.path.basename(foto.filename)
                ruta_dest = f"{temp_dir}/{clean_name}"
                with open(ruta_dest, "wb") as buffer:
                    shutil.copyfileobj(foto.file, buffer)
                rutas_fotos_servidor.append(os.path.abspath(ruta_dest))
                archivos_para_borrar.append(os.path.abspath(ruta_dest))

        # 2. Guardar Firmas
        rutas_firmas_servidor = {} 
        if firmas_usuarios:
            for firma in firmas_usuarios:
                clean_name = os.path.basename(firma.filename)
                ruta_dest = f"{temp_dir}/{clean_name}"
                with open(ruta_dest, "wb") as buffer:
                    shutil.copyfileobj(firma.file, buffer)
                rutas_firmas_servidor[clean_name] = os.path.abspath(ruta_dest)
                archivos_para_borrar.append(os.path.abspath(ruta_dest))

        # 3. Mapear rutas
        contador_fotos = 0
        for usuario in usuarios_parsed:
            if 'fotos' in usuario and isinstance(usuario['fotos'], list):
                nuevas_rutas = []
                for _ in usuario['fotos']:
                    if contador_fotos < len(rutas_fotos_servidor):
                        nuevas_rutas.append(rutas_fotos_servidor[contador_fotos])
                        contador_fotos += 1
                usuario['fotos'] = nuevas_rutas
            
            if 'firma' in usuario and usuario['firma']:
                nombre_archivo = os.path.basename(usuario['firma'])
                if nombre_archivo in rutas_firmas_servidor:
                    usuario['firma'] = rutas_firmas_servidor[nombre_archivo]
                else:
                    usuario['firma'] = None

        # 4. Generar PDF
        path_firma_tec = None 
        pdf_path = pdf_generator.generar_pdf(
            cliente=cliente,
            tecnico=tecnico,
            obs=obs,
            path_firma=path_firma_tec,
            datos_usuarios=usuarios_parsed 
        )
        if pdf_path:
            archivos_para_borrar.append(pdf_path)

        # 5. SUBIR A SHAREPOINT
        ok_sp, msg_sp, web_url = utils.subir_archivo_sharepoint(pdf_path, cliente)

        # 6. CREAR ITEM EN LISTA
        msg_lista = "Lista omitida (sin URL)"
        if ok_sp and web_url:
            datos_lista = {
                "titulo": f"Visita {cliente} - {tecnico}",
                "cliente": cliente,
                "tecnico": tecnico,
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "link": web_url
            }
            try:
                ok_lista, msg_lista = utils.crear_item_lista(datos_lista)
            except:
                msg_lista = "Error escribiendo en lista"

        # 7. ENVIAR CORREOS
        ok_email, msg_email = utils.enviar_correo_graph(pdf_path, cliente, tecnico, email_tecnico)

        # 8. Guardar en BD Local
        fecha_actual = utils.obtener_hora_chile().strftime('%Y-%m-%d %H:%M:%S')
        server_id = database.guardar_reporte(
            fecha=fecha_actual,
            cliente=cliente,
            tecnico=tecnico,
            obs=obs,
            fotos_json=json.dumps(rutas_fotos_servidor),
            pdf_path=pdf_path,
            detalles_json=json.dumps(usuarios_parsed),
            estado_envio=1 if ok_email else 0
        )

        # 9. PROGRAMAR LIMPIEZA
        background_tasks.add_task(eliminar_archivos_temporales, archivos_para_borrar)

        return {
            "status": "success",
            "server_id": server_id,
            "pdf_generated": pdf_path,
            "message": f"Email: {msg_email} | SP: {msg_sp}"
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)