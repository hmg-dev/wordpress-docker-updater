FROM python:3.8-alpine

ENV TZ=Europe/Berlin

RUN apk update
RUN apk upgrade
RUN apk add git bash openssl curl ca-certificates && update-ca-certificates
RUN apk add --update tzdata
RUN cp /usr/share/zoneinfo/Europe/Berlin /etc/localtime && \
    echo "Europe/Berlin" > /etc/timezone
RUN apk add --update tzdata

RUN mkdir -p /data/DUS && \
    mkdir -p /data/app

COPY wp /data/app/wp
COPY git-passwd-helper.sh /data/app/
COPY requirements.txt /data/app/

WORKDIR /data/app
RUN pip install --no-cache-dir -r requirements.txt
ENV PYTHONUNBUFFERED=1

RUN git config --global user.email "ci-user@your-company.tld"
RUN git config --global user.name "CI-User"

CMD [ "python", "-m", "wp.app" ]
