FROM centos:7

RUN sed -i \
        -e 's/mirror.centos.org/vault.centos.org/g' \
        -e 's/^#.*baseurl=http/baseurl=http/g' \
        -e 's/^mirrorlist=http/#mirrorlist=http/g' \
        /etc/yum.repos.d/*.repo && \
    yum check-update -q >/dev/null || { [ "$?" -eq 100 ] && yum update -y; } && \
    yum install -y \
        ca-certificates \
        epel-release \
        centos-release-scl \
        gnupg \
        wget \
    && \
    sed -i \
        -e 's/mirror.centos.org/vault.centos.org/g' \
        -e 's/^#.*baseurl=http/baseurl=http/g' \
        -e 's/^mirrorlist=http/#mirrorlist=http/g' \
        /etc/yum.repos.d/*.repo && \
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
        gcc-c++ \
        make \
        rsyslog \
        sudo \
        unixODBC-devel \
        which \
    && \
    yum clean all && \
    rm -rf /var/cache/yum /tmp/*

RUN yum update -y && \
    yum install -y \
        python3 \
        python3-devel \
        python3-pip \
        python36-distro \
        python36-jsonschema \
        python36-psutil \
        python36-requests \
    && \
    yum clean all && \
    rm -rf /var/cache/yum /tmp/*

RUN python3 -m pip install \
    pyodbc \
    'unittest-xml-reporting<3.1.0'

COPY rsyslog.conf /etc/rsyslog.conf

RUN mkdir -p /irods_testing_environment_mount_dir && chmod 777 /irods_testing_environment_mount_dir

ENTRYPOINT ["bash", "-c", "until false; do sleep 2147483647d; done"]
