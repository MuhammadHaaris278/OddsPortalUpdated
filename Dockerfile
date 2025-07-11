# Use a slim Python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# System packages needed by Playwright + Chromium
RUN apt-get update && apt-get install -y \
    wget curl unzip xvfb libnss3 libatk-bridge2.0-0 \
    libxss1 libasound2 libgbm1 libgtk-3-0 libdrm2 \
    && apt-get clean

# Install Python packages and Playwright
RUN pip install --upgrade pip && pip install playwright && playwright install --with-deps

# Install the rest of the Python requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Add your source code
COPY . /app
WORKDIR /app

# Expose the port Streamlit uses
EXPOSE 8501

# Launch Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
