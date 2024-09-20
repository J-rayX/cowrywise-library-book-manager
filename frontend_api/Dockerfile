
FROM python:3.10-slim
WORKDIR /app
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    gcc \
    python3-dev \
    libpq-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*  # Clean up to reduce image size
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt
COPY . /app/
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
