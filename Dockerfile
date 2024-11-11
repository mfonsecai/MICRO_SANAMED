FROM python:3.11-slim

WORKDIR /code

COPY requirements.txt  .

# Instala las dependencias necesarias para mysqlclient
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev build-essential \
    && apt-get clean

# Instala los paquetes de Python
RUN pip install --no-cache-dir -r requirements.txt




COPY . . 


CMD [ "python3","app.py","--host","0.0.0.0" ]

