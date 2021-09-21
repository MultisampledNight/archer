# syntax=docker/dockerfile:1
FROM python:3.9.7-alpine

RUN apk add --update --no-cache g++ gcc libxslt-dev
WORKDIR /archer
COPY . .
RUN pip install -r requirements.txt
CMD [ "python", "main.py" ]
