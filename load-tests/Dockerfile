FROM locustio/locust:latest

WORKDIR /locust

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY locustfile.py .

EXPOSE 8089
