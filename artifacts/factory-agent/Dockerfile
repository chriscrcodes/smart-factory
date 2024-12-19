# Use the official Python 3.12.3 slim image as the base image.
FROM python:3.12.3-slim

# Set the working directory inside the container to /app.
WORKDIR /app

# Copy the current directory's contents (where the Dockerfile is located) to /app inside the container.
COPY . /app

# Install Python dependencies specified in the requirements.txt file.
RUN pip3 install -r requirements.txt

# Expose port 8501, which is the port the Streamlit app will run on.
EXPOSE 8501

# Define a health check to verify if the Streamlit server is running by sending a request to the health endpoint.
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Set the entry point for the container to run Streamlit. It starts the Streamlit app by running 'frontend.py',
# and binds it to port 8501, accessible on all network interfaces (0.0.0.0).
ENTRYPOINT ["streamlit", "run", "frontend.py", "--server.port=8501", "--server.address=0.0.0.0"]