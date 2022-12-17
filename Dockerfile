# syntax=docker/dockerfile:1
FROM python:3-slim

COPY . /app
WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt

RUN chmod 444 app.py
RUN chmod 444 requirements.txt

ENV PORT 8080
ENV FLASK_ENV=production
# Run the web service on container startup.
CMD [ "waitress-serve", "--port", "8080", "app:app" ]