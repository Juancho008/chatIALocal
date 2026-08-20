#!/usr/bin/env python3
"""Mide latencia y tokens/s de Phi-4 Mini contra la API de Ollama."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
MODEL = os.environ.get("MODEL", "phi4-mini")
NUM_CTX = int(os.environ.get("NUM_CTX", "2048"))
NUM_THREAD = int(os.environ.get("NUM_THREAD", "10"))
PROMPT = os.environ.get(
    "PROMPT",
    "Escribe un resumen concreto de 8 oraciones sobre cómo funciona Docker.",
)
NUM_PREDICT = int(os.environ.get("NUM_PREDICT", "128"))
ROUNDS = int(os.environ.get("ROUNDS", "3"))


def wait_ready(timeout: int = 180) -> None:
    deadline = time.time() + timeout
    last_error = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{HOST}/api/tags", timeout=5) as resp:
                data = json.loads(resp.read().decode())
            names = [m.get("name", "") for m in data.get("models", [])]
            if any(MODEL in name for name in names):
                return
            last_error = f"modelo {MODEL} aún no aparece en {names}"
        except Exception as exc:  # noqa: BLE001
            last_error = str(exc)
        time.sleep(2)
    raise SystemExit(f"Ollama no quedó listo: {last_error}")


def ns_to_s(value: int | None) -> float:
    return (value or 0) / 1_000_000_000


def post_generate(think: bool) -> dict:
    payload = {
        "model": MODEL,
        "prompt": PROMPT,
        "stream": False,
        "think": think,
        "options": {
            "num_predict": NUM_PREDICT,
            "num_ctx": NUM_CTX,
            "num_thread": NUM_THREAD,
            "temperature": 0.2,
        },
    }
    req = urllib.request.Request(
        f"{HOST}/api/generate",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    with urllib.request.urlopen(req, timeout=300) as resp:
        body = json.loads(resp.read().decode())
    body["_wall_s"] = time.perf_counter() - started
    return body


def post_stream_ttft(think: bool) -> float:
    payload = {
        "model": MODEL,
        "prompt": PROMPT,
        "stream": True,
        "think": think,
        "options": {
            "num_predict": NUM_PREDICT,
            "num_ctx": NUM_CTX,
            "num_thread": NUM_THREAD,
            "temperature": 0.2,
        },
    }
    req = urllib.request.Request(
        f"{HOST}/api/generate",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    with urllib.request.urlopen(req, timeout=300) as resp:
        for raw in resp:
            chunk = json.loads(raw.decode())
            if chunk.get("response"):
                return time.perf_counter() - started
            if chunk.get("done"):
                break
    return time.perf_counter() - started


def summarize(label: str, runs: list[dict], ttft: float) -> None:
    last = runs[-1]
    eval_count = last.get("eval_count") or 0
    prompt_count = last.get("prompt_eval_count") or 0
    eval_s = ns_to_s(last.get("eval_duration"))
    prompt_s = ns_to_s(last.get("prompt_eval_duration"))
    load_s = ns_to_s(last.get("load_duration"))
    gen_tps = (eval_count / eval_s) if eval_s else 0.0
    prompt_tps = (prompt_count / prompt_s) if prompt_s else 0.0
    walls = [r["_wall_s"] for r in runs]
    avg_wall = sum(walls) / len(walls)

    preview = (last.get("response") or "").strip().replace("\n", " ")
    if len(preview) > 180:
        preview = preview[:177] + "..."

    print(f"\n=== {label} ===")
    print(f"Modelo              : {MODEL}")
    print(f"Prompt tokens       : {prompt_count}")
    print(f"Tokens generados    : {eval_count}")
    print(f"Carga del modelo    : {load_s:.2f} s")
    print(f"Prefill (prompt)    : {prompt_s:.2f} s  ({prompt_tps:.1f} tok/s)")
    print(f"Generación          : {eval_s:.2f} s  ({gen_tps:.1f} tok/s)")
    print(f"Time to first token : {ttft:.2f} s")
    print(f"Wall clock promedio : {avg_wall:.2f} s  ({ROUNDS} rondas)")
    print(f"Vista previa        : {preview}")


def main() -> int:
    print(f"Benchmark contra {HOST}  modelo={MODEL}")
    wait_ready()

    print("\nCalentamiento (descarta carga inicial del modelo)...")
    post_generate(think=False)

    for think, label in ((False, "Sin thinking (más rápido)"), (True, "Con thinking")):
        print(f"\nEjecutando {label.lower()}...")
        runs = [post_generate(think=think) for _ in range(ROUNDS)]
        ttft = post_stream_ttft(think=think)
        summarize(label, runs, ttft)

    print("\nListo. tok/s de generación es la métrica principal de velocidad.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.URLError as exc:
        print(f"No se pudo conectar a Ollama: {exc}", file=sys.stderr)
        raise SystemExit(1)
