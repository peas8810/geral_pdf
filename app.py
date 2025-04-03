# app.py
import os
import shutil
import subprocess
from typing import List
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from PIL import Image
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from pdf2docx import Converter
from pdf2image import convert_from_path
import pytesseract

POPPLER_PATH = "/usr/bin"
WORK_DIR = "documentos"
os.makedirs(WORK_DIR, exist_ok=True)

app = FastAPI()

@app.get("/")
def root():
    return {"mensagem": "API funcionando com sucesso 🚀"}

@app.get("/status")
def status():
    return {"status": "API online"}

def salvar_arquivos(uploaded_files: List[UploadFile]) -> List[str]:
    caminhos = []
    for arquivo in uploaded_files:
        nome_base, extensao = os.path.splitext(arquivo.filename)
        nome_limpo = nome_base.replace(" ", "_") + extensao.lower()
        caminho = os.path.join(WORK_DIR, nome_limpo)
        with open(caminho, "wb") as f:
            shutil.copyfileobj(arquivo.file, f)
        caminhos.append(caminho)
    return caminhos

@app.post("/pdf-para-word")
def pdf_para_word(file: UploadFile = File(...)):
    try:
        caminho = salvar_arquivos([file])[0]
        nome_base = os.path.splitext(os.path.basename(caminho))[0]
        saida = os.path.join(WORK_DIR, f"pdf2docx_{nome_base}.docx")
        if os.path.exists(saida): os.remove(saida)
        cv = Converter(caminho)
        cv.convert(saida)
        cv.close()
        return FileResponse(saida, filename=os.path.basename(saida))
    except Exception as e:
        return JSONResponse(content={"erro": str(e)}, status_code=500)

@app.post("/jpg-para-pdf")
def jpg_para_pdf(files: List[UploadFile] = File(...)):
    try:
        caminhos = salvar_arquivos(files)
        imagens = [Image.open(c).convert("RGB") for c in caminhos]
        nome_saida = "img2pdf_resultado.pdf"
        saida = os.path.join(WORK_DIR, nome_saida)
        imagens[0].save(saida, save_all=True, append_images=imagens[1:])
        return FileResponse(saida, filename=nome_saida)
    except Exception as e:
        return JSONResponse(content={"erro": str(e)}, status_code=500)

@app.post("/juntar-pdfs")
def juntar_pdfs(files: List[UploadFile] = File(...)):
    try:
        caminhos = salvar_arquivos(files)
        merger = PdfMerger()
        for caminho in caminhos:
            merger.append(caminho)
        saida = os.path.join(WORK_DIR, "merge_resultado.pdf")
        merger.write(saida)
        merger.close()
        return FileResponse(saida, filename="merge_resultado.pdf")
    except Exception as e:
        return JSONResponse(content={"erro": str(e)}, status_code=500)

@app.post("/dividir-pdf")
def dividir_pdf(file: UploadFile = File(...)):
    try:
        caminho = salvar_arquivos([file])[0]
        reader = PdfReader(caminho)
        arquivos = []
        for i, page in enumerate(reader.pages):
            writer = PdfWriter()
            writer.add_page(page)
            saida = os.path.join(WORK_DIR, f"split_pag{i+1}.pdf")
            with open(saida, "wb") as f:
                writer.write(f)
            arquivos.append(saida)
        return {"arquivos": arquivos}
    except Exception as e:
        return JSONResponse(content={"erro": str(e)}, status_code=500)

@app.post("/ocr-pdf")
def ocr_pdf(file: UploadFile = File(...)):
    try:
        if not shutil.which("tesseract"):
            return JSONResponse(content={"erro": "Tesseract não está instalado."}, status_code=500)

        caminho = salvar_arquivos([file])[0]
        imagens = convert_from_path(caminho, poppler_path=POPPLER_PATH)
        texto = ""
        for i, img in enumerate(imagens):
            texto += f"\n\n--- Página {i+1} ---\n\n"
            texto += pytesseract.image_to_string(img, lang="por")
        saida = os.path.join(WORK_DIR, "ocrpdf_resultado.txt")
        with open(saida, "w", encoding="utf-8") as f:
            f.write(texto)
        return FileResponse(saida, filename="ocrpdf_resultado.txt")
    except Exception as e:
        return JSONResponse(content={"erro": str(e)}, status_code=500)

@app.post("/ocr-imagem")
def ocr_imagem(files: List[UploadFile] = File(...)):
    try:
        if not shutil.which("tesseract"):
            return JSONResponse(content={"erro": "Tesseract não está instalado."}, status_code=500)

        caminhos = salvar_arquivos(files)
        texto = ""
        for i, caminho in enumerate(caminhos):
            img = Image.open(caminho)
            texto += f"\n\n--- Imagem {i+1} ---\n\n"
            texto += pytesseract.image_to_string(img, lang="por")
        saida = os.path.join(WORK_DIR, "ocrimg_resultado.txt")
        with open(saida, "w", encoding="utf-8") as f:
            f.write(texto)
        return FileResponse(saida, filename="ocrimg_resultado.txt")
    except Exception as e:
        return JSONResponse(content={"erro": str(e)}, status_code=500)

@app.post("/pdf-para-pdfa")
def pdf_para_pdfa(file: UploadFile = File(...)):
    try:
        caminho = salvar_arquivos([file])[0]
        nome_saida = os.path.join(WORK_DIR, "pdfa_resultado.pdf")
        comando = [
            "/usr/bin/gs", "-dPDFA=2", "-dBATCH", "-dNOPAUSE", "-dNOOUTERSAVE",
            "-sProcessColorModel=DeviceRGB", "-sDEVICE=pdfwrite",
            "-sPDFACompatibilityPolicy=1", f"-sOutputFile={nome_saida}", caminho
        ]
        resultado = subprocess.run(comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if os.path.exists(nome_saida) and resultado.returncode == 0:
            return FileResponse(nome_saida, filename="pdfa_resultado.pdf")
        return JSONResponse(content={"erro": "Falha ao converter para PDF/A"}, status_code=500)
    except Exception as e:
        return JSONResponse(content={"erro": str(e)}, status_code=500)
