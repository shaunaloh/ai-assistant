FROM python:3.10-slim

WORKDIR /app

# Copy backend & frontend into /app
COPY backend/ backend/
COPY frontend/ frontend/

# Install Python dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Expose Flask port
EXPOSE 8000

# Run the app
CMD ["python", "backend/app.py"]
