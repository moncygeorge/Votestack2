# Use Python 3.11 as the base image
FROM python:3.11-slim

# Install necessary system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libfreetype6-dev \
    libjpeg8-dev \
    zlib1g-dev \
    liblcms2-dev \
    libopenjpeg-dev

# Set the working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of your application files
COPY . /app/

# Set the command to run your app
CMD ["python", "app.py"]
