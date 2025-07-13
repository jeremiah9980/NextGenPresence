
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install flask paho-mqtt
EXPOSE 5001
CMD ["python", "mqtt_consumer.py"]
