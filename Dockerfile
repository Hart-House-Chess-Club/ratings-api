FROM python:3.12-alpine3.20

WORKDIR /app

# Install dependencies needed for building Python packages and handling ZIP files
RUN apk add --no-cache build-base libffi-dev zip unzip

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for rating lists if it doesn't exist
RUN mkdir -p rating-lists

# Make scripts executable
RUN chmod +x initialize_rating_lists.sh

# Add wget for health checks
RUN apk add --no-cache wget

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
