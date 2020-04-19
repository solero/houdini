FROM python:3-alpine

RUN apk add build-base openssl-dev libffi-dev

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV server "login"

CMD ["sh", "-c", "python ./bootstrap.py ${server}"]