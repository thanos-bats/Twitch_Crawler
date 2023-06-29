FROM python:3.10.11

WORKDIR /twitch_ctrl
COPY . .

RUN pip install -r requirements.txt

CMD ["python","-u", "client.py"]