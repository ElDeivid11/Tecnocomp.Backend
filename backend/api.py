import shutil
import os
import json
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
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

# Modelos
class ClienteBase(BaseModel):
    nombre: str
    email: str

class TecnicoBase(BaseModel):
    nombre: str

@app.get("/clientes")
def get_clientes(): return database.obtener_clientes()

@app.get("/tecnicos")
def get_tecnicos(): return database.obtener_tecnicos()

@app.post("/clientes")
def create_cliente(cliente: ClienteBase):
    database.agregar_cliente(cliente.nombre, cliente.email)
    return {"status": "ok"}

@app.get("/usuarios/{cliente_nombre}")
def get_usuarios(cliente_nombre: str):
    return database.obtener_usuarios_por_cliente(cliente_nombre)

# --- ENDPOINT PRINCIPAL ---
@app.post("/reporte/crear")
async def crear_reporte(
    cliente: str = Form(...),
    tecnico: str = Form(...),
    obs: str = Form(""),
    datos_usuarios: str = Form(...), 
    email_cliente: str = Form(None), 
    email_tecnico: str = Form(None), # Recibimos el email del técnico
    firma_tecnico: UploadFile = File(None),
    fotos: List[UploadFile] = File(None),
    firmas_usuarios: List[UploadFile] = File(None) 
):
    try:
        # 0. Actualizar email cliente si viene nuevo
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

        # 2. Guardar Firmas
        rutas_firmas_servidor = {} 
        if firmas_usuarios:
            for firma in firmas_usuarios:
                clean_name = os.path.basename(firma.filename)
                ruta_dest = f"{temp_dir}/{clean_name}"
                with open(ruta_dest, "wb") as buffer:
                    shutil.copyfileobj(firma.file, buffer)
                rutas_firmas_servidor[clean_name] = os.path.abspath(ruta_dest)

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

        # 5. SUBIR A SHAREPOINT (DRIVE) y obtener LINK
        ok_sp, msg_sp, web_url = utils.subir_archivo_sharepoint(pdf_path, cliente)

        # 6. CREAR ITEM EN LISTA SHAREPOINT (DASHBOARD)
        msg_lista = "Lista omitida (sin URL)"
        if ok_sp and web_url:
            datos_lista = {
                "titulo": f"Visita {cliente} - {tecnico}",
                "cliente": cliente,
                "tecnico": tecnico,
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "link": web_url
            }
            ok_lista, msg_lista = utils.crear_item_lista(datos_lista)

        # 7. ENVIAR CORREOS (Con copia al técnico si aplica)
        ok_email, msg_email = utils.enviar_correo_graph(pdf_path, cliente, tecnico, email_tecnico)

        # 8. Guardar en BD Local (Historial backend)
        fecha_actual = utils.obtener_hora_chile().strftime('%Y-%m-%d %H:%M:%S')
        database.guardar_reporte(
            fecha=fecha_actual,
            cliente=cliente,
            tecnico=tecnico,
            obs=obs,
            fotos_json=json.dumps(rutas_fotos_servidor),
            pdf_path=pdf_path,
            detalles_json=json.dumps(usuarios_parsed),
            estado_envio=1 if ok_email else 0
        )

        return {
            "status": "success",
            "pdf_generated": pdf_path,
            "message": f"Email: {msg_email} | Archivo SP: {msg_sp} | Lista SP: {msg_lista}"
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import os
    # IMPORTANTE: Render nos pasa el puerto en la variable de entorno 'PORT'.
    # Si no existe (estamos en local), usamos el 8000.
    port = int(os.environ.get("PORT", 8000))
    
    # Iniciamos Uvicorn escuchando en 0.0.0.0 y el puerto correcto
    uvicorn.run(app, host="0.0.0.0", port=port)