FROM rasa/rasa:3.6.10

COPY . /app
WORKDIR /app

USER root
RUN pip install --no-cache-dir -r requirements.txt || true

CMD ["run", "--enable-api", "--cors", "*", "--debug"]
