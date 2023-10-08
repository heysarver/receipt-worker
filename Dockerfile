FROM python:3.7-alpine

RUN apk add --no-cache --virtual=build-dependencies build-base

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "-u", "run.py" ]
