#!/bin/bash

WEBHOOK_URL=$1
export TEMPLATE_FILE=$2

export TEMPLATE_IN_DIR=.slack
TEMPLATE_SUBST_OUT_DIR=temp/slack

mkdir ${TEMPLATE_SUBST_OUT_DIR} -p
export COMMON_FOOTER=$(envsubst < ${TEMPLATE_IN_DIR}/common-footer-template.txt)
envsubst < ${TEMPLATE_IN_DIR}/${TEMPLATE_FILE} > ${TEMPLATE_SUBST_OUT_DIR}/msg.json || (echo "error: failed to generate message" && exit 1)

cat ${TEMPLATE_SUBST_OUT_DIR}/msg.json
curl \
    -X POST \
    -H 'Content-type: application/json' \
    --data "@${TEMPLATE_SUBST_OUT_DIR}/msg.json" \
    ${WEBHOOK_URL}
