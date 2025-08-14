FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y \
        apt-transport-https \
        ca-certificates \
        gnupg \
        wget \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/*

RUN mkdir -p /etc/apt/keyrings && \
    wget -qO - https://packages.irods.org/irods-signing-key.asc | \
        gpg \
            --no-options \
            --no-default-keyring \
            --no-auto-check-trustdb \
            --homedir /dev/null \
            --no-keyring \
            --import-options import-export \
            --output /etc/apt/keyrings/renci-irods-archive-keyring.pgp \
            --import \
        && \
    echo "deb [signed-by=/etc/apt/keyrings/renci-irods-archive-keyring.pgp arch=amd64] https://packages.irods.org/apt/ jammy main" | \
        tee /etc/apt/sources.list.d/renci-irods.list && \
    wget -qO - https://core-dev.irods.org/irods-core-dev-signing-key.asc | \
        gpg \
            --no-options \
            --no-default-keyring \
            --no-auto-check-trustdb \
            --homedir /dev/null \
            --no-keyring \
            --import-options import-export \
            --output /etc/apt/keyrings/renci-irods-core-dev-archive-keyring.pgp \
            --import \
        && \
    echo "deb [signed-by=/etc/apt/keyrings/renci-irods-core-dev-archive-keyring.pgp arch=amd64] https://core-dev.irods.org/apt/ jammy main" | \
        tee /etc/apt/sources.list.d/renci-irods-core-dev.list

RUN apt-get update && \
    apt-get install -y \
        libcurl4-gnutls-dev \
        python3 \
        python3-distro \
        python3-jsonschema \
        python3-pip \
        python3-psutil \
        python3-requests \
        rsyslog \
        unixodbc \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/*

RUN python3 -m pip install 'unittest-xml-reporting<3.1.0'

RUN mkdir -p /irods_testing_environment_mount_dir && chmod 777 /irods_testing_environment_mount_dir

ENTRYPOINT ["bash", "-c", "until false; do sleep 2147483647d; done"]
