#!/bin/sh
set -e

MODEL="${MODEL:-phi4-mini}"

echo "[phi4] Iniciando servidor Ollama (1 modelo, ctx=${OLLAMA_CONTEXT_LENGTH:-2048})..."
ollama serve &
pid=$!

echo "[phi4] Esperando a que Ollama esté listo..."
i=0
while [ "$i" -lt 60 ]; do
  if ollama list >/dev/null 2>&1; then
    break
  fi
  i=$((i + 1))
  sleep 1
done

if ! ollama list >/dev/null 2>&1; then
  echo "[phi4] Error: Ollama no respondió a tiempo."
  kill "$pid" 2>/dev/null || true
  exit 1
fi

echo "[phi4] Descargando / verificando modelo ${MODEL}..."
ollama pull "$MODEL"
echo "[phi4] Modelo listo. API en :11434"

trap 'kill "$pid" 2>/dev/null || true' TERM INT
wait "$pid"
