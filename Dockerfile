# Use the official Python image as a base
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Set the environment variables for the GitHub Action
ENV GITHUB_TOKEN=$GITHUB_TOKEN
ENV ADD_DESCRIPTION=$ADD_DESCRIPTION
ENV REPO_NAME=$REPO_NAME
ENV GITHUB_USERNAME=$GITHUB_USERNAME
ENV INCREMENT_TYPE=$INCREMENT_TYPE

# Run the script when the container starts
ENTRYPOINT ["python", "create_release.py"]
