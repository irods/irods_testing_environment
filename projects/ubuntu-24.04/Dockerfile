FROM ubuntu:24.04

SHELL [ "/bin/bash", "-c" ]
ENV DEBIAN_FRONTEND=noninteractive

# Make sure we're starting with an up-to-date image
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get autoremove -y --purge && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/*

RUN apt-get update && \
    apt-get install -y \
        apt-transport-https \
        gnupg \
        wget \
        lsb-release \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/*

RUN wget -qO - https://packages.irods.org/irods-signing-key.asc | apt-key add - && \
    echo "deb [arch=amd64] https://packages.irods.org/apt/ noble main" | tee /etc/apt/sources.list.d/renci-irods.list

RUN apt-get update && \
    apt-get install -y \
        libcurl4-gnutls-dev \
        procps \
        python3 \
        python3-distro \
        python3-jsonschema \
        python3-lxml \
        python3-pip \
        python3-psutil \
        python3-requests \
        python3-setuptools \
        rsyslog \
        systemd \
        unixodbc \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/*

# Installing packages via pip in Ubuntu 24.04 is more strict than before. Given
# this is for testing purposes, we remove the file which blocks pip from touching
# system packages. See https://peps.python.org/pep-0668/ for details.
RUN rm /usr/lib/python3.*/EXTERNALLY-MANAGED && \
    python3 -m pip --no-cache-dir install 'unittest-xml-reporting'

RUN mkdir -p /irods_testing_environment_mount_dir && chmod 777 /irods_testing_environment_mount_dir

ENTRYPOINT ["bash", "-c", "until false; do sleep 2147483647d; done"]
