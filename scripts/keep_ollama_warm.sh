#!/bin/bash
# Keep Ollama model warm
while true; do
  curl -s -X POST http://localhost:11434/api/chat -H "Content-Type: application/json" -d "{\"model\":\"gemma3:4b\",\"messages\":[{\"role\":\"user\",\"content\":\"ping\"}],\"stream\":false}" > /dev/null
  sleep 300  # Every 5 minutes
done
