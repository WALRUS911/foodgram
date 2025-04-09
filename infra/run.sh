#!/bin/bash
docker-compose -f docker-compose.yml stop
docker-compose -f docker-compose.yml rm
docker-compose -f docker-compose.yml up -d
docker-compose -f docker-compose.yml ps
docker-compose -f docker-compose.yml exec backend python manage.py makemigrations recipes
docker-compose -f docker-compose.yml exec backend python manage.py migrate
docker-compose -f docker-compose.yml exec backend python manage.py collectstatic
docker-compose -f docker-compose.yml exec backend cp -r /app/collected_static/. /static/
docker-compose -f docker-compose.yml exec backend cp -r /app/collected_static/. /admin_static/
docker-compose -f docker-compose.yml exec -it backend python manage.py createsuperuser
docker-compose -f docker-compose.yml exec backend python manage.py import_ingredients
docker-compose -f docker-compose.yml exec backend python manage.py create_tags
