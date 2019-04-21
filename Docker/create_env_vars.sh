#!/usr/bin/env bash

echo "Dumping required env vars in env_vars"
echo "LNDMON_django_user=$LNDMON_django_user" > env_vars
echo "LNDMON_django_pass=$LNDMON_django_pass" >> env_vars
echo "LNDMON_django_config=$LNDMON_django_config" >> env_vars
echo "LNDMON_django_config=$LNDMON_django_secret_key" >> env_vars