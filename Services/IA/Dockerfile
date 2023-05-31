FROM python:3.9
COPY . /app/
WORKDIR /app/
RUN chmod -R 777 configuracionInicialIA
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
ENV DEBIAN_FRONTEND=noninteractive
RUN mkdir -p /usr/share/man/man1 /usr/share/man/man2
RUN pip install --upgrade pip
EXPOSE 6000
ENTRYPOINT [ "python","manage.py", "runserver", "0.0.0.0:6000"]