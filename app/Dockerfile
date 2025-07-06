# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install dependencies for Selenium and a browser
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    --no-install-recommends
ENV PATH="/usr/bin:${PATH}"

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt ./

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code
COPY . .

# Make port 5000 available
EXPOSE 5000

# Run app.py using a production-ready server
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "--threads", "2", "--timeout", "120", "app:app"]