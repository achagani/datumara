#!/bin/bash
# Setup script for the Datumara project
# Usage: bash setup.sh

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$PROJECT_ROOT/venv"

echo "=========================================="
echo "Datumara - Environment Setup"
echo "=========================================="

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.10+ required (found $python_version)"
    exit 1
fi

echo "✅ Python version: $python_version"

# Check for CUDA (optional, but recommended)
if command -v nvidia-smi &> /dev/null; then
    echo "✅ NVIDIA GPU detected:"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | head -1
else
    echo "⚠️  No NVIDIA GPU found (training will be slow, use CPU)"
fi

# Create virtual environment
if [ ! -d "$VENV_PATH" ]; then
    echo ""
    echo "Creating virtual environment at $VENV_PATH..."
    python3 -m venv "$VENV_PATH"
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_PATH/bin/activate"

# Upgrade pip
echo "Upgrading pip, setuptools, wheel..."
pip install --upgrade pip setuptools wheel --quiet

# Install dependencies
echo "Installing dependencies from requirements.txt..."
pip install -r "$PROJECT_ROOT/requirements.txt" --quiet

echo ""
echo "=========================================="
echo "✅ Setup complete!"
echo "=========================================="
echo ""
echo "To activate the environment, run:"
echo "  source $VENV_PATH/bin/activate"
echo ""
echo "To verify installation, run:"
echo "  python poc_verification.py"
echo ""
echo "To run training, see training/README.md"
echo "=========================================="
