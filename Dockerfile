# Use slim Python base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_ROOT_USER_ACTION=ignore

# Install system dependencies required by Chromium
RUN apt-get update && apt-get install -y \
    wget curl unzip xvfb libnss3 libatk-bridge2.0-0 \
    libxss1 libasound2 libgbm1 libgtk-3-0 libdrm2 \
    && apt-get clean

# Install Python and Playwright packages
COPY requirements.txt .
RUN pip install --upgrade pip --no-cache-dir \
    && pip install -r requirements.txt --no-cache-dir \
    && pip install playwright --no-cache-dir

# Copy application code
COPY . /app
WORKDIR /app

# Expose Streamlit port
EXPOSE 8501

# ✅ RUNTIME FIX: install Chromium browser before launching Streamlit
CMD ["bash", "-c", "playwright install chromium && streamlit run app.py --server.port=8501 --server.address=0.0.0.0"]
