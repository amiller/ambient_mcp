FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY oauth_mcp_proxy.py .
COPY ambient_mcp_server.py .
COPY start_services.py .

RUN mkdir -p mcp_data

EXPOSE 9100

CMD ["python", "start_services.py"]