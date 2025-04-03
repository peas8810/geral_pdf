# app.py (FastAPI)
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import os
import subprocess
import shutil

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "API de Conversão de Documentos - Online"}

@app.post("/word-para-pdf")
async def word_para_pdf(files: List[UploadFile] = File(...)):
    try:
        # Verificar se o LibreOffice está disponível
        libreoffice_path = shutil.which("libreoffice")
        if not libreoffice_path:
            raise HTTPException(
                status_code=500,
                detail="LibreOffice não está instalado ou não está no PATH"
            )
        
        # Restante do código de conversão...
        comando = [
            libreoffice_path,
            "--headless",
            "--convert-to", "pdf",
            "--outdir", WORK_DIR,
            caminho
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro na conversão: {str(e)}"
        )
