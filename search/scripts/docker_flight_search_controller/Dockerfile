FROM python:3.12

# Install system dependencies and Google Chrome in one step to reduce layers
RUN apt-get update -qq && apt-get install -y \
    wget \
    curl \
    gnupg \
    --no-install-recommends && \
    curl -sSL https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update -qq && \
    apt-get install -y google-chrome-stable && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the necessary files
COPY requirements.txt .
# Add the main Python script
COPY flight_search_docker_image.py .

# If undetected_chromedriver is a file, handle permissions correctly
COPY undetected_chromedriver /app/undetected_chromedriver
RUN chmod +x /app/undetected_chromedriver

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt



# Set environment variables
# Expose the port
EXPOSE 8080

# Run the Python application
CMD ["python3", "./flight_search_docker_image.py"]
