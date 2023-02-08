#!/bin/bash

API_KEY1=$(openssl rand -hex 32)
API_KEY2=$(openssl rand -hex 32)


cp bh-secrets.yaml.template bh-secrets.yaml

sed -i "s|<INSERT_API_KEY1>|$API_KEY1|g" bh-secrets.yaml
sed -i "s|<INSERT_API_KEY2>|$API_KEY2|g" bh-secrets.yaml

cp bh-config.yaml.template bh-config.yaml

cp bh-auth.yaml.template bh-auth.yaml
