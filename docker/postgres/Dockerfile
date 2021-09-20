ARG ARM64={$ARCH_IMAGE:+1}
ARG ARCH_IMAGE=${ARCH_IMAGE:-arm32v7/postgres}
FROM $ARCH_IMAGE

RUN printf "deb http://ftp.de.debian.org/debian stable main" > /etc/apt/sources.list


RUN apt-get update
RUN apt-get install -y wait-for-it binutils gdal-bin libproj-dev
# true if arm64 is set
RUN if [ -n "$ARM64"] ; then \
    apt-get install -y postgis* ; \
    else \
    apt-get install -y postgis postgresql-13-postgis-3 postgresql-13-postgis-3-scripts ; \
    fi
RUN rm -rf /var/lib/apt/lists/*

RUN mkdir -p /docker-entrypoint-initdb.d

RUN localedef -i en_US -f UTF-8 en_US.UTF-8