FROM ollama/ollama:latest

ENV OLLAMA_HOST=0.0.0.0
ENV OLLAMA_KEEP_ALIVE=24h
ENV MODEL=qwen3:0.6b

COPY scripts/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 11434

HEALTHCHECK --interval=10s --timeout=10s --start-period=30s --retries=30 \
  CMD ollama show qwen3:0.6b || exit 1

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
