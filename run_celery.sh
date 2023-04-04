celery -A celery_app worker -l INFO --pool=solo --concurrency=10 -n worker1@localhost
