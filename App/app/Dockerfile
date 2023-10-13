FROM python:3.10
COPY . /app/
WORKDIR /app/
RUN chmod -R 777 data
RUN chmod -R 777 app/static/uml
RUN chmod -R 777 app/ConfigTraining
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
ENV DEBIAN_FRONTEND=noninteractive

RUN mkdir -p /usr/share/man/man1 /usr/share/man/man2

RUN apt-get update && \
apt-get install -y --no-install-recommends \
        openjdk-17-jre
RUN apt install -y graphviz
RUN python3 pysett.py
EXPOSE 8000
ENTRYPOINT [ "python","manage.py", "runserver", "0.0.0.0:8000"]