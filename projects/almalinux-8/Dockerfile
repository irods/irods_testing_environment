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
    unixODBC-devel \
    wget \
    which
  #&& \
  #yum clean all && \
  #rm -rf /var/cache/yum /tmp/* && \

RUN yum install -y python3-devel

RUN pip3 install xmlrunner distro psutil pyodbc jsonschema requests

# TODO: when externals packages are published for almalinux:8, this section can be uncommented
#RUN rpm --import https://packages.irods.org/irods-signing-key.asc && \
    #wget -qO - https://packages.irods.org/renci-irods.yum.repo | tee /etc/yum.repos.d/renci-irods.yum.repo

#RUN rpm --import https://core-dev.irods.org/irods-core-dev-signing-key.asc && \
    #wget -qO - https://core-dev.irods.org/renci-irods-core-dev.yum.repo | tee /etc/yum.repos.d/renci-irods-core-dev.yum.repo

ENTRYPOINT ["bash", "-c", "until false; do sleep 2147483647d; done"]
