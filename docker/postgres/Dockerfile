FROM arm32v7/postgres

RUN printf "deb http://ftp.de.debian.org/debian stable main" > /etc/apt/sources.list

RUN apt-get update
RUN apt-get install -y wait-for-it binutils gdal-bin libproj-dev postgis*
RUN rm -rf /var/lib/apt/lists/*

RUN mkdir -p /docker-entrypoint-initdb.d

RUN localedef -i en_US -f UTF-8 en_US.UTF-8