FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port for the application
EXPOSE 8002

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV OLLAMA_API_URL=http://100.69.25.25:11434/api/generate
ENV OLLAMA_MODEL=llama3.1:latest
ENV DB_HOST=db
ENV DB_USER=root
ENV DB_PASSWORD=example
ENV DB_NAME=traffic_safety
ENV DB_PORT=3306

# Run the application
CMD ["python", "app.py"]