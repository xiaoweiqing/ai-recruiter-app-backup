#!/bin/bash

# =================================================================
#    AI Recruiter - Starter Script (v33.2 - Conda Edition)
#    - Prepares the environment and launches the Python application.
#    - MODIFIED: Uses Conda instead of venv for system stability.
# =================================================================

# --- 1. Configuration ---
# CHANGE THIS if your conda environment has a different name
CONDA_ENV_NAME="ai-recruiter" 

PYTHON_SCRIPT_NAME="main.py"
CENTRAL_DB_CONTAINER_NAME="qdrant_db" # Ensure this matches your .env if hardcoded fallback is needed

# --- Color Definition Functions ---
set_theme() {
    # Sets a cyberpunk purple theme
    echo -e "\033[95m"
}
reset_colors() {
    # Resets terminal to default colors
    echo -e "\033[0m"
}

# --- Apply color theme at script start ---
set_theme

# --- CRITICAL STEP: Change to the script's directory ---
cd "$(dirname "$0")" || exit

# --- Main Script Logic ---
echo "========================================================"
echo "      AI Recruiter v33.2 - Launcher (Conda Edition)"
echo "========================================================"
echo ""

# --- Step 1: Load .env configuration file ---
echo "[1/5] Loading .env configuration..."
if [ -f .env ]; then
  # Export variables from the .env file for the current session
  export $(grep -v '^#' .env | xargs)
  echo "      > Status: ✅ .env configuration loaded and exported."
else
  echo "      > ❌ FATAL ERROR: .env configuration file not found!"
  reset_colors
  read -p "Press any key to exit..."
  exit 1
fi
echo ""

# --- Step 2: Confirm and apply network proxy ---
echo "[2/5] Applying network proxy..."
if [ -n "$HTTP_PROXY" ]; then
    echo "      > Status: ✅ Network proxy set from .env: $HTTP_PROXY"
else
    echo "      > Status: 🟡 Warning: HTTP_PROXY not found in .env file."
fi
echo ""

# --- Step 3: Activate Conda Environment (REPLACED VENV LOGIC) ---
echo "[3/5] Activating Conda environment: '${CONDA_ENV_NAME}'..."

# Attempt to locate conda.sh in common locations
CONDA_PATH=""
if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    CONDA_PATH="$HOME/miniconda3/etc/profile.d/conda.sh"
elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
    CONDA_PATH="$HOME/anaconda3/etc/profile.d/conda.sh"
elif [ -f "/opt/conda/etc/profile.d/conda.sh" ]; then
    CONDA_PATH="/opt/conda/etc/profile.d/conda.sh"
fi

if [ -n "$CONDA_PATH" ]; then
    source "$CONDA_PATH"
else
    # Fallback: hope 'conda' is already in PATH
    echo "      > ⚠️  Warning: Conda startup script not found. Relying on system PATH..."
fi

# Try to activate
conda activate "${CONDA_ENV_NAME}" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "      > Status: ✅ Conda environment '${CONDA_ENV_NAME}' activated."
else
    echo "      > ❌ FATAL ERROR: Failed to activate Conda environment '${CONDA_ENV_NAME}'."
    echo "      > Please run: 'conda create -n ${CONDA_ENV_NAME} python=3.11' first."
    reset_colors
    read -p "Press any key to exit..."
    exit 1
fi
echo ""

# --- Step 4: Install/Update Python dependencies ---
echo "[4/5] Installing/Updating Python dependencies..."
if [ ! -f "requirements.txt" ]; then
    echo "      > ❌ FATAL ERROR: 'requirements.txt' file not found!"
    reset_colors
    read -p "Press any key to exit..."
    exit 1
fi

# Use the 'pip' from the activated Conda environment
pip install -r requirements.txt &> /dev/null

if [ $? -ne 0 ]; then
    echo "      > ❌ Installation failed. Retrying with verbose output..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "      > ❌ FATAL ERROR: Failed to install Python dependencies!"
        reset_colors
        read -p "Press any key to exit..."
        exit 1
    fi
fi
echo "      > Status: ✅ Python dependencies are up-to-date."
echo ""

# --- Step 5: Check and ensure Qdrant database is running ---
# Fallback to variable inside script if .env didn't load it
DB_NAME=${CENTRAL_DB_CONTAINER_NAME:-"qdrant_db"} 

echo "[5/5] Checking Qdrant database (${DB_NAME}) status..."

if docker ps -q -f name=^/${DB_NAME}$ | grep -q .; then
    echo "      > Status: ✅ Qdrant database is running."
elif docker ps -aq -f name=^/${DB_NAME}$ | grep -q .; then
    echo "      > Detected stopped Qdrant container. Attempting to start it..."
    docker start ${DB_NAME} > /dev/null
    echo "      > Status: ✅ Qdrant database started successfully."
else
    echo "      > ❌ FATAL ERROR: Docker container named '${DB_NAME}' not found!"
    reset_colors
    read -p "Press any key to exit..."
    exit 1
fi
echo ""

# --- Final Step: Launch the main Python application ---
echo ">>> Launching Python application (${PYTHON_SCRIPT_NAME})..."
echo "-------------------------- [ Program Log Start ] --------------------------"
echo ""

# We use simple 'python' here because Conda is activated
python "${PYTHON_SCRIPT_NAME}"

# --- Script End ---
echo ""
echo "-------------------------- [ Program Log End ] --------------------------"
echo "The program has finished."
reset_colors
read -p "Press any key to close this terminal..."
