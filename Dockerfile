# Use a lightweight Python base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt to install dependencies
COPY app/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY app/ /app

# Expose the application's port
EXPOSE 8080

# Run the application
CMD ["python", "app.py"]
