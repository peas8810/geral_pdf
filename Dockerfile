FROM python:3.10-slim

# Instalar ferramentas necessárias
RUN apt-get update && apt-get install -y \
    libreoffice \
    ghostscript \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-por \  # Adicionar suporte a português
    libgl1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Configurar locale para UTF-8
RUN apt-get update && apt-get install -y locales && rm -rf /var/lib/apt/lists/* \
    && localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8
ENV LANG en_US.utf8

# Diretório de trabalho
WORKDIR /app

# Copiar dependências e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante do código
COPY . .

# Criar diretório para documentos
RUN mkdir -p /app/documentos

# Expor porta da API
EXPOSE 8000

# Comando para rodar FastAPI
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
