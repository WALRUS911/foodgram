#!/bin/bash

docker-compose stop
docker rm foodgram-backend
docker rm foodgram-db
docker image rm infra-backend   
docker image rm postgres:13
docker volume rm infra_pg_data
