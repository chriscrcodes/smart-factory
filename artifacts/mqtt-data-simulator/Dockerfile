# Use a base image with Python installed
FROM python:3.12.3-slim

# Set the working directory
WORKDIR /app

# Copy the Python simulator into the container
COPY simulator.py requirements.txt .

# Install required Python packages
RUN pip3 install -r requirements.txt

# Command to run the simulator
CMD ["python", "simulator.py"]