import shutil
import os
import json
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

# Importamos tus módulos existentes
import database
import utils
import pdf_generator
import config

app = FastAPI(title="Tecnocomp API")

# Inicializamos la DB al arrancar
database.inicializar_db()

# Modelos de datos para recibir JSON (Pydantic)
class ClienteBase(BaseModel):
    nombre: str
    email: str

class TecnicoBase(BaseModel):
    nombre: str

# --- ENDPOINTS DE CONFIGURACIÓN ---

@app.get("/clientes")
def get_clientes():
    return database.obtener_clientes()

@app.get("/tecnicos")
def get_tecnicos():
    return database.obtener_tecnicos()

@app.post("/clientes")
def create_cliente(cliente: ClienteBase):
    exito = database.agregar_cliente(cliente.nombre, cliente.email)
    if not exito: raise HTTPException(status_code=400, detail="Error al crear cliente")
    return {"status": "ok"}

@app.get("/usuarios/{cliente_nombre}")
def get_usuarios(cliente_nombre: str):
    return database.obtener_usuarios_por_cliente(cliente_nombre)

# --- ENDPOINT PRINCIPAL: CREAR REPORTE ---
# Modificado para recibir email_cliente, firmas y arreglar rutas de fotos
@app.post("/reporte/crear")
async def crear_reporte(
    cliente: str = Form(...),
    tecnico: str = Form(...),
    obs: str = Form(""),
    datos_usuarios: str = Form(...), 
    email_cliente: str = Form(None), # <--- NUEVO CAMPO: Recibimos el email desde la App
    firma_tecnico: UploadFile = File(None),
    fotos: List[UploadFile] = File(None),
    firmas_usuarios: List[UploadFile] = File(None) 
):
    try:
        # 0. REGISTRO AUTOMÁTICO DE CLIENTE NUEVO (O ACTUALIZACIÓN DE EMAIL)
        # Si la app nos manda un email, nos aseguramos de que el cliente exista en la DB del servidor
        if email_cliente:
            database.agregar_cliente(cliente, email_cliente)
            # Actualizamos la configuración en memoria para que utils.py lo vea inmediatamente
            config.CORREOS_POR_CLIENTE[cliente] = email_cliente

        usuarios_parsed = json.loads(datos_usuarios)
        temp_dir = "temp_uploads"
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

        # 2. Guardar Firmas de Usuarios
        rutas_firmas_servidor = {} 
        if firmas_usuarios:
            for firma in firmas_usuarios:
                clean_name = os.path.basename(firma.filename)
                ruta_dest = f"{temp_dir}/{clean_name}"
                with open(ruta_dest, "wb") as buffer:
                    shutil.copyfileobj(firma.file, buffer)
                rutas_firmas_servidor[clean_name] = os.path.abspath(ruta_dest)

        # 3. Mapear rutas JSON -> Rutas Servidor
        contador_fotos = 0
        
        for usuario in usuarios_parsed:
            # A. Arreglar rutas de FOTOS
            if 'fotos' in usuario and isinstance(usuario['fotos'], list):
                nuevas_rutas = []
                for _ in usuario['fotos']:
                    if contador_fotos < len(rutas_fotos_servidor):
                        nuevas_rutas.append(rutas_fotos_servidor[contador_fotos])
                        contador_fotos += 1
                usuario['fotos'] = nuevas_rutas
            
            # B. Arreglar ruta de FIRMA
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

        # 5. Guardar en DB y Enviar
        fecha_actual = utils.obtener_hora_chile().strftime('%Y-%m-%d %H:%M:%S')
        database.guardar_reporte(
            fecha=fecha_actual,
            cliente=cliente,
            tecnico=tecnico,
            obs=obs,
            fotos_json=json.dumps(rutas_fotos_servidor),
            pdf_path=pdf_path,
            detalles_json=json.dumps(usuarios_parsed),
            estado_envio=0
        )

        # Enviar emails
        # Intentamos obtener el email actualizado
        email_dest = database.obtener_correo_cliente(cliente)
        if email_dest:
            config.CORREOS_POR_CLIENTE[cliente] = email_dest
        
        ok_email, msg_email = utils.enviar_correo_graph(pdf_path, cliente, tecnico)
        ok_sp, msg_sp = utils.subir_archivo_sharepoint(pdf_path, cliente)

        return {
            "status": "success",
            "pdf_generated": pdf_path,
            "message": f"Email: {msg_email} | SP: {msg_sp}"
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)