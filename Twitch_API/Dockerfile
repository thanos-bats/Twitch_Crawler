FROM python:3.10.11

WORKDIR /twitch
COPY . .

RUN pip install -r requirements.txt

EXPOSE 3000
CMD ["python","-u",  "main.py"]

