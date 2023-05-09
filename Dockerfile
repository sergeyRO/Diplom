FROM python:3.9.6-alpine
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
RUN pip install --upgrade pip
RUN mkdir -p /app
RUN mkdir -p /app/tests
RUN mkdir -p /app/staticfiles
RUN mkdir -p /app/diplom/netology_pd_diplom
RUN mkdir -p /app/diplom/backend
ADD ./* /app
ADD ./diplom/netology_pd_diplom /app/diplom/netology_pd_diplom
ADD ./diplom/backend /app/diplom/backend
ADD ./tests /app/tests
RUN ls -lrt /app
RUN pip install -r requirements.txt
RUN python3 ./manage.py makemigrations backend
EXPOSE 8000


