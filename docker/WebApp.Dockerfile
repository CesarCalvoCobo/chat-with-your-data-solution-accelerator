# Step 1: Build the React application
FROM node:20-buster AS frontend
RUN mkdir -p /home/node/app/node_modules && chown -R node:node /home/node/app
WORKDIR /home/node/app
COPY ./frontend/package*.json ./
USER node
RUN npm ci
COPY --chown=node:node ./frontend/ ./frontend
COPY --chown=node:node ./static/ ./static
WORKDIR /home/node/app/frontend
RUN npm run build

# Step 2: Setup Python environment and copy built static files using Ubuntu 20.04
FROM ubuntu:20.04 AS backend
ARG DEBIAN_FRONTEND=noninteractive
RUN sed -i 's|http://archive.ubuntu.com/ubuntu/|http://mirror.ox.ac.uk/sites/archive.ubuntu.com/ubuntu/|g' /etc/apt/sources.list && \
    apt-get update --fix-missing && \
    apt-get install -y --fix-missing python3.9 python3-pip python3-tk tk-dev gcc-9 g++-9 build-essential \
    libffi-dev libssl-dev curl libpq5 && \
    ln -fs /usr/bin/gcc-9 /usr/bin/gcc && \
    ln -fs /usr/bin/g++-9 /usr/bin/g++ && \
    rm -rf /var/lib/apt/lists/*
COPY requirements.txt /usr/src/app/
WORKDIR /usr/src/app
RUN pip3 install --no-cache-dir -r requirements.txt
# Install uwsgi
RUN pip3 install --no-cache-dir uwsgi
COPY . /usr/src/app/
COPY --from=frontend /home/node/app/static /usr/src/app/static/
EXPOSE 80
CMD ["uwsgi", "--http", ":80", "--wsgi-file", "app.py", "--callable", "app", "-b","32768"]


