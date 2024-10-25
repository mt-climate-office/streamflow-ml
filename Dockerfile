FROM python:3.12-slim

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the application into the container.
COPY . /app

# Install the application dependencies.
WORKDIR /app
RUN uv sync --frozen --no-cache

# Run the application.
# CMD ["tail", "-f", "/dev/null"]
CMD ["/app/.venv/bin/fastapi", "run", "src/streamflow_ml/api/main.py", "--port", "8000", "--host", "0.0.0.0"]