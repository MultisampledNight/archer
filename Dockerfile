# syntax=docker/dockerfile:1
FROM alpine:3.14

RUN apk add --update --no-cache gcc python3 python3-dev musl-dev py3-requests py3-lxml py3-pip \
        py3-aiohttp py3-multidict py3-yarl py3-attrs py3-async-timeout
WORKDIR /archer
COPY . .
RUN pip3 install -r requirements.docker.txt
CMD [ "python3", "main.py" ]
