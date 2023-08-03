FROM python:3.9
LABEL authors="jross"

WORKDIR .

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . .

# install curl. used for healthcheck
RUN apt install curl


# nothing to run. command to launch server is in docker-compose
