FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install flask schedule ring_doorbell

EXPOSE 5000

CMD ["python", "flask_ui.py"]
