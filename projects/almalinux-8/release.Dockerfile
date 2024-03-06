FROM almalinux:8

RUN yum check-update -q >/dev/null || { [ "$?" -eq 100 ] && yum update -y; } && \
    yum install -y \
        ca-certificates \
        epel-release \
        gnupg \
        wget \
    && \
    yum clean all && \
    rm -rf /var/cache/yum /tmp/*

RUN rpm --import https://packages.irods.org/irods-signing-key.asc && \
    wget -qO - https://packages.irods.org/renci-irods.yum.repo | tee /etc/yum.repos.d/renci-irods.yum.repo

RUN rpm --import https://core-dev.irods.org/irods-core-dev-signing-key.asc && \
    wget -qO - https://core-dev.irods.org/renci-irods-core-dev.yum.repo | tee /etc/yum.repos.d/renci-irods-core-dev.yum.repo

# TODO: For some reason, this makes the build fail after adding the iRODS repo
#RUN yum check-update -q >/dev/null || { [ "$?" -eq 100 ] && yum update -y; } && \
RUN yum update -y && \
    yum install -y \
        authd \
        diffutils \
        gcc-c++ \
        make \
        rsyslog \
        sudo \
        unixODBC-devel \
        which \
    && \
    yum clean all && \
    rm -rf /var/cache/yum /tmp/*

# python 2 and 3 must be installed separately because yum will ignore/discard python2
# TODO: For some reason, this makes the build fail after adding the iRODS repo
#RUN yum check-update -q >/dev/null || { [ "$?" -eq 100 ] && yum update -y; } && \
RUN yum update -y && \
    yum install -y \
        python3 \
        python3-devel \
        python3-pip \
    && \
    yum clean all && \
    rm -rf /var/cache/yum /tmp/*

RUN python3 -m pip install \
    distro \
    jsonschema \
    psutil \
    pyodbc \
    requests \
    'unittest-xml-reporting<3.1.0'

COPY rsyslog.conf /etc/rsyslog.conf

RUN mkdir -p /irods_testing_environment_mount_dir && chmod 777 /irods_testing_environment_mount_dir

ENTRYPOINT ["bash", "-c", "until false; do sleep 2147483647d; done"]

ARG irods_package_version=4.3.0-1

# TODO: For some reason, this makes the build fail after adding the iRODS repo
#RUN yum check-update -q >/dev/null || { [ "$?" -eq 100 ] && yum update -y; } && \
RUN yum update -y && \
    yum install -y \
        irods-database-plugin-postgres-${irods_package_version} \
        irods-runtime-${irods_package_version} \
        irods-server-${irods_package_version} \
        irods-icommands-${irods_package_version} \
    && \
    yum clean all && \
    rm -rf /var/cache/yum /tmp/*
