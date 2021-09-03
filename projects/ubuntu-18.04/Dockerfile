FROM ubuntu:18.04

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
        wget \
        apt-transport-https \
        python-pip \
        libfuse2 \
        unixodbc \
        rsyslog \
        netcat \
        gnupg \
    && \
    pip install xmlrunner

RUN wget -qO - https://packages.irods.org/irods-signing-key.asc | apt-key add - && \
    echo "deb [arch=amd64] https://packages.irods.org/apt/ bionic main" | tee /etc/apt/sources.list.d/renci-irods.list && \
    apt-get update

ENTRYPOINT ["bash", "-c", "until false; do sleep 2147483647d; done"]
