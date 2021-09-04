FROM python:3

ENV PYTHONUNBUFFERED=1
WORKDIR /code

RUN printf "deb http://ftp.de.debian.org/debian stable main" > /etc/apt/sources.list

RUN apt-get update
RUN apt-get install -y wait-for-it binutils gdal-bin libproj-dev postgis postgresql-13-postgis-3 postgresql-13-postgis-3-scripts graphviz graphviz-dev
RUN rm -rf /var/lib/apt/lists/*

RUN mkdir -p /docker-entrypoint-initdb.d

COPY requirements.txt /code
RUN pip install -r requirements.txt

# COPY ./init-database.sh /docker-entrypoint-initdb.d/01_init-database.sh
COPY . /code
