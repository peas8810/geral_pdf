import os
import shutil
import time
import zipfile
import subprocess
import uuid
import streamlit as st
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from pdf2docx import Converter
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import img2pdf

# Configurações iniciais
WORK_DIR = "documentos"
os.makedirs(WORK_DIR, exist_ok=True)

# Verifica e configura o Tesseract OCR (pode precisar de ajuste no seu sistema)
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

# Função para salvar arquivos enviados
def salvar_arquivos(uploaded_files):
    caminhos = []
    for uploaded_file in uploaded_files:
        # Limpa o nome do arquivo
        nome_base, extensao = os.path.splitext(uploaded_file.name)
        nome_limpo = (nome_base.replace(" ", "_")
                      .replace("ç", "c").replace("ã", "a")
                      .replace("á", "a").replace("é", "e")
                      .replace("í", "i").replace("ó", "o")
                      .replace("ú", "u").replace("ñ", "n")) + extensao.lower()
        
        caminho = os.path.join(WORK_DIR, nome_limpo)
        with open(caminho, "wb") as f:
            f.write(uploaded_file.getbuffer())
        caminhos.append(caminho)
    return caminhos

# Função para limpar arquivos temporários
def limpar_diretorio():
    for filename in os.listdir(WORK_DIR):
        file_path = os.path.join(WORK_DIR, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            st.error(f"Erro ao limpar arquivo {file_path}: {e}")

# Função para baixar arquivos
def criar_link_download(nome_arquivo, label):
    with open(os.path.join(WORK_DIR, nome_arquivo), "rb") as f:
        st.download_button(
            label=label,
            data=f,
            file_name=nome_arquivo,
            mime="application/octet-stream"
        )

# Funções de conversão
def pdf_para_word():
    st.header("PDF para Word")
    uploaded_file = st.file_uploader(
        "Carregue um arquivo PDF",
        type=["pdf"],
        accept_multiple_files=False
    )
    
    if uploaded_file and st.button("Converter para Word"):
        caminho = salvar_arquivos([uploaded_file])[0]
        nome_base = os.path.splitext(os.path.basename(caminho))[0]
        nome_saida = f"pdf2docx_{nome_base}.docx"
        saida = os.path.join(WORK_DIR, nome_saida)
        
        # Remove arquivo existente se houver
        if os.path.exists(saida):
            os.remove(saida)
        
        try:
            cv = Converter(caminho)
            cv.convert(saida)
            cv.close()
            
            if os.path.exists(saida):
                st.success(f"Arquivo convertido: {nome_saida}")
                criar_link_download(nome_saida, f"Baixar {nome_saida}")
            else:
                st.error(f"Falha na conversão: {caminho}")
        except Exception as e:
            st.error(f"Erro na conversão: {str(e)}")

def juntar_pdf():
    st.header("Juntar PDFs")
    uploaded_files = st.file_uploader(
        "Carregue os PDFs para juntar",
        type=["pdf"],
        accept_multiple_files=True
    )
    
    if len(uploaded_files) >= 2 and st.button("Juntar PDFs"):
        caminhos = salvar_arquivos(uploaded_files)
        nome_saida = "merge_resultado.pdf"
        saida = os.path.join(WORK_DIR, nome_saida)
        
        # Remove arquivo existente se houver
        if os.path.exists(saida):
            os.remove(saida)
        
        try:
            merger = PdfMerger()
            for c in caminhos:
                merger.append(c)
            merger.write(saida)
            merger.close()
            
            if os.path.exists(saida):
                st.success("PDFs unidos com sucesso!")
                criar_link_download(nome_saida, f"Baixar {nome_saida}")
            else:
                st.error("Falha ao unir PDFs.")
        except Exception as e:
            st.error(f"Erro ao unir PDFs: {str(e)}")

def dividir_pdf():
    st.header("Dividir PDF")
    uploaded_file = st.file_uploader(
        "Carregue um PDF para dividir",
        type=["pdf"],
        accept_multiple_files=False
    )
    
    if uploaded_file and st.button("Dividir PDF"):
        caminho = salvar_arquivos([uploaded_file])[0]
        nome_base = os.path.splitext(os.path.basename(caminho))[0]
        
        try:
            reader = PdfReader(caminho)
            for i, page in enumerate(reader.pages):
                writer = PdfWriter()
                writer.add_page(page)
                nome_saida = f"split_{nome_base}_pag{i+1}.pdf"
                out_path = os.path.join(WORK_DIR, nome_saida)
                with open(out_path, "wb") as f:
                    writer.write(f)
                st.success(f"Página gerada: {nome_saida}")
                criar_link_download(nome_saida, f"Baixar {nome_saida}")
        except Exception as e:
            st.error(f"Erro ao dividir PDF: {str(e)}")

def jpg_para_pdf():
    st.header("Imagens para PDF")
    uploaded_files = st.file_uploader(
        "Carregue imagens para converter em PDF",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )
    
    if uploaded_files and st.button("Converter para PDF"):
        caminhos = salvar_arquivos(uploaded_files)
        nome_saida = "img2pdf_resultado.pdf"
        caminho_pdf = os.path.join(WORK_DIR, nome_saida)
        
        # Remove arquivo existente se houver
        if os.path.exists(caminho_pdf):
            os.remove(caminho_pdf)
        
        try:
            # Usando img2pdf para melhor qualidade
            with open(caminho_pdf, "wb") as f:
                f.write(img2pdf.convert([Image.open(img).filename for img in caminhos]))
            
            if os.path.exists(caminho_pdf):
                st.success("PDF gerado com sucesso!")
                criar_link_download(nome_saida, f"Baixar {nome_saida}")
            else:
                st.error("Falha ao gerar PDF.")
        except Exception as e:
            st.error(f"Erro ao converter imagens para PDF: {str(e)}")


# Interface principal
def main():
    st.title("📄 Conversor de Documentos")
    st.markdown("""
    Ferramenta para conversão entre diversos formatos de documentos.
    """)
    
    # Menu lateral
    st.sidebar.title("Menu")
    opcao = st.sidebar.selectbox(
        "Selecione a operação",
        [
            "PDF para Word",
            "Juntar PDFs",
            "Dividir PDF",
            "Imagens para PDF",
         ]
    )
    
    # Limpar arquivos temporários
    if st.sidebar.button("Limpar arquivos temporários"):
        limpar_diretorio()
        st.sidebar.success("Arquivos temporários removidos!")
    
    # Rodapé
    st.sidebar.markdown("---")
    st.sidebar.markdown("Desenvolvido por PEAS.Co")
    
    # Executa a função selecionada
    if opcao == "PDF para Word":
        pdf_para_word()
    elif opcao == "Juntar PDFs":
        juntar_pdf()
    elif opcao == "Dividir PDF":
        dividir_pdf()
    elif opcao == "Imagens para PDF":
        jpg_para_pdf()


if __name__ == "__main__":
    main()


# --- Seção de Propaganda ---

 # Incorporação de website (exemplo de iframe para propaganda)
st.markdown("### Técnica PROATIVA: Domine a Criação de Comandos Poderosos na IA e gere produtos monetizáveis - https://peas8810.hotmart.host/product-page-1f2f7f92-949a-49f0-887c-5fa145e7c05d")
st.components.v1.iframe("https://pay.hotmart.com/U99934745U?off=y2b5nihy&hotfeature=51&_hi=eyJjaWQiOiIxNzQ4Mjk4OTUxODE2NzQ2NTc3ODk4OTY0NzUyNTAwIiwiYmlkIjoiMTc0ODI5ODk1MTgxNjc0NjU3Nzg5ODk2NDc1MjUwMCIsInNpZCI6ImM4OTRhNDg0MzJlYzRhZTk4MTNjMDJiYWE2MzdlMjQ1In0=.1748375599003&bid=1748375601381", height=250)

st.subheader("Técnica PROATIVA: Domine a Criação de Comandos Poderosos na IA e gere produtos monetizáveis  - https://peas8810.hotmart.host/product-page-1f2f7f92-949a-49f0-887c-5fa145e7c05d")
# Exibição de imagem para propaganda (substitua a URL pela sua imagem)
image_url = "https://static-media.hotmart.com/cu0MontuJsAjZltv6bttoE1zxbI=/filters:quality(100):format(webp)/klickart-prod/uploads/media/file/9314924/imagem_-_proativa.jpg"
st.image(image_url, caption="Anuncie aqui", use_container_width=True)
