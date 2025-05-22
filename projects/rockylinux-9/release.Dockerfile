# syntax=docker/dockerfile:1.5

FROM rockylinux/rockylinux:9

SHELL [ "/usr/bin/bash", "-c" ]

# Make sure we're starting with an up-to-date image
RUN dnf update -y || [ "$?" -eq 100 ] && \
    rm -rf /tmp/*

RUN dnf install -y \
        ca-certificates \
        epel-release \
        gnupg \
        wget \
    && \
    rm -rf /tmp/*

RUN dnf install -y \
        diffutils \
        lsof \
        openssl \
        postgresql-server \
        python3 \
        python3-distro \
        python3-jsonschema \
        python3-pip \
        python3-psutil \
        python3-pyodbc \
        python3-requests \
        rsyslog \
        sudo \
        unixODBC \
        which \
    && \
    yum clean all && \
    rm -rf /var/cache/yum /tmp/*

# TODO: irods/irods#7349 - Remove this line once iRODS repository signing keys have been updated.
RUN update-crypto-policies --set LEGACY

RUN dnf install -y \
        dnf-plugin-config-manager \
    && \
    rpm --import https://packages.irods.org/irods-signing-key.asc && \
    dnf config-manager -y --add-repo https://packages.irods.org/renci-irods.yum.repo && \
    dnf config-manager -y --set-enabled renci-irods && \
    rpm --import https://core-dev.irods.org/irods-core-dev-signing-key.asc && \
    dnf config-manager -y --add-repo https://core-dev.irods.org/renci-irods-core-dev.yum.repo && \
    dnf config-manager -y --set-enabled renci-irods-core-dev && \
    rm -rf /tmp/*

RUN python3 -m pip install 'unittest-xml-reporting<3.1.0'

COPY rsyslog.conf /etc/rsyslog.conf

RUN mkdir -p /irods_testing_environment_mount_dir && chmod 777 /irods_testing_environment_mount_dir

ENTRYPOINT ["bash", "-c", "until false; do sleep 2147483647d; done"]

ARG irods_package_version=4.3.1-1

RUN dnf update -y && \
    dnf install -y \
        irods-database-plugin-postgres-${irods_package_version} \
        irods-runtime-${irods_package_version} \
        irods-server-${irods_package_version} \
        irods-icommands-${irods_package_version} \
    && \
    yum clean all && \
    rm -rf /var/cache/yum /tmp/*
