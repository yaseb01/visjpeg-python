#!/usr/bin/env bash
set -e

# Detect OS
OS="unknown"
case "$(uname -s)" in
    Linux*)     OS="linux";;
    Darwin*)    OS="macos";;
    CYGWIN*|MINGW*|MSYS*) OS="windows";;
esac

echo "Detected OS: $OS"
echo ""

# Build image if needed
build_if_needed() {
    if ! docker images | grep -q "visjpeg-python"; then
        echo "Building Docker image..."
        docker build -t visjpeg-python .
        echo ""
    fi
}

# Function to run with X11 forwarding
run_x11() {
    echo "Running VisJPEG with X11 forwarding..."
    build_if_needed

    if [ "$OS" = "macos" ]; then
        # Check if XQuartz is installed
        if ! command -v xquartz &> /dev/null && [ ! -d /Applications/Utilities/XQuartz.app ]; then
            echo "ERROR: XQuartz is not installed."
            echo "Install it with: brew install --cask xquartz"
            echo "Or download from: https://www.xquartz.org/"
            echo ""
            echo "Alternatively, run: $0 vnc"
            exit 1
        fi

        # Start XQuartz if not running
        open -a XQuartz

        # Allow connections from Docker
        xhost + $(hostname) 2>/dev/null || xhost +localhost 2>/dev/null || xhost + 2>/dev/null

        # On macOS, Docker Desktop uses a VM; we need to use host.docker.internal
        export DISPLAY=host.docker.internal:0
        docker run --rm -it \
            -e DISPLAY=$DISPLAY \
            -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
            -v "$(pwd)/visjpeg:/app/visjpeg:ro" \
            visjpeg-python \
            sh -c "python3 /app/run.py"
    else
        # Linux
        xhost +local:docker 2>/dev/null || xhost + 2>/dev/null
        docker run --rm -it \
            -e DISPLAY=$DISPLAY \
            -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
            -v "$(pwd)/visjpeg:/app/visjpeg:ro" \
            visjpeg-python \
            sh -c "python3 /app/run.py"
    fi
}

# Function to run with VNC (works on any OS)
run_vnc() {
    echo "Running VisJPEG with VNC (no X11 required)..."
    build_if_needed

    # Check if container already running
    if docker ps | grep -q visjpeg-vnc; then
        echo "VisJPEG VNC container is already running!"
        echo "Open: http://localhost:6080"
        exit 0
    fi

    docker run --rm -d \
        --name visjpeg-vnc \
        -p 6080:6080 \
        -v "$(pwd)/visjpeg:/app/visjpeg:ro" \
        visjpeg-python \
        bash -c "
            echo 'Starting VNC server on :99...'
            vncserver :99 -geometry 1024x768 -depth 24 -localhost no -PasswordFile ~/.vnc/passwd
            echo 'Starting noVNC on port 6080...'
            websockify --web=/usr/share/novnc --cert=none --ssl-only=false 6080 localhost:5999 &
            sleep 2
            echo 'Starting VisJPEG...'
            export DISPLAY=:99
            python3 /app/run.py
        "

    echo ""
    echo "========================================"
    echo "VisJPEG VNC container started!"
    echo "Open your browser and go to:"
    echo "  http://localhost:6080/vnc.html"
    echo ""
    echo "Password: password"
    echo "========================================"
    echo ""
    echo "To stop the container, run:"
    echo "  docker stop visjpeg-vnc"
}

# Function to run headless (xvfb, for testing)
run_headless() {
    echo "Running VisJPEG headless (xvfb)..."
    build_if_needed
    docker run --rm -it \
        -v "$(pwd)/visjpeg:/app/visjpeg:ro" \
        visjpeg-python
}

# Main menu
if [ "$1" = "vnc" ]; then
    run_vnc
elif [ "$1" = "x11" ]; then
    run_x11
elif [ "$1" = "headless" ]; then
    run_headless
else
    echo "VisJPEG Docker Runner"
    echo "====================="
    echo ""
    echo "Usage: $0 [x11|vnc|headless]"
    echo ""
    echo "Options:"
    echo "  x11       - Run with X11 forwarding (native GUI)"
    echo "              macOS: requires XQuartz (brew install --cask xquartz)"
    echo "              Linux: requires X server (usually built-in)"
    echo "  vnc       - Run with VNC via browser (works on any OS)"
    echo "              Open http://localhost:6080/vnc.html after starting"
    echo "  headless  - Run with virtual framebuffer (no GUI visible)"
    echo ""

    # Auto-suggest
    if [ "$OS" = "linux" ]; then
        echo "Linux detected. Recommended: $0 x11"
    elif [ "$OS" = "macos" ]; then
        if command -v xquartz &> /dev/null || [ -d /Applications/Utilities/XQuartz.app ]; then
            echo "XQuartz detected. Recommended: $0 x11"
        else
            echo "No XQuartz detected. Recommended: $0 vnc"
        fi
    else
        echo "Recommended for your OS: $0 vnc"
    fi
fi
