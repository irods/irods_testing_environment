FROM almalinux:8

RUN \
  yum update -y && \
  yum install -y \
    authd \
    epel-release \
    gcc-c++ \
    gnupg \
    make \
    python3 \
    python3-pip \
    rsyslog \
    sudo \
    unixODBC-devel \
    wget \
    which \
  && \
  yum clean all && \
  rm -rf /var/cache/yum /tmp/*

# python 2 and 3 must be installed separately because yum will ignore/discard python2
RUN \
  yum check-update -q >/dev/null || { [ "$?" -eq 100 ] && yum update -y; } && \
  yum install -y \
    python3 \
    python3-devel \
    python3-pip \
  && \
  yum clean all && \
  rm -rf /var/cache/yum /tmp/*

RUN python3 -m pip install xmlrunner distro psutil pyodbc jsonschema requests

#RUN \
  #yum check-update -q >/dev/null || { [ "$?" -eq 100 ] && yum update -y; } && \
  #yum install -y \
    #python \
    #python-devel \
    #python-distro \
    #python-pip \
    #python-requests \
    #python-jsonschema \
    #python-psutil \
  #&& \
  #yum clean all && \
  #rm -rf /var/cache/yum /tmp/*

RUN rpm --import https://packages.irods.org/irods-signing-key.asc && \
    wget -qO - https://packages.irods.org/renci-irods.yum.repo | tee /etc/yum.repos.d/renci-irods.yum.repo

RUN rpm --import https://core-dev.irods.org/irods-core-dev-signing-key.asc && \
    wget -qO - https://core-dev.irods.org/renci-irods-core-dev.yum.repo | tee /etc/yum.repos.d/renci-irods-core-dev.yum.repo

COPY rsyslog.conf /etc/rsyslog.conf

ENTRYPOINT ["bash", "-c", "until false; do sleep 2147483647d; done"]
