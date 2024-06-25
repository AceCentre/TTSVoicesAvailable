# Use an official Python runtime as a parent image
 FROM python:3.11.4

 # Set the working directory to /app
 WORKDIR /app

 # Update the package list and install necessary packages
 RUN apt-get update && apt-get install -y portaudio19-dev

 # Copy the current directory contents into the container at /app
 ADD . /app

 # Define a build argument to pass the GOOGLE_CREDS_JSON value
 ARG GOOGLE_CREDS_JSON
 # Set the environment variable from the build argument
 ENV GOOGLE_CREDS_JSON=${GOOGLE_CREDS_JSON}

 # Install any needed packages specified in requirements.txt
 RUN python create_google_creds.py
 RUN pip install -r requirements.txt

 # Expose port 8000 to the world outside this container
 EXPOSE 8000

 # Run the FastAPI app with uvicorn
 CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]