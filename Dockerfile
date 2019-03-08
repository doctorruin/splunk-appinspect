FROM alpine:3.9
LABEL "splunk-appinspect-version"="1.6.1"
RUN apk add --update --no-cache --virtual .build-deps \
        g++ gcc libxml2-dev libxslt-dev python-dev &&\
        apk add --no-cache python py-pip py-lxml libmagic &&\
        adduser -S splunk &&\
        pip install --no-cache-dir http://dev.splunk.com/goto/appinspectdownload &&\
        apk del .build-deps &&\
        chown -R splunk: /home/splunk
USER splunk
WORKDIR /home/splunk
HEALTHCHECK --interval=1m --timeout=3s \
  CMD splunk-appinspect --help || exit 1