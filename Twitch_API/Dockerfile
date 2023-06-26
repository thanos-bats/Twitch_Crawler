FROM python:3.10.11

WORKDIR /twitch
COPY . .

RUN pip install -r requirements.txt

CMD ["python", "app.py"]
EXPOSE 3000
