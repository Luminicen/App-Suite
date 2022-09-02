FROM python:3.9
COPY . /app/
WORKDIR /app/
RUN chmod -R 777 data
RUN chmod -R 777 app/static/uml
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
ENV DEBIAN_FRONTEND=noninteractive

RUN mkdir -p /usr/share/man/man1 /usr/share/man/man2

RUN apt-get update && \
apt-get install -y --no-install-recommends \
        openjdk-11-jre
RUN apt install -y graphviz
EXPOSE 8000
ENTRYPOINT [ "python","manage.py", "runserver", "0.0.0.0:8000"]