#!/usr/bin/env bash


# Dump required env_vars
./create_env_vars.sh
docker_compose_fpath="/mnt/c/Program Files/Docker/Docker/resources/bin/docker-compose.exe"



sudo "$docker_compose_fpath" run web django-adm
in startproject composeexample .


docker run --env-file=env_vars lndmon env