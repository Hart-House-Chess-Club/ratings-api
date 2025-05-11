FROM python:3.12-alpine3.20

WORKDIR /app

# Install dependencies needed for building Python packages
RUN apk add --no-cache build-base libffi-dev

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for rating lists if it doesn't exist
RUN mkdir -p rating-lists

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
