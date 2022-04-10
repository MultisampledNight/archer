# syntax=docker/dockerfile:1
FROM alpine:3.14

RUN apk add --update --no-cache gcc python3 python3-dev musl-dev py3-requests py3-lxml py3-pip
WORKDIR /archer
COPY . .
RUN pip3 install -r requirements.docker.txt
CMD [ "python3", "main.py" ]
