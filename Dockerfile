# Use a lightweight Python base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy application files
COPY requirements.txt /app/
COPY src/ /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the application's port
EXPOSE 8080

# Run the application
CMD ["python", "app.py"]
