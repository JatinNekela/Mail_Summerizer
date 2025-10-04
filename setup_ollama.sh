#!/bin/sh

set -e

/bin/ollama serve &
pid=$!

echo "Waiting for Ollama server to start..."
sleep 5

# Type the models you want to download here
echo "Pulling llama3 model..."
ollama pull llama3

echo "Pulling gemma:2b model..."
ollama pull gemma:2b

# You can keep or remove the embedding model as needed
# echo "Pulling nomic-embed-text model..."
# ollama pull nomic-embed-text

echo "Models downloaded."

wait $pid