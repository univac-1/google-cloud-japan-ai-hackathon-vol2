# Python image to use.
FROM python:3.9-slim

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file.
COPY requirements.txt .

# Install dependencies.
RUN pip install -r requirements.txt

# Copy the rest of the code.
COPY . .

# Set the entrypoint to use gunicorn.
ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]
