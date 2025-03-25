#!/bin/bash
cd ../backend/
docker buildx build --platform=linux/amd64 -t walrus911/backend_food .

cd ../frontend/
docker buildx build --platform=linux/amd64 -t walrus911/frontend_food .

cd ../infra/
docker push walrus911/backend_food
docker push walrus911/frontend_food
