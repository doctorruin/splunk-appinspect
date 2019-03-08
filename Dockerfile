FROM alpine:3.9
LABEL "splunk-appinspect-version"="1.6.1"
RUN apk add --update --no-cache python py-pip g++ gcc libxml2-dev libxslt-dev libmagic py-lxml python-dev &&\
        adduser -S splunk-appinspect-user &&\
        wget -c http://dev.splunk.com/goto/appinspectdownload -O splunk-appinspect-1.6.1.tar.gz &&\
        pip install --no-cache-dir splunk-appinspect-1.6.1.tar.gz &&\
        rm -rf splunk-appinspect-1.6.1.tar.gz
USER splunk-appinspect-user
WORKDIR /home/splunk-appinspect-user
HEALTHCHECK --interval=1m --timeout=3s \
  CMD splunk-appinspect --help || exit 1