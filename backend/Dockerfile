FROM python:3.13-slim

WORKDIR /app

# Copy requirements
COPY pyproject.toml ./

# Install uv
RUN pip install uv

# Install dependencies without lockfile
RUN uv sync

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]