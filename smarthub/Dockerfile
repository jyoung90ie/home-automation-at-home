FROM python:3

ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1
ENV PYTHONUNBUFFERED=1
WORKDIR /code

RUN printf "deb http://ftp.de.debian.org/debian stable main" > /etc/apt/sources.list

RUN apt-get update
RUN apt-get install -y wait-for-it binutils gdal-bin libproj-dev graphviz graphviz-dev
RUN rm -rf /var/lib/apt/lists/*

COPY requirements.txt /code
RUN pip install -r requirements.txt

COPY . /code
