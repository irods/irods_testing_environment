FROM centos:7

RUN yum update -y && \
    yum install -y epel-release && \
    yum install -y sudo wget python-pip rsyslog netcat gnupg python python-psutil python-requests python-jsonschema && \
    pip install xmlrunner

COPY ../../entrypoint.sh /
ENTRYPOINT ["bash", "/entrypoint.sh"]
