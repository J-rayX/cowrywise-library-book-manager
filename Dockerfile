# Parent image
FROM python:3.10-slim

# Set the working dir in the container
WORKDIR /app

# Copy the requirements.txt file into the container at /app
COPY requirements.txt /app/

# Install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the current dir contents into the container at /app
COPY . /app/

# Run Django migrations and start the app
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
