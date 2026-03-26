FROM astromanager-base:bookworm

COPY image/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

RUN apt-get update && apt-get install -y --no-install-recommends     libvips-tools  && rm -rf /var/lib/apt/lists/*

COPY code/ /app/
RUN mkdir -p /app/web/static/vendor/openseadragon/images && \
    curl -fsSL https://cdn.jsdelivr.net/npm/openseadragon@5.0.1/build/openseadragon/openseadragon.min.js -o /app/web/static/vendor/openseadragon/openseadragon.min.js && \
    chmod +x /app/master.sh 2>/dev/null || true && \
    find /app/lib -type f -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true && \
    find /app/bin -type f -exec chmod +x {} \; 2>/dev/null || true && \
    find /app/workflows -type f -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true

WORKDIR /app
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["bash"]
