FROM apache/airflow:latest
USER root
RUN apt-get update \
  && apt-get install -y python3-pip
USER airflow
COPY ./requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
