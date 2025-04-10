# Foodgram

## Описание проекта
Foodgram — сервис для хранения рецептов с возможностью формирования списка покупок.  
Пользователи могут:
- Создавать/редактировать рецепты
- Подписываться на авторов
- Формировать список покупок в PDF

▶ [Демо-версия](http://foodgram.himcorp.ru)

## Технологии
- **Backend**: Python 3.9, Django 3.2, Django REST Framework
- **База данных**: PostgreSQL
- **Аутентификация**: JWT
- **Инфраструктура**: Docker, Nginx, Gunicorn
- **CI/CD**: GitHub Actions

## Автор
👨💻 **Плякин Сергей**  
[![GitHub](https://img.shields.io/badge/-GitHub-181717?logo=github)](https://github.com/WALRUS911/foodgram)

---
## Пример .env

POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
DB_NAME=foodgram
DB_HOST=db
DB_PORT=5432

DJANGO_DEBUG=False
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=*

## Развертывание с Docker

### 1. Клонируйте репозиторий
```bash
git clone https://github.com/WALRUS911/foodgram.git
cd foodgram
```



### 2. Запуск контейнеров
```bash
docker-compose up -d --build
```

### 3. Миграции и суперпользователь
```bash
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
```
###  4. Импорт данных
```bash
docker-compose exec backend python manage.py import_ingredients
docker-compose exec backend python manage.py create_tags
```
###  5. Сборка статики
```bash
docker-compose exec backend python manage.py collectstatic --noinput
```

## Локальное развертывание (без Docker)

###  1. Установите зависимости
```bash
python -m venv venv
source venv/bin/activate  # Linux/MacOS
venv\Scripts\activate.bat  # Windows
pip install -r requirements.txt
```
###  2. Настройте базу данных
Создайте PostgreSQL БД:

```sql
Copy
CREATE DATABASE foodgram;
CREATE USER foodgram_user WITH PASSWORD 'foodgram_password';
GRANT ALL PRIVILEGES ON DATABASE foodgram TO foodgram_user;
```
###  3. Примените миграции 
```bash
python manage.py makemigrations recipes
python manage.py migrate
python manage.py collectstatic
```

###  4. Импорт данных
```bash
python manage.py import_ingredients
python manage.py create_tags
```

###  5. Запустите сервер
```bash
python manage.py runserver
```

## API-документация
Доступна после запуска проекта:
http://localhost:8000/api/docs/ (локально)
http://foodgram.himcorp.ru/api/docs/ (демо)

## CI/CD
Автоматический деплой при пуше в main
Тестирование PEP8 и Django Tests
Сборка Docker-образов
Уведомления в Telegram
