#!/bin/sh
set -e

MODEL="${MODEL:-qwen3:0.6b}"

echo "[qwen3] Iniciando servidor Ollama..."
ollama serve &
pid=$!

echo "[qwen3] Esperando a que Ollama esté listo..."
i=0
while [ "$i" -lt 60 ]; do
  if ollama list >/dev/null 2>&1; then
    break
  fi
  i=$((i + 1))
  sleep 1
done

if ! ollama list >/dev/null 2>&1; then
  echo "[qwen3] Error: Ollama no respondió a tiempo."
  kill "$pid" 2>/dev/null || true
  exit 1
fi

echo "[qwen3] Descargando / verificando modelo ${MODEL}..."
ollama pull "$MODEL"
echo "[qwen3] Modelo listo. API en :11434"

trap 'kill "$pid" 2>/dev/null || true' TERM INT
wait "$pid"
