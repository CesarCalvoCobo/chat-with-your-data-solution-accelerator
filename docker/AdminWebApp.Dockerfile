# Use a base image with Ubuntu 20.04
FROM ubuntu:20.04

# Prevents prompts during package installation
ARG DEBIAN_FRONTEND=noninteractive

# Update the package list and install necessary dependencies
# The `--fix-missing` option is added to bypass any missing or inaccessible packages
RUN apt-get update --fix-missing && \
    apt-get install -y --fix-missing python3.9 python3-pip python3-tk tk-dev gcc-9 g++-9

# Alternatively, you could change the repositories to a mirror that's accessible from your network
# RUN sed -i 's/http:\/\/archive.ubuntu.com\/ubuntu\//http:\/\/<your-mirror-here>.ubuntu.com\/ubuntu\//g' /etc/apt/sources.list && \
#     apt-get update && \
#     apt-get install -y python3.9 python3-pip python3-tk tk-dev gcc-9 g++-9

# Link the newer version of gcc and g++
RUN ln -fs /usr/bin/gcc-9 /usr/bin/gcc && \
    ln -fs /usr/bin/g++-9 /usr/bin/g++

# Copy your backend files
COPY ./backend/requirements.txt /usr/local/src/myscripts/requirements.txt
COPY ./backend/ /usr/local/src/myscripts

# Set the working directory
WORKDIR /usr/local/src/myscripts

# Install the Python dependencies
RUN pip3 install -r requirements.txt

# Expose port 80
EXPOSE 80

# Set the command to run your application
CMD ["streamlit", "run", "Admin.py", "--server.port", "80", "--server.enableXsrfProtection", "false"]



