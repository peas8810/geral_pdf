FROM python:3.10-slim

# Instalar ferramentas necessárias
RUN apt-get update && apt-get install -y \
    libreoffice \
    ghostscript \
    poppler-utils \
    tesseract-ocr \
    libgl1 \
    && apt-get clean

# Diretório de trabalho
WORKDIR /app

# Copiar dependências e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante do código
COPY . .

# Expor porta da API
EXPOSE 8000

# Comando para rodar FastAPI
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
