#!/bin/bash

# This script is used to re-generate the AMI identifiers that are hardcoded in
# the portal application
#
# Author: Nicholas Lenzi

SKIP_IMAGE_TYPE_LIST_DOWNLOAD=false
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

OS_LOGICAL_NAMES=(\
"Amazon Linux" \
"Amazon Linux" \
"Ubuntu" \
"Ubuntu" \
"Red Hat" \
)

IMAGE_TYPE_LOGICAL_NAMES=(\
 "Amazon Linux 2023 (x86_64)" \
 "Amazon Linux 2023 Deep Learning OSS Nvidia Driver AMI GPU PyTorch 2.5.1" \
 "Ubuntu 24.04 (amd64-server)" \
 "Ubuntu 22.04 Deep Learning OSS Nvidia Driver AMI GPU PyTorch 2.5.1" \
 "Red Hat 9.5.0 (x86_64-gp3)" \
)

JQ_FILTERS_BY_IMAGE_TYPE=( \
  '.Images| sort_by(.CreationDate) | .[]  | . as $parent | .ImageLocation | select(startswith("amazon/al2023-ami-2023"))  | select(contains("x86_64")) | $parent'  \
  '.Images| sort_by(.CreationDate) | .[]  | . as $parent | .ImageLocation | select(startswith("amazon/Deep Learning OSS Nvidia Driver AMI GPU PyTorch 2.5.1")) | select(contains("Amazon Linux 2023")) | $parent'  \
  '.Images| sort_by(.CreationDate) | .[]  | . as $parent | .ImageLocation | select(startswith("amazon/ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server")) | $parent'  \
  '.Images| sort_by(.CreationDate) | .[]  | . as $parent | .ImageLocation | select(startswith("amazon/Deep Learning OSS Nvidia Driver AMI GPU PyTorch 2.5.1 (Ubuntu 22.04)")) | $parent'  \
  '.Images| sort_by(.CreationDate) | .[]  | . as $parent | .ImageLocation | select(startswith("amazon/RHEL-9.5")) | select(contains("GP3")) | select(contains("x86_64")) | $parent' \
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

# Update the gherkin scripts the use the AMI info
echo "Copy the following gherkin snippet to ./features/portal_ec2_launch_all_image_types.feature..."
echo ""
echo ""
echo ""

echo "    Examples:"
printf "      | %-29s | %-12s | %-82s | %-19s | %-13s | %-17s |\n" "instance_name" "img_os_tab" "ami_name" "instance_type_group" "instance_type" "volume_size_in_gb"
IDX=0
for IMAGE_TYPE_NAME in "${IMAGE_TYPE_NAMES[@]}"; do
  instance_no=$((IDX + 1))
  IMAGE_NAME_NO_QUOTE=$(echo ${IMAGE_TYPE_NAME} | sed 's#"##g')
  volume_size_in_gb=9
  if [[ "${IDX}" == "3" ]]; then
    volume_size_in_gb=20
  fi

  printf "      | helioptile-ec2-image-type-%03d | %-12s | %-82s | %-19s | %-13s | %17d |\n" ${instance_no} "${OS_LOGICAL_NAMES[${IDX}]}" "${IMAGE_NAME_NO_QUOTE}" "General Purpose" "t2.micro" ${volume_size_in_gb}

  TARGET_INPUT=$(printf "helioptile-ec2-image-type-%03d" ${instance_no})
  NEW_TEST_INPUT=$(printf "| helioptile-ec2-image-type-%03d | %-12s | %-82s | %-19s | %-13s | %17d |" ${instance_no} "${OS_LOGICAL_NAMES[${IDX}]}" "${IMAGE_NAME_NO_QUOTE}" "General Purpose" "t2.micro" ${volume_size_in_gb})
  sed "s#| ${TARGET_INPUT}.*#${NEW_TEST_INPUT}#" -i ./features/portal_ec2_launch_all_image_types.feature

  IDX=$((IDX + 1))

done
echo ""

# Update the feature test that checks all the EC2 instance types
IMAGE_NAME_NO_QUOTE=$(echo ${IMAGE_TYPE_NAMES[0]} | sed 's#"##g')
sed \
  "s#| Amazon Linux | .* |#| Amazon Linux | $(printf '%-80s' ${IMAGE_NAME_NO_QUOTE}) |                 9 |#" \
  -i ./features/portal_ec2_launch_all_instance_types.feature

# Update the normal test
sed \
  "s;And click \".*\"[[:space:]]# hint update-portal-amis.sh;And click \"${IMAGE_NAME_NO_QUOTE}\" # hint update-portal-amis.sh;" \
  -i features/portal_ec2_launch.feature


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
