FROM python:3-alpine
# COPY qemu-arm-static /usr/bin
WORKDIR /app

COPY requirements.txt ./
COPY app/tion2mqtt.py ./

RUN apk add --no-cache glib-dev bluez-dev bluez-libs tar gcc libc-dev make bash

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "tion2mqtt.py"]