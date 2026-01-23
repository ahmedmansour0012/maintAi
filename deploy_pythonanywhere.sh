#!/bin/bash
# PythonAnywhere Deployment Script
# Run this in PythonAnywhere Bash console

echo "=== Video Repair Assistant - PythonAnywhere Deployment ==="
echo ""

# Configuration
PROJECT_NAME="video_rag"
HOME_DIR="/home/ahmedmansour0022"
PROJECT_DIR="$HOME_DIR/$PROJECT_NAME"
VENV_DIR="$HOME_DIR/.virtualenvs/video_rag_env"
PYTHON_VERSION="3.10"

# Step 1: Create virtual environment
echo "[1/6] Creating virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    mkvirtualenv video_rag_env --python=/usr/bin/python$PYTHON_VERSION
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Step 2: Clone/Update project (if using git) or check if files exist
echo "[2/6] Setting up project directory..."
if [ ! -d "$PROJECT_DIR" ]; then
    mkdir -p "$PROJECT_DIR"
    echo "Created $PROJECT_DIR - Please upload your project files"
fi

cd "$PROJECT_DIR"

# Step 3: Install dependencies
echo "[3/6] Installing dependencies..."
if [ -f "requirements_pythonanywhere.txt" ]; then
    pip install -r requirements_pythonanywhere.txt
else
    echo "Warning: requirements_pythonanywhere.txt not found"
    echo "Please upload it first"
fi

# Step 4: Create .env file template if not exists
echo "[4/6] Checking .env file..."
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "Creating .env template..."
    cat > "$PROJECT_DIR/.env" << 'EOF'
# Video Repair Assistant Configuration
# Fill in your API keys below

GEMINI_API_KEY=your_gemini_key_here
GEMINI_MODEL=gemini-2.5-pro
MAX_VIDEO_BYTES=26214400

# ElevenLabs (optional for voice features)
ELEVENLABS_API_KEY=your_elevenlabs_key_here
ELEVENLABS_API_KEY_WRITE=your_elevenlabs_write_key_here
ELEVENLABS_AGENT_ID=your_agent_id_here
ELEVENLABS_KNOWLEDGE_BASE_ID=your_kb_id_here

DEFAULT_FOLLOWUP_MODE=troubleshooting
AUTO_SYNC_KB=false
EOF
    echo "Created .env template - PLEASE EDIT WITH YOUR API KEYS"
else
    echo ".env file exists"
fi

# Step 5: Verify installation
echo "[5/6] Verifying installation..."
python -c "from app.main import app; print('FastAPI app imported successfully')" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ FastAPI app loads correctly"
else
    echo "❌ Error loading FastAPI app - check your imports"
fi

# Step 6: Instructions for WSGI setup
echo ""
echo "[6/6] Final Setup Instructions"
echo "================================"
echo ""
echo "1. Go to Web tab in PythonAnywhere dashboard"
echo ""
echo "2. Set these values:"
echo "   - Source code: $PROJECT_DIR"
echo "   - Working directory: $PROJECT_DIR"
echo "   - Virtualenv: $VENV_DIR"
echo ""
echo "3. Click on 'WSGI configuration file' link and replace ALL content with:"
echo "   (Copy from $PROJECT_DIR/pythonanywhere_wsgi.py)"
echo ""
echo "4. Edit your .env file with real API keys:"
echo "   nano $PROJECT_DIR/.env"
echo ""
echo "5. Click 'Reload' button on Web tab"
echo ""
echo "Your app will be available at: https://ahmedmansour0022.pythonanywhere.com"
echo ""
echo "=== Deployment script complete ==="
