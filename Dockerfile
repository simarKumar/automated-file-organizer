# Use an official Python runtime as a parent image
# python:3.11-slim is an industry-standard lightweight image that reduces attack surface and image size
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# --no-cache-dir keeps the docker image small by not storing the pip cache
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create the default source directory so the container doesn't fail if volume isn't bound
RUN mkdir -p /app/test_folder

# Define the command to run our daemon script
CMD ["python", "organizer.py", "--source", "/app/test_folder", "--dest", "/app/test_folder"]
