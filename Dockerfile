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

# Install system dependencies and uv
RUN apt-get update && \
    apt-get install -y curl && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency manifests
COPY pyproject.toml ./
COPY uv.lock ./

# Install Python dependencies in venv using the full path to uv
RUN /root/.local/bin/uv venv && \
    /root/.local/bin/uv sync --locked --no-install-project --no-editable

# Copy web_report directory (which includes conversations_data.json)
COPY web_report/ ./web_report/

# Set proper environment path
ENV PATH="/app/.venv/bin:$PATH"

# Expose port 8080 for Netlify
EXPOSE 8080

# Run streamlit app on port 8080
CMD ["streamlit", "run", "web_report/app.py", "--server.port=8080", "--server.address=0.0.0.0"]
