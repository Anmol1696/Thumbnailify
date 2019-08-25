FROM python:3.7-alpine

ENV MAGICK_HOME=/usr
RUN apk update && apk add --no-cache imagemagick && apk add --no-cache imagemagick-dev \
    && apk --update add --virtual build-dependencies libffi-dev openssl-dev python-dev py-pip build-base

RUN mkdir -p /usr/local/var/log/thumb
ADD ./worker /usr/local/thumb/worker
ADD ./config /usr/local/thumb/config

RUN pip install -r /usr/local/thumb/worker/docker/requirements.txt

WORKDIR /usr/local/thumb
ENTRYPOINT python -m worker.consume
