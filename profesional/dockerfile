FROM python:3.8

COPY . /usr/src/app
COPY requirements.txt /usr/src/app/requirements.txt
WORKDIR /usr/src/app

RUN pip install -r requirements.txt

CMD ["python", "app.py", "--host", "0.0.0.0"]