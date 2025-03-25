#!/bin/bash
sudo docker-compose -f docker-compose.prod.yml stop
sudo docker-compose -f docker-compose.prod.yml rm
sudo docker-compose -f docker-compose.prod.yml up -d
sudo docker-compose -f docker-compose.prod.yml ps
sudo docker-compose -f docker-compose.prod.yml exec backend python manage.py makemigrations recipes
sudo docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate
sudo docker-compose -f docker-compose.prod.yml exec backend python manage.py collectstatic
sudo docker-compose -f docker-compose.prod.yml exec backend cp -r /app/collected_static/. /admin_static/
sudo docker-compose -f docker-compose.prod.yml exec -it backend python manage.py createsuperuser
sudo docker-compose -f docker-compose.prod.yml exec backend python manage.py import_ingredients
sudo docker-compose -f docker-compose.prod.yml exec backend python manage.py create_tags
