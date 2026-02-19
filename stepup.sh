#!/bin/bash
# setup.sh

echo "📥 Setting up Hospital AI..."

# Create models directory
mkdir -p models

# Check if model exists
if [ ! -f models/mistral-7b-openorca.gguf2.Q4_0.gguf ]; then
    echo "📥 Downloading model (this may take a few minutes)..."
    
    # Try with curl
    curl -L -o models/mistral-7b-openorca.gguf2.Q4_0.gguf \
        https://gpt4all.io/models/gguf/mistral-7b-openorca.gguf2.Q4_0.gguf
    
    # Check if download succeeded
    if [ $? -eq 0 ]; then
        echo "✅ Model downloaded successfully!"
    else
        echo "Failed to download model"
        exit 1
    fi
else
    echo "✅ Model already exists"
fi

echo "🎉 Setup complete!"