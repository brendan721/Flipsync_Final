#!/bin/bash

# FlipSync Ollama Model Preloading Script
# Ensures required AI models are available for the FlipSync agents

echo "🔄 Preloading Ollama models for FlipSync..."

# Wait for Ollama service to be ready
echo "⏳ Waiting for Ollama service..."
for i in {1..30}; do
    if curl -s http://ollama-cpu:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama service is ready"
        break
    fi
    echo "⏳ Waiting for Ollama... ($i/30)"
    sleep 2
done

# Check if Ollama is accessible
if ! curl -s http://ollama-cpu:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️ Ollama service not accessible, continuing without preloading"
    exit 0
fi

# List of models to preload for FlipSync agents
MODELS=(
    "gemma3:4b"
    "gemma3:4b"
)

# Function to pull model if not exists
pull_model() {
    local model=$1
    echo "🔍 Checking model: $model"
    
    # Check if model exists
    if curl -s http://ollama-cpu:11434/api/tags | grep -q "\"name\":\"$model\""; then
        echo "✅ Model $model already exists"
    else
        echo "📥 Pulling model: $model"
        curl -X POST http://ollama-cpu:11434/api/pull \
            -H "Content-Type: application/json" \
            -d "{\"name\":\"$model\"}" \
            --max-time 300 || echo "⚠️ Failed to pull $model"
    fi
}

# Preload models
for model in "${MODELS[@]}"; do
    pull_model "$model"
done

echo "🎉 Ollama model preloading completed"
