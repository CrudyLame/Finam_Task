FROM python:3.12-slim-bookworm

# Set environment variables for consistent builds and non-interactive apt
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    TZ=UTC \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy uv binary from official image
COPY --from=ghcr.io/astral-sh/uv:0.7.8 /uv /bin/uv

# Copy dependency manifests
COPY pyproject.toml ./
COPY uv.lock ./

# Install Python dependencies in venv
RUN uv venv && \
    uv sync --locked --no-install-project --no-editable

# Copy web_report directory and conversations data
COPY web_report/ ./web_report/
COPY conversations_data.json ./conversations_data.json

# Set proper environment path
ENV PATH="/app/.venv/bin:$PATH"

# Expose streamlit port
EXPOSE 8501

# Run streamlit app
CMD ["streamlit", "run", "web_report/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
