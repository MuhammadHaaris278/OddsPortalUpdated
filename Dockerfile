FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_ROOT_USER_ACTION=ignore

# System packages needed by Playwright Chromium
RUN apt-get update && apt-get install -y \
    wget curl unzip xvfb libnss3 libatk-bridge2.0-0 \
    libxss1 libasound2 libgbm1 libgtk-3-0 libdrm2 \
    && apt-get clean

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip --no-cache-dir \
 && pip install -r requirements.txt --no-cache-dir \
 && pip install playwright --no-cache-dir

# 👇 FORCE Playwright to install required browser binaries at build time
RUN playwright install chromium --with-deps

# Copy rest of the code
COPY . /app
WORKDIR /app

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
