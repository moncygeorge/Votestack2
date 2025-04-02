# Use a Python image as the base
FROM python:3.10-slim

# Install necessary system dependencies
RUN apt-get update -y && \
    apt-get upgrade -y && \
    apt-get install -y \
        build-essential \
        python3-dev \
        libfreetype6-dev \
        libjpeg62-turbo-dev \
        zlib1g-dev \
        liblcms2-dev \
        wget \
        cmake && \
    apt-get clean

# Download and build OpenJPEG from source
RUN wget https://github.com/uclouvain/openjpeg/archive/refs/tags/v2.4.0.tar.gz -O openjpeg.tar.gz && \
    tar -xzf openjpeg.tar.gz && \
    cd openjpeg-2.4.0 && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make && \
    make install && \
    cd ../.. && \
    rm -rf openjpeg-2.4.0 openjpeg.tar.gz


# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the application code into the container
COPY . /app/

# Expose the port the app will run on
EXPOSE 5000

# Command to run the application
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
