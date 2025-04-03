# Dockerfile compatível com Render + LibreOffice
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Instala dependências básicas e ferramentas
RUN apt-get update && \
    apt-get install -y \
    libreoffice \
    ghostscript \
    poppler-utils \
    tesseract-ocr \
    python3-pip \
    python3-dev \
    python3-setuptools \
    python3-wheel \
    libgl1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Define diretório de trabalho
WORKDIR /app

# Copia requirements e instala dependências Python
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copia o restante do código
COPY . .

# Garante que a pasta de trabalho existe
RUN mkdir -p documentos

# Expõe a porta
EXPOSE 8000

# Comando de inicialização
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
