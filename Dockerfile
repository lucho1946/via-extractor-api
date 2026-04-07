# =============================
# IMAGEN BASE
# =============================
FROM python:3.11-slim

# =============================
# VARIABLES DE ENTORNO
# =============================
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# =============================
# DIRECTORIO DE TRABAJO
# =============================
WORKDIR /app

# =============================
# INSTALAR DEPENDENCIAS DEL SISTEMA (PLAYWRIGHT)
# =============================
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libnss3 \
    libatk-bridge2.0-0 \
    libxkbcommon0 \
    libgtk-3-0 \
    libasound2 \
    libxshmfence1 \
    libgbm1 \
    libdrm2 \
    libxrandr2 \
    libxdamage1 \
    libxfixes3 \
    libxcomposite1 \
    libxcursor1 \
    libxi6 \
    libxtst6 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# =============================
# INSTALAR DEPENDENCIAS PYTHON
# =============================
COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# =============================
# INSTALAR PLAYWRIGHT
# =============================
RUN pip install playwright
RUN playwright install --with-deps

# =============================
# COPIAR PROYECTO
# =============================
COPY . .

# =============================
# PUERTO (RENDER)
# =============================
EXPOSE 10000

# =============================
# COMANDO DE INICIO
# =============================
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "10000"]