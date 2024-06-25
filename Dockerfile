# Use an official Python runtime as a parent image
 FROM python:3.11.4

 # Set the working directory to /app
 WORKDIR /app

 # Update the package list and install necessary packages
 RUN apt-get update && apt-get install -y portaudio19-dev

 # Copy the current directory contents into the container at /app
 ADD . /app

 # Print current working directory and list files for debugging
 RUN echo "Current working directory:" && pwd
 RUN echo "List files in /app directory:" && ls -la /app

 # Define a build argument to pass the GOOGLE_CREDS_JSON value
 ARG GOOGLE_CREDS_JSON
 ARG GOOGLE_CREDS_PATH
 # Set the environment variable from the build argument
 ENV GOOGLE_CREDS_JSON=${GOOGLE_CREDS_JSON}
 ENV GOOGLE_CREDS_PATH=${GOOGLE_CREDS_PATH}
 
 # Install any needed packages specified in requirements.txt
 RUN python create_google_creds.py

 # Print current working directory and list files for debugging
 RUN echo "Current working directory:" && pwd
 RUN echo "List files in /app directory:" && ls -la /app


 RUN pip install -r requirements.txt

 # Expose port 8000 to the world outside this container
 EXPOSE 8000

 # Run the FastAPI app with uvicorn
 CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]