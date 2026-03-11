FROM astromanager-base:bookworm

COPY image/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

COPY code/ /app/
RUN chmod +x /app/master.sh 2>/dev/null || true && \
    find /app/lib -type f -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true && \
    find /app/bin -type f -exec chmod +x {} \; 2>/dev/null || true && \
    find /app/workflows -type f -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true

WORKDIR /app
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["bash"]
