FROM ollama/ollama:latest

ENV OLLAMA_HOST=0.0.0.0
ENV OLLAMA_KEEP_ALIVE=24h
ENV OLLAMA_MAX_LOADED_MODELS=1
ENV OLLAMA_NUM_PARALLEL=1
ENV OLLAMA_CONTEXT_LENGTH=2048
ENV MODEL=phi4-mini
ENV NUM_CTX=2048

COPY scripts/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN sed -i 's/\r$//' /usr/local/bin/entrypoint.sh && chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 11434

HEALTHCHECK --interval=10s --timeout=10s --start-period=600s --retries=60 \
  CMD ollama show "$MODEL" || exit 1

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
