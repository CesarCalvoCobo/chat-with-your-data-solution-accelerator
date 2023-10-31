# To enable ssh & remote debugging on app service change the base image to the one below
# FROM mcr.microsoft.com/azure-functions/python:4-python3.9-appservice
FROM mcr.microsoft.com/azure-functions/python:4-python3.9-appservice

# Set environment variables
ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true

# Install necessary tools for adding a PPA
RUN apt-get update && apt-get install -y software-properties-common


# Update system and install libstdc++6
RUN apt-get update && apt-get install -y libstdc++6

# Copy requirements file and install dependencies
COPY ./backend/requirements.txt /
RUN pip install -r /requirements.txt

# Copy backend source code
COPY ./backend /home/site/wwwroot