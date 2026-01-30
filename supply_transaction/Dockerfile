# Dockerfile
FROM python:3.8
EXPOSE 5000
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY . /app
CMD python main.py