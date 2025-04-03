# app.py (FastAPI)
import os
import shutil
import zipfile
import subprocess
from typing import List
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from pdf2docx import Converter
from pdf2image import convert_from_path
import pytesseract
import uuid
import uvicorn

# Configurações e Diretórios
POPPLER_PATH = "/usr/bin"
WORK_DIR = "documentos"
os.makedirs(WORK_DIR, exist_ok=True)

app = FastAPI()

# Adicionar rota para servir arquivos estáticos
app.mount("/download", StaticFiles(directory=WORK_DIR), name="download")

def salvar_arquivos(uploaded_files: List[UploadFile]) -> List[str]:
    caminhos = []
    for arquivo in uploaded_files:
        nome_base, extensao = os.path.splitext(arquivo.filename)
        nome_limpo = (nome_base.replace(" ", "_")
                      .replace("\u00e7", "c").replace("\u00e3", "a")
                      .replace("\u00e1", "a").replace("\u00e9", "e")
                      .replace("\u00ed", "i").replace("\u00f3", "o")
                      .replace("\u00fa", "u").replace("\u00f1", "n")) + extensao.lower()

        caminho = os.path.join(WORK_DIR, nome_limpo)
        with open(caminho, "wb") as f:
            shutil.copyfileobj(arquivo.file, f)
        caminhos.append(caminho)
    return caminhos

@app.get("/download")
async def download_file(path: str):
    if not os.path.exists(path):
        return JSONResponse({"error": "File not found"}, status_code=404)
    return FileResponse(path)

@app.post("/word-para-pdf")
async def word_para_pdf(files: List[UploadFile] = File(...)):
    try:
        resultados = []
        caminhos = salvar_arquivos(files)
        for caminho in caminhos:
            nome_base = os.path.splitext(os.path.basename(caminho))[0]
            nome_saida = f"word_{nome_base}.pdf"
            saida = os.path.join(WORK_DIR, nome_saida)
            
            # Limpar arquivos existentes
            if os.path.exists(saida):
                os.remove(saida)
            
            # Converter usando LibreOffice
            comando = f"libreoffice --headless --convert-to pdf --outdir '{WORK_DIR}' '{caminho}'"
            resultado = subprocess.run(comando, shell=True, capture_output=True, text=True)
            
            # Verificar se a conversão foi bem-sucedida
            temp_pdf = os.path.join(WORK_DIR, f"{nome_base}.pdf")
            if os.path.exists(temp_pdf):
                os.rename(temp_pdf, saida)
                resultados.append(saida)
            else:
                return JSONResponse(
                    {"error": f"Falha na conversão de {caminho}", "details": resultado.stderr},
                    status_code=500
                )
        
        if resultados:
            if len(resultados) == 1:
                return FileResponse(resultados[0], filename=os.path.basename(resultados[0]))
            return {"arquivos": resultados}
        return JSONResponse({"error": "Nenhum arquivo foi convertido"}, status_code=500)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# ... (manter as outras rotas como estão, mas adicionar tratamento de erro similar)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
