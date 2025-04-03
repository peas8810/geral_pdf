RUN apt-get update && apt-get install -y \
    wget \
    gnupg2 \
    software-properties-common \
    && wget -qO- https://deb.nodesource.com/setup_16.x | bash - \
    && add-apt-repository -y ppa:libreoffice/ppa \
    && apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-writer \
    libreoffice-calc \
    ghostscript \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-por \
    libgl1 \
    libsm6 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/documentos

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
