# This script is used to re-generate the AMI identifiers that are hardcoded in
# the portal application
#
# Author: Nicholas Lenzi

SKIP_IMAGE_TYPE_LIST_DOWNLOAD=true
WORKSPACE_DIR=tmp/update-portal-amis

PRIME_REGION=us-east-1
REGIONS=("us-east-1" "us-east-2" "us-west-1" "us-west-2")

mkdir -p ${WORKSPACE_DIR}
if [[ "${SKIP_IMAGE_TYPE_LIST_DOWNLOAD}" != "true" ]]; then
  for REGION in "${REGIONS[@]}"; do
    echo "Downloading the image type list for ${REGION}"
    aws ec2 describe-images --region ${REGION} > ${WORKSPACE_DIR}/ec2-image-types-full-${REGION}.txt
  done
fi

IMAGE_TYPE_LOGICAL_NAMES=(\
 "Amazon Linux 2 (x86_64-gp2)" \
 "Amazon Linux 2 (Deep Learning PyTorch 1.12)" \
 "Ubuntu 22.04 (amd64-server)" \
 "Ubuntu 18.04 (Deep Learning)" \
 "Red Hat 8.6.0 (x86_64-gp2)" \
)

JQ_FILTERS_BY_IMAGE_TYPE=( \
  '.Images| sort_by(.CreationDate) | .[]  | . as $parent | .ImageLocation | select(startswith("amazon/amzn2-ami-kernel-5.10-hvm"))  | select(contains("x86_64-gp2")) | $parent'  \
  '.Images| sort_by(.CreationDate) | .[]  | . as $parent | .ImageLocation | select(startswith("amazon/Deep Learning AMI GPU PyTorch 1.12")) | select(contains("Amazon Linux 2")) | $parent'  \
  '.Images| sort_by(.CreationDate) | .[]  | . as $parent | .ImageLocation | select(startswith("amazon/ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server")) | $parent'  \
  '.Images| sort_by(.CreationDate) | .[]  | . as $parent | .ImageLocation | select(startswith("amazon/Deep Learning AMI (Ubuntu 18.04)")) | $parent'  \
  '.Images| sort_by(.CreationDate) | .[]  | . as $parent | .ImageLocation | select(startswith("amazon/RHEL-8.6")) | select(contains("GP2")) | select(contains("x86_64")) | $parent'  \
)


IDX=0
IMAGE_TYPE_NAMES=()

SRC_IMAGE_TYPES_FILE=${WORKSPACE_DIR}/ec2-image-types-full-${PRIME_REGION}.txt
for JQ_FILTER_BY_IMAGE_TYPE in "${JQ_FILTERS_BY_IMAGE_TYPE[@]}"; do
  IMAGE_TYPE_NAMES[${IDX}]=$(cat ${SRC_IMAGE_TYPES_FILE} | jq -c "${JQ_FILTER_BY_IMAGE_TYPE}" | tail -n 1 | jq '.Name')
  if [[ $? != 0 ]]; then
    echo "error: Unable to locate image name at idx=${IDX}; JQ_FILTER='${JQ_FILTER_BY_IMAGE_TYPE}'"
    exit 1
  fi

  echo "Found Image Type Name: ${IMAGE_TYPE_NAMES[${IDX}]} for ${IMAGE_TYPE_LOGICAL_NAMES[${IDX}]}"
  IDX=$((IDX + 1))
done

echo "Copy the following python snippet to ./portal/lib/ec2_config.py..."
echo ""
echo ""
echo ""

echo "image_id_dict = {"
for REGION in "${REGIONS[@]}"; do
  IDX=0
  IN_REGION_AMI=()

  for IMAGE_TYPE_NAME in "${IMAGE_TYPE_NAMES[@]}"; do
    IN_REGION_AMI[${IDX}]=$(cat ${WORKSPACE_DIR}/ec2-image-types-full-${REGION}.txt | jq ".Images | .[] | select(.Name == ${IMAGE_TYPE_NAME}) | .ImageId")
    
    IDX=$((IDX + 1))
  done

  echo "    \"${REGION}\": {"
  echo "        \"Amazon Linux\": [${IN_REGION_AMI[0]}, ${IN_REGION_AMI[1]}],"
  echo "        \"Ubuntu\": [${IN_REGION_AMI[2]}, ${IN_REGION_AMI[3]}],"
  echo "        \"Red Hat\": [${IN_REGION_AMI[4]}],"
  echo "    },"

done
echo "}"
