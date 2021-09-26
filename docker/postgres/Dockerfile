ARG AMD64=${ARCH_IMAGE}
FROM ${ARCH_IMAGE:-arm32v7/postgres}

RUN printf "deb http://ftp.de.debian.org/debian stable main" >> /etc/apt/sources.list


RUN localedef -i en_US -f UTF-8 en_US.UTF-8
RUN apt-get update
RUN apt-get install -y wait-for-it binutils gdal-bin libproj-dev
# true if amd64 is set
RUN echo "amd64=$AMD64"
RUN if [ -n "$AMD64"] ; then \
    apt-get install -y postgresql-13 ; \
    apt-get install -y postgresql-13-postgis-3 ; \
    apt-get install -y postgresql-13-postgis-3-scripts; \
    apt-get install -y postgis ; \
    else \
    apt-get install -y postgis* ; \
    fi
RUN rm -rf /var/lib/apt/lists/*

RUN mkdir -p /docker-entrypoint-initdb.d
