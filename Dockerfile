FROM debian:13.3-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-docs.txt /tmp/requirements-docs.txt
RUN pip3 install --break-system-packages -r /tmp/requirements-docs.txt && rm /tmp/requirements-docs.txt

# Copy plugin source (incl. vendored web component assets) and install
COPY . /tmp/mkdocs-asyncapi/
RUN pip3 install --break-system-packages /tmp/mkdocs-asyncapi/ && rm -rf /tmp/mkdocs-asyncapi

WORKDIR /docs
EXPOSE 8000
CMD ["mkdocs", "serve", "-a", "0.0.0.0:8000", "--livereload"]
