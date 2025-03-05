NEW_VERSION=$1
DEST=daskhub/deploy/kube-system/base/nvidia-device-plugin.yml

if [[ "${NEW_VERSION}" == "" ]]; then
  echo "error: missing version"
  echo "usage: ${0} <version|vX.X.X>"
  exit 1
fi

HTTP_CODE=$(curl \
  --silent \
  --write-out "%{http_code}" \
  https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/${NEW_VERSION}/nvidia-device-plugin.yml \
  -o ${DEST})
if [[ ${HTTP_CODE} -lt 200 || ${HTTP_CODE} -gt 299 ]] ; then
  echo "error: server returned ${HTTP_CODE}"
  exit 1
fi

COMMIT_MSG="Update nvidia-device-plugin to ${NEW_VERSION}"

TICKET_NO=$(git branch --show-current | grep --perl-regexp 'platform-(\d+)' | sed 's#platform-##')
if [[ $? == 0 ]]; then
  if [[ "${TICKET_NO}" != "" ]]; then
    COMMIT_MSG="heliocloud/platform#${TICKET_NO}: ${COMMIT_MSG}"
  fi
fi

git commit -m "${COMMIT_MSG}"
