FROM alpine:3.9
LABEL "splunk-appinspect-version"="1.6.1"

RUN mkdir -p /home/splunk/app
COPY inspect-api.py /home/splunk/app
COPY custom_checks_splunk_appinspect /home/splunk/custom_checks_splunk_appinspect

RUN apk add --update --no-cache --virtual .build-deps \
        g++ gcc libxml2-dev libxslt-dev python-dev py-pip &&\
        apk add --no-cache python py-lxml libmagic &&\
        addgroup -S splunk &&\
        adduser -S splunk -G splunk &&\
        chown -R splunk:splunk /home/splunk &&\
        pip install --no-cache-dir http://dev.splunk.com/goto/appinspectdownload &&\
        pip install --no-cache-dir flask waitress &&\
        apk del .build-deps

USER splunk
WORKDIR /home/splunk
CMD ["python", "/home/splunk/app/inspect-api.py", "&"]
HEALTHCHECK --interval=1m --timeout=3s \
  CMD splunk-appinspect --help || exit 1