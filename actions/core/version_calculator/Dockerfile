FROM python:3.9-slim

# Install git (required for git operations)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy implementation
COPY main.py .

# Set entrypoint
ENTRYPOINT ["python", "/app/main.py"]