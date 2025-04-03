from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from typing import List  # Importação adicionada
import os
import shutil
import subprocess
import uuid
from pdf2docx import Converter
from pdf2image import convert_from_path
import pytesseract
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from PIL import Image

# Configurações
POPPLER_PATH = "/usr/bin"
WORK_DIR = "documentos"
os.makedirs(WORK_DIR, exist_ok=True)

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "API de conversão de documentos operacional"}

def salvar_arquivos(uploaded_files: List[UploadFile]) -> List[str]:
    caminhos = []
    for arquivo in uploaded_files:
        try:
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
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao salvar arquivo: {str(e)}")
    return caminhos

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

        resultados = []
        caminhos = salvar_arquivos(files)
        
        for caminho in caminhos:
            nome_base = os.path.splitext(os.path.basename(caminho))[0]
            nome_saida = f"word_{nome_base}.pdf"
            saida = os.path.join(WORK_DIR, nome_saida)
            
            if os.path.exists(saida):
                os.remove(saida)
            
            try:
                comando = [
                    libreoffice_path,
                    "--headless",
                    "--convert-to", "pdf",
                    "--outdir", WORK_DIR,
                    caminho
                ]
                resultado = subprocess.run(
                    comando, 
                    capture_output=True, 
                    text=True,
                    timeout=30
                )
                
                if resultado.returncode != 0:
                    raise Exception(resultado.stderr)
                
                temp_pdf = os.path.join(WORK_DIR, f"{nome_base}.pdf")
                if os.path.exists(temp_pdf):
                    os.rename(temp_pdf, saida)
                    resultados.append(saida)
                else:
                    raise Exception("Arquivo de saída não foi gerado")
                    
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Falha na conversão de {os.path.basename(caminho)}: {str(e)}"
                )
        
        if not resultados:
            raise HTTPException(
                status_code=500,
                detail="Nenhum arquivo foi convertido"
            )
            
        if len(resultados) == 1:
            return FileResponse(
                resultados[0],
                filename=os.path.basename(resultados[0])
        return {"arquivos": resultados}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )

# ... (adicionar aqui as outras rotas com o mesmo padrão)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
