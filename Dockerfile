FROM python:3.10

ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE murojat_website.settings

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt
# CMD ["gunicorn", "murojat_website.wsgi:application", "--bind", "0.0.0.0:8000"]
# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

