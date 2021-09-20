ARG AMD64=${ARCH_IMAGE}
ARG ARCH_IMAGE=${ARCH_IMAGE:-arm32v7/postgres}
FROM $ARCH_IMAGE

RUN printf "deb http://ftp.de.debian.org/debian stable main" > /etc/apt/sources.list


RUN apt-get update
RUN apt-get install -y wait-for-it binutils gdal-bin libproj-dev
# true if amd64 is set
RUN echo "amd64=$AMD64"
RUN if [ -n "$AMD64"] ; then \
    apt-get install -y postgis postgresql-13-postgis-3 postgresql-13-postgis-3-scripts ; \
    else \
    apt-get install -y postgis* ; \
    fi
RUN rm -rf /var/lib/apt/lists/*

RUN mkdir -p /docker-entrypoint-initdb.d

RUN localedef -i en_US -f UTF-8 en_US.UTF-8