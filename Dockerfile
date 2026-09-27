# Android ADB Toolkit — local web UI + API
# Requires host ADB (platform-tools). Device access typically needs USB
# passthrough or network ADB from the host; this image is mainly for the
# server/UI when ADB is provided via ADB_SERVER_SOCKET or a mounted binary.

FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends android-tools-adb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY adb_toolkit/ adb_toolkit/
COPY static/ static/
COPY server.py pyproject.toml requirements.txt README.md API.md ./

ENV ADB_TOOLKIT_HOST=0.0.0.0
ENV ADB_TOOLKIT_PORT=8000
EXPOSE 8000

# Default bind inside containers is 0.0.0.0; on the host prefer 127.0.0.1.
CMD ["python3", "server.py", "--host", "0.0.0.0", "--port", "8000"]
