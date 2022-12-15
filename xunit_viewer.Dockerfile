FROM node:19

RUN npm i -g xunit-viewer

ENTRYPOINT ["xunit-viewer", "-s"]
