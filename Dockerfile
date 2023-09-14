FROM python:3.8-slim-buster 


RUN apt update && apt install -y pandoc

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY templates/ ./templates/
COPY main.py .

RUN mkdir /data
WORKDIR /data

CMD ["python3", "/main.py"]
