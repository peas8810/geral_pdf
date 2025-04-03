# app.py (FastAPI)
import os
import shutil
import subprocess
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from pdf2docx import Converter
from pdf2image import convert_from_path
import pytesseract

# Configurações e Diretórios
POPPLER_PATH = "/usr/bin"
WORK_DIR = "documentos"
os.makedirs(WORK_DIR, exist_ok=True)

app = FastAPI()

# Servir arquivos estáticos
app.mount("/static", StaticFiles(directory=WORK_DIR), name="static")

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

@app.get("/")
async def root():
    return {"message": "API de Conversão de Documentos"}

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
            try:
                comando = [
                    "libreoffice", 
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
                
                # Verificar se o arquivo foi criado
                temp_pdf = os.path.join(WORK_DIR, f"{nome_base}.pdf")
                if os.path.exists(temp_pdf):
                    os.rename(temp_pdf, saida)
                    resultados.append(f"/static/{nome_saida}")
                else:
                    raise Exception("Arquivo de saída não foi gerado")
                    
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Falha na conversão de {caminho}: {str(e)}"
                )
        
        if not resultados:
            raise HTTPException(
                status_code=500,
                detail="Nenhum arquivo foi convertido"
            )
            
        if len(resultados) == 1:
            return FileResponse(
                resultados[0].replace("/static/", WORK_DIR + "/"),
                filename=os.path.basename(resultados[0])
            )
        return {"arquivos": resultados}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )

# ... (manter as outras rotas com o mesmo padrão de tratamento de erros)

@app.post("/pdf-para-word")
async def pdf_para_word(file: UploadFile = File(...)):
    try:
        caminhos = salvar_arquivos([file])
        caminho = caminhos[0]
        nome_base = os.path.splitext(os.path.basename(caminho))[0]
        saida = os.path.join(WORK_DIR, f"pdf2docx_{nome_base}.docx")
        
        if os.path.exists(saida):
            os.remove(saida)
            
        try:
            cv = Converter(caminho)
            cv.convert(saida)
            cv.close()
            
            if not os.path.exists(saida):
                raise Exception("Arquivo de saída não foi gerado")
                
            return FileResponse(
                saida,
                filename=os.path.basename(saida),
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Falha na conversão: {str(e)}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
