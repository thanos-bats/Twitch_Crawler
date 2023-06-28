FROM python:3.10.11

WORKDIR /twitch_ctrl
COPY . .

RUN pip install -r requirements.txt

CMD ["python", "client.py"]
EXPOSE 3000