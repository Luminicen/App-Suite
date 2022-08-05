FROM python:3
COPY . /app/
WORKDIR /app/
RUN chmod -R 777 data
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8000
ENTRYPOINT [ "python","manage.py", "runserver", "0.0.0.0:8000"]