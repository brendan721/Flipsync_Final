#!/bin/bash

# FlipSync Ollama Keep-Alive Script
# Maintains Ollama models in memory for faster response times

echo "🔄 Starting Ollama keep-alive service..."

# Function to ping Ollama and keep models loaded
keep_alive() {
    while true; do
        # Ping Ollama every 30 seconds to keep models loaded
        if curl -s http://ollama-cpu:11434/api/tags > /dev/null 2>&1; then
            echo "💓 Ollama heartbeat - $(date)"
        else
            echo "⚠️ Ollama not responding - $(date)"
        fi
        sleep 30
    done
}

# Start keep-alive in background
keep_alive &

echo "✅ Ollama keep-alive service started"
