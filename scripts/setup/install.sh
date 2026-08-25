#!/bin/bash
set -e

echo "⚡ Installing Datumara Local..."
echo ""

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed."
    echo ""
    echo "Please install Ollama first:"
    echo "  curl -fsSL https://ollama.com/install.sh | sh"
    echo ""
    exit 1
fi

echo "✓ Ollama detected"

# Pull the model
echo ""
echo "⬇️  Downloading Datumara Local model..."
ollama pull datumara-local

echo ""
echo "✅ Datumara installed successfully!"
echo ""
echo "Start using it with:"
echo "  ollama run datumara-local"
echo ""
echo "Example:"
echo "  ollama run datumara-local \"Return only SQL: show all users\""
