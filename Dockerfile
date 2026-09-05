FROM python:3.11-slim

# Install system dependencies: tkinter, X11, VNC, noVNC, and fonts
RUN apt-get update && apt-get install -y \
    python3-tk \
    tk-dev \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxtst6 \
    libxi6 \
    libxft2 \
    libfreetype6 \
    libfontconfig1 \
    fonts-dejavu \
    # VNC + noVNC dependencies
    tigervnc-standalone-server \
    tigervnc-viewer \
    novnc \
    websockify \
    # Xvfb for headless fallback
    xvfb \
    # utilities
    net-tools \
    procps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY visjpeg/ ./visjpeg/
COPY run.py .

# Create a non-root user for running the app
RUN useradd -m -s /bin/bash visjpeg
RUN chown -R visjpeg:visjpeg /app
USER visjpeg

# Create VNC password directory
RUN mkdir -p ~/.vnc && echo "password" | vncpasswd -f > ~/.vnc/passwd && chmod 600 ~/.vnc/passwd

ENV DISPLAY=:99

# Default: run with xvfb (headless); override via docker run command for X11 or VNC
CMD ["sh", "-c", "Xvfb :99 -screen 0 1024x768x24 & sleep 1 && python3 run.py"]
