FROM python:3.11.1

RUN apt update && apt install -y python3 python3-pip

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN python -m pip install --upgrade pip

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

RUN apt update && apt install -y python3 python3-pip