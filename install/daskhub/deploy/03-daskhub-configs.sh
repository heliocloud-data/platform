#!/bin/bash

API_KEY1=$(openssl rand -hex 32)
API_KEY2=$(openssl rand -hex 32)

cp dh-secrets.yaml.template dh-secrets.yaml

sed -i "s|<INSERT_API_KEY1>|$API_KEY1|g" dh-secrets.yaml
sed -i "s|<INSERT_API_KEY2>|$API_KEY2|g" dh-secrets.yaml

cp dh-config.yaml.template dh-config.yaml
cp dh-auth.yaml.template dh-auth.yaml
