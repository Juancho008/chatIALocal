#!/usr/bin/env python3
"""Chat en vivo contra Phi-4 Mini (CPU, contexto corto)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
MODEL = os.environ.get("MODEL", "phi4-mini")
PORT = int(os.environ.get("PORT", "3001"))
NUM_CTX = int(os.environ.get("NUM_CTX", "2048"))
SYSTEM = (
    "Eres un asistente en español. Contesta el último mensaje del usuario "
    "de forma concreta. Si es un acertijo o una pregunta, da la respuesta. "
    "No saludes otra vez. No repitas frases. No ofrezcas un menú genérico."
)


def compact_messages(raw: list) -> list[dict]:
    hist = [m for m in raw if m.get("role") in ("user", "assistant")]
    return [{"role": "system", "content": SYSTEM}, *hist[-8:]]

HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta http-equiv="Cache-Control" content="no-store" />
  <title>Phi-4 Mini · chat</title>
  <style>
    :root {
      --bg: #0e1116;
      --panel: #161b22;
      --line: #2b3340;
      --think: #d4a017;
      --think-bg: #1a160c;
      --text: #e8edf4;
      --muted: #8b97a8;
      --accent: #7dd3c0;
      --user: #243044;
    }
    * { box-sizing: border-box; }
    html, body { margin: 0; height: 100%; background: var(--bg); color: var(--text);
      font: 15px/1.5 "Segoe UI", system-ui, sans-serif; }
    body { display: grid; grid-template-rows: auto 1fr auto; }
    header {
      display: flex; align-items: center; justify-content: space-between; gap: 1rem;
      padding: 0.9rem 1.2rem; border-bottom: 1px solid var(--line); background: #0b0e13;
    }
    h1 { margin: 0; font-size: 1rem; font-weight: 650; letter-spacing: 0.02em; }
    h1 span { color: var(--accent); }
    .meta { color: var(--muted); font-size: 0.8rem; }
    .right { display: flex; align-items: center; gap: 0.85rem; }
    #mode {
      font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;
      padding: 0.28rem 0.55rem; border-radius: 999px; border: 1px solid var(--line);
    }
    #mode.off { color: var(--accent); background: #10241f; }
    #mode.on { color: var(--think); background: var(--think-bg); }
    label.toggle { display: flex; align-items: center; gap: 0.45rem; color: var(--muted); font-size: 0.85rem; cursor: pointer; }
    select {
      background: var(--panel); color: var(--text); border: 1px solid var(--line);
      border-radius: 10px; padding: 0.35rem 0.5rem; font: inherit;
    }
    #log { overflow: auto; padding: 1.1rem 1.2rem 1.4rem; display: flex; flex-direction: column; gap: 1rem; }
    .msg { max-width: 52rem; width: 100%; margin: 0 auto; }
    .msg.user .bubble {
      background: var(--user); border: 1px solid var(--line); border-radius: 14px 14px 4px 14px;
      padding: 0.75rem 0.95rem; white-space: pre-wrap;
    }
    .msg.assistant .think, .msg.assistant .answer {
      border-radius: 12px; padding: 0.75rem 0.95rem; white-space: pre-wrap; margin-top: 0.45rem;
    }
    .msg.assistant .think {
      background: var(--think-bg); border: 1px solid #3a3014; color: #f0d48a;
      font-family: ui-monospace, Consolas, monospace; font-size: 0.82rem; line-height: 1.55;
    }
    .msg.assistant .answer { background: var(--panel); border: 1px solid var(--line); }
    .label { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.12em; color: var(--muted); margin-bottom: 0.25rem; }
    .think .label { color: var(--think); }
    .answer .label { color: var(--accent); }
    .think.hidden { display: none; }
    .cursor::after { content: "▍"; animation: blink 1s step-end infinite; color: var(--accent); }
    @keyframes blink { 50% { opacity: 0; } }
    footer { border-top: 1px solid var(--line); padding: 0.85rem 1.2rem 1.1rem; background: #0b0e13; }
    form { max-width: 52rem; margin: 0 auto; display: grid; grid-template-columns: 1fr auto; gap: 0.6rem; }
    textarea {
      resize: none; min-height: 52px; max-height: 180px; padding: 0.7rem 0.85rem;
      border-radius: 12px; border: 1px solid var(--line); background: var(--panel); color: var(--text);
      font: inherit;
    }
    textarea:focus { outline: 2px solid #2a6f64; border-color: var(--accent); }
    button {
      border: 0; border-radius: 12px; padding: 0 1.15rem; background: var(--accent); color: #06251f;
      font-weight: 700; cursor: pointer;
    }
    button:disabled { opacity: 0.5; cursor: wait; }
    .empty { margin: auto; text-align: center; color: var(--muted); max-width: 28rem; }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>Phi-4 Mini · <span>chat</span></h1>
      <div class="meta">3.8B · CPU · 1 modelo · contexto 2048 tokens</div>
    </div>
    <div class="right">
      <div id="mode" class="off">sin thinking</div>
      <label class="toggle">
        <input id="think" type="checkbox" />
        Mostrar thinking
      </label>
    </div>
  </header>
  <main id="log">
    <div class="empty" id="empty">Phi-4 Mini en CPU. Buen equilibrio calidad/velocidad. No busca internet ni tus archivos salvo que armes un RAG.</div>
  </main>
  <footer>
    <form id="form">
      <textarea id="input" rows="2" placeholder="Escribí tu mensaje…  Enter envía, Shift+Enter nueva línea" autofocus></textarea>
      <button id="send" type="submit">Enviar</button>
    </form>
  </footer>
  <script>
    const log = document.getElementById("log");
    const empty = document.getElementById("empty");
    const form = document.getElementById("form");
    const input = document.getElementById("input");
    const send = document.getElementById("send");
    const thinkBox = document.getElementById("think");
    const mode = document.getElementById("mode");
    const messages = [];

    function syncMode() {
      if (thinkBox.checked) {
        mode.textContent = "con thinking";
        mode.className = "on";
      } else {
        mode.textContent = "sin thinking";
        mode.className = "off";
      }
    }
    thinkBox.checked = false;
    thinkBox.addEventListener("change", syncMode);
    syncMode();

    function visibleAnswer(raw) {
      return raw
        .replace(/<think>[\s\S]*?<\/think>/gi, "")
        .replace(/<think>[\s\S]*$/gi, "")
        .trimStart();
    }

    input.addEventListener("input", () => {
      input.style.height = "auto";
      input.style.height = Math.min(input.scrollHeight, 180) + "px";
    });
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); form.requestSubmit(); }
    });

    function el(tag, cls, text) {
      const node = document.createElement(tag);
      if (cls) node.className = cls;
      if (text) node.textContent = text;
      return node;
    }

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const text = input.value.trim();
      if (!text || send.disabled) return;
      empty.remove();
      const showThink = thinkBox.checked;
      messages.push({ role: "user", content: text });
      const user = el("article", "msg user");
      user.appendChild(el("div", "bubble", text));
      log.appendChild(user);

      const card = el("article", "msg assistant");
      const thinkWrap = el("div", showThink ? "think" : "think hidden");
      thinkWrap.appendChild(el("div", "label", "Pensando"));
      const thinkBody = el("div", "body cursor");
      thinkWrap.appendChild(thinkBody);
      const answerWrap = el("div", "answer");
      answerWrap.appendChild(el("div", "label", "Respuesta"));
      const answerBody = el("div", "body cursor");
      answerWrap.appendChild(answerBody);
      card.append(thinkWrap, answerWrap);
      log.appendChild(card);
      log.scrollTop = log.scrollHeight;

      input.value = "";
      input.style.height = "auto";
      send.disabled = true;
      send.textContent = "…";

      let thinking = "";
      let content = "";
      try {
        const res = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ messages, enable_thinking: showThink })
        });
        if (!res.ok) throw new Error(await res.text());
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buf = "";
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          buf += decoder.decode(value, { stream: true });
          const lines = buf.split("\n");
          buf = lines.pop();
          for (const line of lines) {
            if (!line.trim()) continue;
            const data = JSON.parse(line);
            const msg = data.message || {};
            if (showThink && msg.thinking) {
              thinking += msg.thinking;
              thinkBody.textContent = thinking;
            }
            if (msg.content) {
              content += msg.content;
              answerBody.textContent = showThink ? content : visibleAnswer(content);
            }
            log.scrollTop = log.scrollHeight;
          }
        }
      } catch (err) {
        answerBody.textContent = "Error: " + err.message;
      }
      thinkBody.classList.remove("cursor");
      answerBody.classList.remove("cursor");
      if (!showThink || !thinking) thinkWrap.classList.add("hidden");
      const stored = showThink ? content : visibleAnswer(content);
      messages.push({ role: "assistant", content: stored || "(sin respuesta)" });
      send.disabled = false;
      send.textContent = "Enviar";
      input.focus();
    });
  </script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        print(f"[live-chat] {self.address_string()} {fmt % args}")

    def _no_cache(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")

    def do_GET(self) -> None:
        if self.path.split("?", 1)[0] not in ("/", "/index.html"):
            self.send_error(404)
            return
        data = HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self._no_cache()
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:
        if self.path != "/api/chat":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError:
            self.send_error(400, "JSON inválido")
            return

        enable_thinking = body.get("enable_thinking") is True
        messages = compact_messages(list(body.get("messages") or []))
        payload = {
            "model": MODEL,
            "messages": messages,
            "stream": True,
            "think": enable_thinking,
            "options": {
                "num_ctx": NUM_CTX,
                "num_thread": int(os.environ.get("NUM_THREAD", "10")),
                "temperature": 0.7,
                "repeat_penalty": 1.1,
                "top_p": 0.9,
            },
        }
        req = urllib.request.Request(
            f"{HOST}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                self.send_response(200)
                self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                while True:
                    chunk = resp.read(256)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    self.wfile.flush()
        except urllib.error.URLError as exc:
            msg = f"No se pudo hablar con Ollama: {exc}".encode("utf-8")
            self.send_response(502)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Chat en vivo: http://localhost:{PORT}  modelo={MODEL}  ollama={HOST}")
    server.serve_forever()


if __name__ == "__main__":
    main()
