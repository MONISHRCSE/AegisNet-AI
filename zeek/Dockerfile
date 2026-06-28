FROM zeek/zeek:6.0

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages redis hiredis

COPY scripts/ /scripts/
COPY site/ /usr/local/zeek/share/zeek/site/

CMD ["/scripts/entrypoint.sh"]
